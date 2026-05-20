"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { requireSession } from "@/lib/auth";
import { apiFetch } from "@/lib/api";
import { MeResponse } from "@/lib/types";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [ok, setOk] = useState(false);

  useEffect(() => {
    (async () => {
      const session = await requireSession(router);
      if (!session) return;
      try {
        const me = await apiFetch<MeResponse>("/auth/me", session.access_token);
        if (!me.profile.is_admin) {
          router.replace("/dashboard");
          return;
        }
        setOk(true);
      } catch {
        router.replace("/login");
      }
    })();
  }, [router]);

  if (!ok) {
    return <div className="center-screen">Carregando admin...</div>;
  }

  return <>{children}</>;
}
