"use client";

import { ReactNode, useMemo, useState } from "react";
import { usePathname, useRouter } from "next/navigation";

import { supabase } from "@/lib/supabase";
import { SUPABASE_CONFIGURED } from "@/lib/supabase";
import { CyberHeader } from "@/components/cyber/CyberHeader";
import { CyberSidebar } from "@/components/cyber/CyberSidebar";

type Props = {
  title: string;
  subtitle?: string;
  children: ReactNode;
  isAdmin?: boolean;
  userLabel?: string;
  canAccessCadastro?: boolean;
};

export function AppShell({
  title,
  subtitle,
  children,
  isAdmin = false,
  userLabel = "",
  canAccessCadastro = false
}: Props) {
  const pathname = usePathname();
  const router = useRouter();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  async function handleLogout() {
    if (SUPABASE_CONFIGURED) {
      await supabase.auth.signOut();
    }
    router.replace("/login");
  }

  const activeSection = useMemo(() => {
    if (pathname.startsWith("/motors")) return "motors";
    if (pathname.startsWith("/cadastro")) return "cadastro";
    if (pathname.startsWith("/admin")) return "admin";
    if (pathname.startsWith("/diagnostico")) return "diagnostic";
    if (pathname.startsWith("/conferencia")) return "conference";
    if (pathname.startsWith("/settings")) return "settings";
    if (pathname.startsWith("/dashboard")) return "dashboard";
    return "dashboard";
  }, [pathname]);

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <div className="fixed inset-0 grid-bg pointer-events-none" />
      <CyberSidebar
        collapsed={sidebarCollapsed}
        onToggleCollapsed={() => setSidebarCollapsed((v) => !v)}
        canAccessCadastro={!!canAccessCadastro}
        isAdmin={!!isAdmin}
      />
      <div className="flex-1 flex flex-col overflow-hidden relative">
        <CyberHeader activeSection={activeSection} userName={userLabel || "Técnico"} />
        <main className="flex-1 overflow-auto p-6">
          <div className="max-w-[1800px] mx-auto">
            {/* Keep existing title/subtitle as accessible fallback */}
            <div className="sr-only">
              <h2>{title}</h2>
              {subtitle ? <p>{subtitle}</p> : null}
            </div>
            {children}
            <div className="mt-8 flex justify-end">
              <button
                onClick={handleLogout}
                className="text-xs px-3 py-2 rounded-lg border border-border/40 bg-muted/30 hover:bg-muted/50 text-muted-foreground hover:text-foreground transition-colors"
              >
                Sair
              </button>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
