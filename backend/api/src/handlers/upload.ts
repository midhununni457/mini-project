import { Request, Response } from "express";
import { supabase } from "@/lib/supabase";
import appConfig from "@/config";

const BUCKET_NAME = appConfig.SUPABASE_BUCKET_NAME;

export async function uploadAPK(
  req: Request,
  res: Response
) {
  try {
    const file = req.file;
    if (!file) {
      return res.status(400).json({ message: "No file uploaded" });
    }

    const destFileName = `${Date.now()}_${file.originalname}`;

    const { data, error } = await supabase.storage
      .from(BUCKET_NAME)
      .upload(destFileName, file.buffer, {
        contentType: file.mimetype,
        cacheControl: "3600",
        upsert: false,
      });

    if (error) {
      throw new Error(error.message);
    }

    return res.status(200).json({
      message: "File uploaded successfully",
    });
  } catch (err: any) {
    console.error("Upload Error:", err);
    return res.status(500).json({
      message: "Internal Server Error",
      error: err.message,
    });
  }
}
