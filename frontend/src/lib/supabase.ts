import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";
const hasSupabaseEnv = Boolean(supabaseUrl && supabaseAnonKey);

const fallbackUrl = "http://127.0.0.1:54321";
const fallbackAnon = "public-anon-key-placeholder";

if (!hasSupabaseEnv) {
  // Falha explicita em runtime para evitar comportamento silencioso.
  // eslint-disable-next-line no-console
  console.warn("Supabase env ausente. Configure NEXT_PUBLIC_SUPABASE_URL e NEXT_PUBLIC_SUPABASE_ANON_KEY.");
}

export const supabase = createClient(
  hasSupabaseEnv ? supabaseUrl : fallbackUrl,
  hasSupabaseEnv ? supabaseAnonKey : fallbackAnon
);
