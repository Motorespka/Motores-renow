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

  return (
    <div className="min-h-screen flex items-center justify-center px-6 relative overflow-hidden">
      <div className="absolute inset-0 grid-bg pointer-events-none" />
      <div className="w-full max-w-md premium-card-elevated p-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-primary via-primary/90 to-primary/70 flex items-center justify-center shadow-lg">
            <span className="font-display text-[12px] tracking-widest font-bold text-primary-foreground">MR</span>
          </div>
          <div className="flex flex-col">
            <span className="font-display text-sm font-bold tracking-wider text-foreground">MOTO-RENOW</span>
            <span className="text-[10px] text-primary/70 tracking-[0.22em] font-medium">TECHNICAL PLATFORM</span>
          </div>
        </div>
        <div className="mt-4 text-[12px] text-muted-foreground font-tech">Carregando…</div>
      </div>
    </div>
  );
}

