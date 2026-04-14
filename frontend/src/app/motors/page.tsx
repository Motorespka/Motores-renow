"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { apiFetch } from "@/lib/api";
import { requireSession } from "@/lib/auth";
import { MeResponse, MotorListResponse } from "@/lib/types";

export default function MotorsPage() {
  const router = useRouter();
  const [token, setToken] = useState("");
  const [me, setMe] = useState<MeResponse | null>(null);
  const [payload, setPayload] = useState<MotorListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [q, setQ] = useState("");

  async function loadData(search: string, accessToken?: string) {
    const tokenResolved = accessToken || token;
    if (!tokenResolved) return;
    setLoading(true);
    setError("");
    try {
      const query = search ? `?q=${encodeURIComponent(search)}&limit=50` : "?limit=50";
      const list = await apiFetch<MotorListResponse>(`/motors${query}`, tokenResolved);
      setPayload(list);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Falha ao carregar motores.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    (async () => {
      const session = await requireSession(router);
      if (!session) return;
      setToken(session.access_token);
      try {
        const mePayload = await apiFetch<MeResponse>("/auth/me", session.access_token);
        setMe(mePayload);
      } catch {
        router.replace("/login");
        return;
      }
      await loadData("", session.access_token);
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router]);

  function onSearch(event: FormEvent) {
    event.preventDefault();
    void loadData(q);
  }

  if (!me) {
    return <div className="center-screen text-muted">Carregando consulta...</div>;
  }

  const isAdmin = me.profile.is_admin;
  const mode = payload?.mode || "teaser";
  return (
    <AppShell
      title="Consulta de Motores"
      subtitle={mode === "teaser" ? "Modo teaser (free)" : "Modo completo (pago/admin)"}
      isAdmin={isAdmin}
      userLabel={me.profile.display_name || me.profile.username || me.profile.email}
      canAccessCadastro={me.profile.cadastro_allowed}
    >
      <div className="card">
        <form onSubmit={onSearch} style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <input
            style={{ flex: 1, minWidth: 240 }}
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Buscar por marca, modelo, potencia, rpm..."
          />
          <button className="btn" type="submit">
            Buscar
          </button>
        </form>
      </div>

      {mode === "teaser" ? (
        <div className="card" style={{ marginTop: 12 }}>
          <span className="badge">MODO TEASER</span>
          <p className="text-muted">
            Sua conta está em visualização limitada. Ative plano pago para detalhes e diagnóstico.
          </p>
        </div>
      ) : null}

      {error ? <div className="error" style={{ marginTop: 12 }}>{error}</div> : null}
      {loading ? <div className="text-muted">Carregando...</div> : null}

      <div className="motors-list" style={{ marginTop: 12 }}>
        {(payload?.items || []).map((m) => (
          <div key={String(m.id)} className="motor-row">
            <div>{String(m.marca || "Motor")}</div>
            <div>{String(m.modelo || "-")}</div>
            <div>{String(m.potencia || "-")}</div>
            {mode === "full" ? (
              <Link href={`/motors/${m.id}`} className="btn secondary">
                Detalhes
              </Link>
            ) : (
              <span className="text-muted">Upgrade</span>
            )}
          </div>
        ))}
      </div>
    </AppShell>
  );
}
