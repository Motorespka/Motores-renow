import { Session } from "@supabase/supabase-js";
import { AppRouterInstance } from "next/dist/shared/lib/app-router-context.shared-runtime";

import { supabase } from "./supabase";

export async function getCurrentSession(): Promise<Session | null> {
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

