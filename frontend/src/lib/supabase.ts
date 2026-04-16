import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";
const hasSupabaseEnv = Boolean(supabaseUrl && supabaseAnonKey);

<<<<<<< Updated upstream
const fallbackUrl = "http://127.0.0.1:54321";
const fallbackAnon = "public-anon-key-placeholder";

if (!hasSupabaseEnv) {
  // Falha explicita em runtime para evitar comportamento silencioso.
=======
if (!hasSupabaseEnv) {
>>>>>>> Stashed changes
  // eslint-disable-next-line no-console
  console.warn(
    "Supabase env ausente. Configure NEXT_PUBLIC_SUPABASE_URL e NEXT_PUBLIC_SUPABASE_ANON_KEY."
  );
}

<<<<<<< Updated upstream
export const supabase = createClient(
  hasSupabaseEnv ? supabaseUrl : fallbackUrl,
  hasSupabaseEnv ? supabaseAnonKey : fallbackAnon
);
=======
const fallbackUrl = "https://placeholder.supabase.co";
const fallbackAnonKey = "placeholder-anon-key";

export const SUPABASE_CONFIGURED = hasSupabaseEnv;

export const supabase = createClient(
  hasSupabaseEnv ? supabaseUrl : fallbackUrl,
  hasSupabaseEnv ? supabaseAnonKey : fallbackAnonKey,
  {
    auth: {
      persistSession: false,
      autoRefreshToken: false,
      detectSessionInUrl: false,
    },
  }
);

>>>>>>> Stashed changes
