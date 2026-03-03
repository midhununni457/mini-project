import subprocess
import sys
import os
import shutil
import zipfile
import re
import csv
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed

# ==============================
# CONFIG
# ==============================

CONTAINER     = "android-emulator"
DEVICE        = "emulator-5554"

DEX2OAT       = "/apex/com.android.art/bin/dex2oat64"
OATDUMP       = "/apex/com.android.art/bin/oatdump"
BOOT_IMAGE    = "/apex/com.android.art/javalib/boot.art"

EMULATOR_TMP  = "/data/local/tmp"
CONTAINER_TMP = "/tmp"
LOCAL_WORK    = "apk_extract"

PARALLEL_WORKERS = 4
TRIM_HEAD        = 4
TRIM_TAIL        = 2

# ==============================
# UTILS
# ==============================

def run(cmd):
    subprocess.run(cmd, check=True)

def docker_exec(cmd):
    run(["docker", "exec", "-u", "0", CONTAINER] + cmd)

def docker_cp_to_container(local, remote):
    run(["docker", "cp", local, f"{CONTAINER}:{remote}"])

def docker_cp_from_container(remote, local):
    run(["docker", "cp", f"{CONTAINER}:{remote}", local])

# ==============================
# REGEX (UNCHANGED)
# ==============================

NATIVE_LINE_RE = re.compile(
    r'^\s{4,}0x[0-9a-fA-F]+:\s+'
    r'(?:[0-9a-fA-F]{2}\s*)+'
    r'\s+([a-zA-Z][a-zA-Z0-9_./]*)'
)

NOISE_SECTION_RE = re.compile(
    r'DEX\s+CODE:'
    r'|QuickeningInfo'
    r'|StackMaps?'
    r'|RegisterInfo'
    r'|CoreSpillMask|FpSpillMask'
    r'|CodeSize|OatMethodOffsets'
    r'|GcMap|InlineInfo'
    r'|dex_method_idx|shorty\s*:'
    r'|begin_offset|end_offset'
    r'|CodeInfo|MappingTable'
    r'|VERIFIED|NOT_COMPILED'
    r'|\(no\s+code\)'
    r'|^\s*$',
    re.IGNORECASE
)

METHOD_START_RE = re.compile(
    r'^\s+\d+:\s+\S.*\(dex_method_idx=\d+\)'
)

NATIVE_ADDR_RE = re.compile(
    r'^\s{4,}0x[0-9a-fA-F]+:\s+[0-9a-fA-F]{2}\s'
)

ASM_DIRECTIVE_RE = re.compile(r'^\.')
X86_SIZE_RE      = re.compile(r'[bwlq]$')
ARM_CC_RE        = re.compile(r'(eq|ne|cs|cc|mi|pl|vs|vc|hi|ls|ge|lt|gt|le|al)$')
LETTERS_ONLY_RE  = re.compile(r'^[a-z]+$')

# ==============================
# NORMALIZATION (UNCHANGED)
# ==============================

def normalize_opcode(op: str):
    op = op.lower().strip()

    if not op or ASM_DIRECTIVE_RE.match(op):
        return None

    if 'unknown' in op:
        return None

    if '-' in op or "'" in op:
        return None

    if '.' in op:
        op = op.split('.')[0]
        if not op:
            return None

    if len(op) > 2:
        stripped = X86_SIZE_RE.sub('', op)
        if stripped:
            op = stripped

    if op.startswith('j') and len(op) > 1:
        return 'jcc'

    if op.startswith('call'):
        return 'call'

    if len(op) > 3:
        stripped = ARM_CC_RE.sub('', op)
        if len(stripped) >= 2:
            op = stripped

    if not LETTERS_ONLY_RE.match(op):
        return None

    return op if op else None

# ==============================
# EXTRACTION (UNCHANGED LOGIC)
# ==============================

def extract_native_opcodes(asm_path: str) -> list:
    all_opcodes    = []
    current_method = []
    in_native      = False

    def flush_method():
        ops = current_method[:]
        if len(ops) > TRIM_HEAD + TRIM_TAIL:
            ops = ops[TRIM_HEAD : len(ops) - TRIM_TAIL]
        all_opcodes.extend(ops)
        current_method.clear()

    with open(asm_path, 'r', errors='ignore') as f:
        for line in f:

            if METHOD_START_RE.match(line):
                flush_method()
                in_native = True
                continue

            if NOISE_SECTION_RE.search(line):
                in_native = False
                continue

            if NATIVE_ADDR_RE.match(line):
                in_native = True

            if not in_native:
                continue

            m = NATIVE_LINE_RE.match(line)
            if m:
                op = normalize_opcode(m.group(1))
                if op is not None:
                    current_method.append(op)

    flush_method()
    return all_opcodes

# ==============================
# OPTIMIZED PER-DEX WORKER
# ==============================

