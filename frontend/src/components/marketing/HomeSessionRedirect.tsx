"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { getCurrentSession } from "@/lib/auth";

/** Se já houver sessão, manda para o painel — não bloqueia a landing. */
export function HomeSessionRedirect() {
  const router = useRouter();

  useEffect(() => {
    let cancelled = false;
    const t = window.setTimeout(() => {
      // se getSession travar, não deixamos a home presa
    }, 2500);

    (async () => {
      try {
        const session = await Promise.race([
          getCurrentSession(),
          new Promise<null>((resolve) => window.setTimeout(() => resolve(null), 2000)),
        ]);
        if (!cancelled && session) {
          router.replace("/dashboard");
        }
      } catch {
        // mantém a landing pública
      }
    })();

    return () => {
      cancelled = true;
      window.clearTimeout(t);
    };
  }, [router]);

  return null;
}
