import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";
const hasSupabaseEnv = Boolean(supabaseUrl && supabaseAnonKey);

if (!hasSupabaseEnv) {
  // eslint-disable-next-line no-console
  console.warn(
    "Supabase env ausente. Configure NEXT_PUBLIC_SUPABASE_URL e NEXT_PUBLIC_SUPABASE_ANON_KEY."
  );
}

const fallbackUrl = "https://placeholder.supabase.co";
const fallbackAnonKey = "placeholder-anon-key";

export const SUPABASE_CONFIGURED = hasSupabaseEnv;

// Com credenciais reais, a sessão precisa persistir (localStorage) ou o login
// "funciona" mas some no próximo getSession() — típico em produção (Vercel).
const authOptions = hasSupabaseEnv
  ? {
      persistSession: true,
      autoRefreshToken: true,
      detectSessionInUrl: true,
    }
  : {
      persistSession: false,
      autoRefreshToken: false,
      detectSessionInUrl: false,
    };

export const supabase = createClient(
  hasSupabaseEnv ? supabaseUrl : fallbackUrl,
  hasSupabaseEnv ? supabaseAnonKey : fallbackAnonKey,
  {
    auth: authOptions,
  }
);
