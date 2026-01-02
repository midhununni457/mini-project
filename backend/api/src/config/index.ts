import dotenv from "dotenv";
import { config } from "@/types";

dotenv.config();

const PORT = Number(process.env.PORT) || 3000;

const SUPABASE_URL = process.env.SUPABASE_URL;

if (!SUPABASE_URL) {
  throw new Error("SUPABASE_URL is not defined in environment variables");
}

const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY;

if (!SUPABASE_SERVICE_KEY) {
  throw new Error(
    "SUPABASE_SERVICE_KEY is not defined in environment variables"
  );
}

const SUPABASE_BUCKET_NAME = process.env.SUPABASE_BUCKET_NAME;

if (!SUPABASE_BUCKET_NAME) {
  throw new Error("SUPABASE_BUCKET_NAME is not defined in environment variables");
}

const appConfig: config = {
  PORT,
  SUPABASE_URL,
  SUPABASE_SERVICE_KEY,
  SUPABASE_BUCKET_NAME,
};

export default appConfig;
