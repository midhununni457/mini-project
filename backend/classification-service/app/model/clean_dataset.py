import pandas as pd

TRAIN_FILE = "training_dataset.csv"
TEST_FILE = "test_dataset.csv"

CLEAN_TRAIN_FILE = "training_dataset_clean.csv"
CLEAN_TEST_FILE = "test_dataset_clean.csv"


# ---------------------------------------------------
# Load datasets
# ---------------------------------------------------

train_df = pd.read_csv(TRAIN_FILE)
test_df = pd.read_csv(TEST_FILE)


# ---------------------------------------------------
# Remove rows with NaN values
# ---------------------------------------------------

train_df = train_df.dropna()
test_df = test_df.dropna()


# ---------------------------------------------------
# Remove rows where all trigram features are zero
# ---------------------------------------------------

feature_cols = [col for col in train_df.columns if col not in ["sha256", "label"]]

train_df = train_df[(train_df[feature_cols] != 0).any(axis=1)]
test_df = test_df[(test_df[feature_cols] != 0).any(axis=1)]


print("Training samples after cleaning:", len(train_df))
print("Test samples after cleaning:", len(test_df))


# ---------------------------------------------------
# Save cleaned datasets
# ---------------------------------------------------

train_df.to_csv(CLEAN_TRAIN_FILE, index=False)
test_df.to_csv(CLEAN_TEST_FILE, index=False)

print("Cleaned datasets saved.")