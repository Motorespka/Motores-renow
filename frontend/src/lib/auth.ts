import { Session } from "@supabase/supabase-js";
import { AppRouterInstance } from "next/dist/shared/lib/app-router-context.shared-runtime";

import { supabase } from "./supabase";
import { SUPABASE_CONFIGURED } from "./supabase";

const DEV_SESSION = {
  access_token: "dev",
  user: { email: "dev@localhost" },
} as unknown as Session;

export async function getCurrentSession(): Promise<Session | null> {
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
  if (!SUPABASE_CONFIGURED) {
    return DEV_SESSION;
  }
  const session = await getCurrentSession();
  if (!session) {
    router.replace("/login");
    return null;
  }
  return session;
}

