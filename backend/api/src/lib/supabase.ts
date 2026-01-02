import { createClient } from "@supabase/supabase-js";
import appConfig from "@/config";

export const supabase = createClient(
  appConfig.SUPABASE_URL,
  appConfig.SUPABASE_SERVICE_KEY,
  {
    auth: {
      persistSession: false,
      autoRefreshToken: false,
    },
  }
);
