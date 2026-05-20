import { createClient } from "@supabase/supabase-js";

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";

/** `.env.example` / cópias incompletas: URL ou chave ainda por substituir — tratar como Supabase inactivo. */
function isUsableSupabaseCredentials(url: string, anonKey: string): boolean {
  const u = url.trim();
  const k = anonKey.trim();
  if (!u || !k) return false;
  if (/YOUR_PROJECT/i.test(u) || /YOUR_SUPABASE_ANON_KEY/i.test(k)) return false;
  if (u.toLowerCase().includes("placeholder.supabase.co")) return false;
  if (k === "placeholder-anon-key") return false;
  return true;
}

const hasSupabaseEnv = isUsableSupabaseCredentials(supabaseUrl, supabaseAnonKey);

if (!hasSupabaseEnv) {
  // eslint-disable-next-line no-console
  console.warn(
    "Supabase inactivo (env em falta ou ainda com placeholders YOUR_*). O login de teste admin/admin usa a API mock em dev."
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
