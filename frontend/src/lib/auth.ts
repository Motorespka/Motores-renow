import { Session } from "@supabase/supabase-js";
import { AppRouterInstance } from "next/dist/shared/lib/app-router-context.shared-runtime";

import { supabase } from "./supabase";
import { SUPABASE_CONFIGURED } from "./supabase";

const DEV_DEMO_STORAGE_KEY = "mrw_dev_demo_login_v1";

const DEV_SESSION = {
  access_token: "dev",
  user: { email: "dev@localhost" },
} as unknown as Session;

/** `next dev` (NODE_ENV=development) ou NEXT_PUBLIC_DEV_DEMO_LOGIN=true — nunca em produção sem o env explícito. */
export function isDevDemoLoginAllowed(): boolean {
  const flag = (process.env.NEXT_PUBLIC_DEV_DEMO_LOGIN || "").trim().toLowerCase();
  if (flag === "false") return false;
  if (flag === "true") return true;
  return process.env.NODE_ENV === "development";
}

function hasDevDemoSessionFlag(): boolean {
  if (typeof window === "undefined") return false;
  try {
    return window.localStorage.getItem(DEV_DEMO_STORAGE_KEY) === "1";
  } catch {
    return false;
  }
}

/** Credenciais de teste: parte antes do @ deve ser `admin` e palavra-passe `admin` (ex.: admin@localhost). */
export function tryDevDemoCredentials(email: string, password: string): boolean {
  if (!isDevDemoLoginAllowed()) return false;
  if (password !== "admin") return false;
  const trimmed = email.trim().toLowerCase();
  if (!trimmed) return false;
  const local = trimmed.includes("@") ? trimmed.split("@")[0] : trimmed;
  return local === "admin";
}

/** Grava a flag de sessão demo; devolve `false` se `localStorage` falhar (modo privado, política do browser). */
export function setDevDemoSession(): boolean {
  if (typeof window === "undefined") return false;
  try {
    window.localStorage.setItem(DEV_DEMO_STORAGE_KEY, "1");
    return window.localStorage.getItem(DEV_DEMO_STORAGE_KEY) === "1";
  } catch {
    return false;
  }
}

export function clearDevDemoSession(): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.removeItem(DEV_DEMO_STORAGE_KEY);
  } catch {
    // no-op
  }
}

export async function getCurrentSession(): Promise<Session | null> {
  if (hasDevDemoSessionFlag() && isDevDemoLoginAllowed()) {
    return DEV_SESSION;
  }
  if (!SUPABASE_CONFIGURED) {
    return DEV_SESSION;
  }
  const { data, error } = await supabase.auth.getSession();
  if (error) {
    return null;
  }
  return data.session ?? null;
}

export async function requireSession(router: AppRouterInstance): Promise<Session | null> {
  const session = await getCurrentSession();
  if (!session) {
    router.replace("/login");
    return null;
  }
  return session;
}

