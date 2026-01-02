import { Router } from "express";
import { uploadAPK } from "@/handlers/upload";
import multer from "multer";

const router = Router();

const upload = multer({
  storage: multer.memoryStorage(),
  limits: {
    fileSize: 50 * 1024 * 1024,
  },
});

router.post("/upload", upload.single("apk"), uploadAPK);

export default router;
