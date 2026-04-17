"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  ClipboardList,
  Database,
  FileSearch,
  Gauge,
  LayoutDashboard,
  ScanLine,
  Settings,
  Shield,
  Wrench,
} from "lucide-react";

type NavItem = {
  href: string;
  label: string;
  icon: React.ElementType;
  badge?: string;
  badgeType?: "accent" | "primary" | "warning";
  visible?: boolean;
};

export function CyberSidebar({
  collapsed,
  onToggleCollapsed,
  canAccessCadastro,
  isAdmin,
}: {
  collapsed: boolean;
  onToggleCollapsed: () => void;
  canAccessCadastro: boolean;
  isAdmin: boolean;
}) {
  const pathname = usePathname();

  const groups: { label: string; items: NavItem[] }[] = [
    {
      label: "OPERAÇÃO",
      items: [
        { href: "/dashboard", label: "Visão Geral", icon: LayoutDashboard, visible: true },
        { href: "/motors", label: "Consulta Técnica", icon: Database, visible: true },
        { href: "/cadastro", label: "Cadastro / OCR", icon: ScanLine, badge: "OCR", badgeType: "primary", visible: canAccessCadastro },
      ],
    },
    {
      label: "ANÁLISE TÉCNICA",
      items: [
        { href: "/diagnostico", label: "Diagnóstico", icon: FileSearch, visible: true },
        { href: "/conferencia", label: "Conferência Técnica", icon: ClipboardList, visible: true },
      ],
    },
    {
      label: "SISTEMA",
      items: [
        { href: "/admin", label: "Administração", icon: Shield, visible: isAdmin },
        { href: "/settings", label: "Configurações", icon: Settings, visible: true },
      ],
    },
  ];

  return (
    <aside
      className={cn(
        "relative flex flex-col h-screen border-r border-sidebar-border transition-all duration-300 ease-out",
        collapsed ? "w-[72px]" : "w-[260px]",
      )}
      style={{ background: "hsl(var(--sidebar-background))" }}
    >
      <div className="absolute top-0 left-0 right-0 h-40 bg-gradient-to-b from-primary/[0.03] to-transparent pointer-events-none" />

      <div
        className={cn(
          "relative flex items-center gap-3 p-4 border-b border-sidebar-border/50",
          collapsed ? "justify-center" : "px-5",
        )}
      >
        <button
          type="button"
          className="relative flex-shrink-0 group"
          onClick={onToggleCollapsed}
          aria-label="Toggle sidebar"
        >
          <div className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-primary via-primary/90 to-primary/70 flex items-center justify-center shadow-lg transition-all duration-300 group-hover:shadow-[0_0_30px_rgba(var(--glow-primary-rgb),0.3)]">
            <Gauge className="w-5 h-5 text-primary-foreground" />
            <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-white/20 to-transparent" />
          </div>
          <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-accent border-2 border-background">
            <div className="absolute inset-0 rounded-full bg-accent animate-ping opacity-50" />
          </div>
        </button>

        {!collapsed && (
          <div className="flex flex-col">
            <span className="font-display text-[15px] font-bold tracking-wider text-foreground">MOTO-RENOW</span>
            <span className="text-[10px] text-primary/70 tracking-[0.2em] font-medium">TECHNICAL PLATFORM</span>
          </div>
        )}
      </div>

      {!collapsed && (
        <div className="px-5 py-3 border-b border-sidebar-border/30">
          <div className="flex items-center justify-between text-[10px] mb-2">
            <span className="text-muted-foreground/70 uppercase tracking-wider font-medium">Workspace</span>
            <span className="text-accent font-semibold flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
              Online
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-md bg-primary/10 border border-primary/20 flex items-center justify-center">
              <span className="text-[10px] font-bold text-primary">MR</span>
            </div>
            <div className="flex flex-col">
              <span className="text-[11px] font-semibold text-foreground leading-tight">Oficina Central</span>
              <span className="text-[9px] text-muted-foreground font-mono">id: ws-mr-001</span>
            </div>
          </div>
        </div>
      )}

      <nav className="flex-1 overflow-y-auto py-4 px-2.5 space-y-5">
        {groups.map((g) => (
          <div key={g.label}>
            {!collapsed && (
              <div className="px-3 mb-2">
                <span className="text-[10px] font-semibold tracking-[0.15em] text-muted-foreground/50">{g.label}</span>
              </div>
            )}
            <div className="space-y-0.5">
              {g.items
                .filter((i) => i.visible !== false)
                .map((item) => {
                  const Icon = item.icon;
                  const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={cn(
                        "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200 group relative",
                        collapsed ? "justify-center" : "",
                        isActive
                          ? "bg-gradient-to-r from-primary/15 to-primary/5 text-primary"
                          : "text-sidebar-foreground hover:bg-muted/30 hover:text-foreground",
                      )}
                    >
                      {isActive && (
                        <>
                          <div className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-7 bg-gradient-to-b from-primary to-primary/50 rounded-r-full" />
                          <div className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-7 bg-primary rounded-r-full blur-sm opacity-60" />
                        </>
                      )}
                      <div
                        className={cn(
                          "relative flex items-center justify-center w-8 h-8 rounded-lg transition-all duration-200",
                          isActive ? "bg-primary/20" : "group-hover:bg-muted/30",
                        )}
                      >
                        <Icon
                          className={cn(
                            "w-[18px] h-[18px] transition-all duration-200",
                            isActive ? "text-primary" : "text-muted-foreground group-hover:text-foreground",
                          )}
                        />
                      </div>
                      {!collapsed && (
                        <span className={cn("flex-1 text-left text-[13px] font-medium transition-colors duration-200", isActive ? "text-primary" : "")}>
                          {item.label}
                        </span>
                      )}
                      {!collapsed && item.badge && (
                        <span
                          className={cn(
                            "badge-premium",
                            item.badgeType === "accent" ? "badge-accent" : item.badgeType === "warning" ? "badge-warning" : "badge-primary",
                          )}
                        >
                          {item.badge}
                        </span>
                      )}
                    </Link>
                  );
                })}
            </div>
          </div>
        ))}
      </nav>

      <div className="p-3 border-t border-sidebar-border/30">
        <button
          onClick={onToggleCollapsed}
          className="w-full flex items-center justify-center gap-2 py-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted/30 transition-all duration-200"
        >
          <Wrench className="w-4 h-4" />
          {!collapsed && <span className="text-xs">Recolher</span>}
        </button>
      </div>
    </aside>
  );
}