def process_dex(dex_file: str, apk_name: str):
    class_id = dex_file.replace('.dex', '')

    local_dex     = os.path.join(LOCAL_WORK, dex_file)
    container_dex = f"{CONTAINER_TMP}/{dex_file}"
    emulator_dex  = f"{EMULATOR_TMP}/{dex_file}"
    emulator_oat  = f"{EMULATOR_TMP}/{apk_name}_{class_id}.oat"
    emulator_asm  = f"{EMULATOR_TMP}/{apk_name}_{class_id}.asm"
    container_asm = f"{CONTAINER_TMP}/{apk_name}_{class_id}.asm"
    local_asm     = os.path.join(LOCAL_WORK, f"{apk_name}_{class_id}.asm")

    docker_cp_to_container(local_dex, container_dex)

    docker_exec(["sh", "-c",
        f"adb -s {DEVICE} push {container_dex} {emulator_dex}"
    ])

    docker_exec(["sh", "-c",
        f"adb -s {DEVICE} shell "
        f"{DEX2OAT} "
        f"--dex-file={emulator_dex} "
        f"--oat-file={emulator_oat} "
        f"--instruction-set=x86_64 "
        f"--boot-image={BOOT_IMAGE} "
        f"--compiler-filter=speed"
    ])

    docker_exec(["sh", "-c",
        f"adb -s {DEVICE} shell "
        f"{OATDUMP} "
        f"--oat-file={emulator_oat} "
        f"--boot-image={BOOT_IMAGE} "
        f"--instruction-set=x86_64 "
        f"--no-dump:vmap "
        f"--output={emulator_asm}"
    ])

    docker_exec(["sh", "-c",
        f"adb -s {DEVICE} pull {emulator_asm} {container_asm}"
    ])

    docker_cp_from_container(container_asm, local_asm)

    return dex_file

# ==============================
# MAIN
# ==============================

if len(sys.argv) != 2:
    print("Usage: python3 native_3gram_pipeline.py <apkname.apk>")
    sys.exit(1)

apk_path = sys.argv[1]
apk_name = os.path.splitext(os.path.basename(apk_path))[0]

if os.path.exists(LOCAL_WORK):
    shutil.rmtree(LOCAL_WORK)
os.makedirs(LOCAL_WORK, exist_ok=True)

with zipfile.ZipFile(apk_path, 'r') as z:
    dex_files = [f for f in z.namelist() if re.match(r'classes\d*\.dex$', f)]
    z.extractall(LOCAL_WORK, dex_files)

dex_files = [os.path.basename(f) for f in dex_files]

if not dex_files:
    print("No dex files found.")
    shutil.rmtree(LOCAL_WORK)
    sys.exit(1)

print(f"Found {len(dex_files)} dex file(s): {dex_files}")

# ---------- Single optimized emulator phase ----------

print("\n  [process] push + compile + dump + pull")

with ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as pool:
    futures = {pool.submit(process_dex, d, apk_name): d for d in dex_files}
    for fut in as_completed(futures):
        dex = futures[fut]
        try:
            fut.result()
            print(f"    ✓  {dex}")
        except Exception as exc:
            print(f"    ✗  {dex} FAILED — {exc}")
            raise

# ---------- Parse phase (true CPU parallelism) ----------

print("\n  [parse] local CPU phase")

def parse_worker(d):
    class_id = d.replace('.dex', '')
    asm_path = os.path.join(LOCAL_WORK, f"{apk_name}_{class_id}.asm")
    return (d, extract_native_opcodes(asm_path))

with ProcessPoolExecutor(max_workers=os.cpu_count()) as pool:
    results_list = list(pool.map(parse_worker, dex_files))

results = dict(results_list)

all_opcodes = []
for dex_file in dex_files:
    ops = results[dex_file]
    print(f"    {dex_file} → {len(ops)} opcodes")
    all_opcodes.extend(ops)

# ---------- Cleanup ----------

print("\n  [cleanup] removing remote files ...")

cleanup_targets = []
for dex_file in dex_files:
    class_id = dex_file.replace('.dex', '')
    cleanup_targets += [
        f"{EMULATOR_TMP}/{dex_file}",
        f"{EMULATOR_TMP}/{apk_name}_{class_id}.oat",
        f"{EMULATOR_TMP}/{apk_name}_{class_id}.asm",
    ]

docker_exec(["adb", "-s", DEVICE, "shell", "rm", "-f"] + cleanup_targets)
docker_exec(["sh", "-c", f"rm -f {CONTAINER_TMP}/*.dex {CONTAINER_TMP}/*.asm"])

# ---------- 3-gram ----------

print(f"\nTotal native opcodes : {len(all_opcodes)}")

counter = Counter(
    (all_opcodes[i], all_opcodes[i+1], all_opcodes[i+2])
    for i in range(len(all_opcodes) - 2)
)

sorted_ngrams = sorted(counter.items(), key=lambda x: x[1], reverse=True)

print(f"Unique 3-grams       : {len(sorted_ngrams)}")
print(f"Top 5 3-grams        : {sorted_ngrams[:5]}")

output_file = f"{apk_name}_3gram.csv"

with open(output_file, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["opcode1", "opcode2", "opcode3", "frequency"])
    for gram, freq in sorted_ngrams:
        writer.writerow([gram[0], gram[1], gram[2], freq])

shutil.rmtree(LOCAL_WORK)

print(f"\nDone. Output saved to: {output_file}")
