"use client";

import Link from "next/link";
import { ChevronLeft } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { DigitalTwinDashboard } from "@/components/digital-twin";

/**
 * Prévia do layout Gêmeo Digital (mockup PMTH).
 * Conecte à API `/admin/demo-calculo` quando migrar do Streamlit.
 */
export default function GemeoDigitalPage() {
  const mockOriginal = {
    badge: "Coluna A — Original",
    title: "Original (sucata / informado)",
    turns: 45,
    wire: "1×19 AWG",
    jAmm2: 4.82,
    ff: 0.42,
    bTesla: 1.25,
  };

  const mockProposed = {
    badge: "Coluna B — Proposta",
    title: "Proposta (rebobinagem)",
    turns: 45,
    wire: "18 AWG",
    jAmm2: 4.82,
    ff: 0.42,
    bTesla: 1.62,
  };

  return (
    <AppShell
      title="Gêmeo Digital de Motores"
      subtitle="Prévia do design system — Streamlit + Next"
      isAdmin
      userLabel="PMTH"
    >
      <Link
        href="/dashboard"
        className="inline-flex items-center gap-1 text-[12px] text-muted-foreground hover:text-primary mb-4"
      >
        <ChevronLeft className="w-4 h-4" />
        Voltar
      </Link>

      <div className="premium-card-elevated p-5 max-w-5xl">
        <p className="text-[11px] text-muted-foreground font-tech mb-4">
          Componentes em{" "}
          <code className="text-primary">frontend/src/components/digital-twin/</code> · tokens em{" "}
          <code className="text-primary">design-system/digital-twin-tokens.json</code>
        </p>

        <DigitalTwinDashboard
          approved
          confidencePct={94.6}
          deviationPct={0.8}
          stackLengthMm={120}
          original={mockOriginal}
          proposed={mockProposed}
          onGeneratePdf={() => window.alert("Conectar endpoint de laudo PDF")}
        />
      </div>
    </AppShell>
  );
}
