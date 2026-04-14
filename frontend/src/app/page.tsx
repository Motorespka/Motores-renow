"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

import { getCurrentSession } from "@/lib/auth";

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    (async () => {
      const session = await getCurrentSession();
      if (session) {
        router.replace("/dashboard");
      } else {
        router.replace("/login");
      }
    })();
  }, [router]);

  return <div className="center-screen text-muted">Carregando...</div>;
}

