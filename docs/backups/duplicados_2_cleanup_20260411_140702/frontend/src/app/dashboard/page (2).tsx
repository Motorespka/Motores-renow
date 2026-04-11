"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { apiFetch } from "@/lib/api";
import { requireSession } from "@/lib/auth";
import { MeResponse } from "@/lib/types";

export default function DashboardPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [me, setMe] = useState<MeResponse | null>(null);

  useEffect(() => {
    (async () => {
      setLoading(true);
      setError("");
      const session = await requireSession(router);
      if (!session) return;
      try {
        const payload = await apiFetch<MeResponse>("/auth/me", session.access_token);
        setMe(payload);
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Falha ao carregar perfil.";
        setError(msg);
      } finally {
        setLoading(false);
      }
    })();
  }, [router]);

  if (loading) {
    return <div className="center-screen text-muted">Carregando dashboard...</div>;
  }

  if (!me) {
    return <div className="center-screen error">{error || "Sessao invalida."}</div>;
  }

  const isAdmin = me.profile.is_admin;
  return (
    <AppShell
      title="Dashboard"
      subtitle={`Plano ${me.profile.plan} | Acesso ${me.profile.tier}`}
      isAdmin={isAdmin}
      userLabel={me.profile.display_name || me.profile.username || me.profile.email}
      canAccessCadastro={me.profile.cadastro_allowed}
    >
      <div className="grid cards">
        <div className="card kpi">
          <div className="label">Conta</div>
          <div className="value">{me.profile.ativo ? "Ativa" : "Inativa"}</div>
        </div>
        <div className="card kpi">
          <div className="label">Role</div>
          <div className="value">{me.profile.role || "user"}</div>
        </div>
        <div className="card kpi">
          <div className="label">Plano</div>
          <div className="value">{me.profile.plan}</div>
        </div>
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <h3>Atalhos</h3>
        <div className="grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))" }}>
          <Link className="btn" href="/motors">
            Ir para Consulta
          </Link>
          {me.profile.cadastro_allowed ? (
            <Link className="btn secondary" href="/cadastro">
              Ir para Cadastro
            </Link>
          ) : null}
          {isAdmin ? (
            <Link className="btn secondary" href="/admin">
              Painel Admin
            </Link>
          ) : null}
        </div>
      </div>
    </AppShell>
  );
}
