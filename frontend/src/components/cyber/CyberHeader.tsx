"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { Bell, HelpCircle, Plus, Search, Settings, Shield, User } from "lucide-react";

const sectionTitles: Record<string, { title: string; subtitle: string }> = {
  dashboard: { title: "VISÃO GERAL", subtitle: "Painel operacional do workspace" },
  motors: { title: "CONSULTA TÉCNICA", subtitle: "Base de motores cadastrados" },
  cadastro: { title: "CADASTRO / OCR", subtitle: "Leitura de plaqueta e revisão assistida" },
  diagnostic: { title: "DIAGNÓSTICO TÉCNICO", subtitle: "Análise assistida de condição" },
  conference: { title: "CONFERÊNCIA TÉCNICA", subtitle: "Checklist de validação e aprovação" },
  admin: { title: "ADMINISTRAÇÃO", subtitle: "Controle do workspace" },
  settings: { title: "CONFIGURAÇÕES", subtitle: "Preferências e integrações do sistema" },
};

export function CyberHeader({
  activeSection = "dashboard",
  userName = "Técnico",
}: {
  activeSection?: string;
  userName?: string;
}) {
  const [searchFocused, setSearchFocused] = useState(false);
  const { title, subtitle } = sectionTitles[activeSection] || sectionTitles.dashboard;

  return (
    <header className="h-16 border-b border-border/50 bg-card/80 backdrop-blur-md flex items-center justify-between px-6 relative">
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-primary/30 to-transparent" />

      <div className="flex items-center gap-4 min-w-0">
        <div className="flex items-center gap-3 min-w-0">
          <div className="relative flex-shrink-0">
            <div className="w-2 h-8 rounded-full bg-gradient-to-b from-primary to-primary/30" />
            <div className="absolute inset-0 w-2 h-8 rounded-full bg-primary/50 blur-sm" />
          </div>
          <div className="flex flex-col min-w-0">
            <h1 className="font-display text-base font-bold tracking-wider text-foreground truncate">{title}</h1>
            <p className="text-[10px] text-muted-foreground tracking-wide font-tech truncate">{subtitle}</p>
          </div>
        </div>
      </div>

      <div className="absolute left-1/2 -translate-x-1/2 w-full max-w-md px-4">
        <div className={cn("relative transition-all duration-300", searchFocused ? "scale-105" : "")}>
          <Search
            className={cn(
              "absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 transition-colors duration-200",
              searchFocused ? "text-primary" : "text-muted-foreground",
            )}
          />
          <input
            type="text"
            placeholder="Buscar motor, série, fabricante, laudo..."
            onFocus={() => setSearchFocused(true)}
            onBlur={() => setSearchFocused(false)}
            className={cn(
              "w-full h-10 pl-11 pr-4 rounded-xl bg-muted/50 border text-sm font-tech",
              "placeholder:text-muted-foreground/60 transition-all duration-300 focus:outline-none",
              searchFocused
                ? "border-primary/50 bg-muted shadow-[0_0_20px_rgba(var(--glow-primary-rgb),0.1)]"
                : "border-border/50 hover:border-border",
            )}
          />
        </div>
      </div>

      <div className="flex items-center gap-2">
        <button className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-primary/10 border border-primary/20 text-primary hover:bg-primary/15 transition-all duration-200">
          <Plus className="w-3.5 h-3.5" />
          <span className="text-[11px] font-semibold tracking-wider">NOVO</span>
        </button>

        <div className="h-8 w-px bg-border/30 mx-1" />

        <HeaderIconButton icon={HelpCircle} tooltip="Ajuda" />
        <HeaderIconButton icon={Settings} tooltip="Configurações" />
        <HeaderIconButton icon={Bell} tooltip="Notificações" badge={0} />

        <div className="h-8 w-px bg-border/30 mx-1" />

        <button className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-muted/50 transition-all duration-200 group">
          <div className="relative">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary/30 to-primary/10 border border-primary/30 flex items-center justify-center">
              <User className="w-4 h-4 text-primary" />
            </div>
            <div className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-accent border-2 border-card" />
          </div>
          <div className="hidden xl:flex flex-col items-start">
            <span className="text-xs font-medium text-foreground">{userName}</span>
            <span className="text-[10px] text-muted-foreground flex items-center gap-1">
              <Shield className="w-2.5 h-2.5" />
              Workspace
            </span>
          </div>
        </button>
      </div>
    </header>
  );
}

function HeaderIconButton({
  icon: Icon,
  tooltip,
  badge,
}: {
  icon: React.ElementType;
  tooltip: string;
  badge?: number;
}) {
  return (
    <button
      className="relative p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted/50 transition-all duration-200"
      title={tooltip}
    >
      <Icon className="w-[18px] h-[18px]" />
      {badge && badge > 0 && (
        <span className="absolute -top-0.5 -right-0.5 min-w-[16px] h-4 flex items-center justify-center px-1 rounded-full bg-destructive text-[9px] font-bold text-destructive-foreground">
          {badge}
        </span>
      )}
    </button>
  );
}

