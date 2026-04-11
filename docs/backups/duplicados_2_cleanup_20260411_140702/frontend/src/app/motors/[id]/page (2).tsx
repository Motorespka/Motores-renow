"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { apiFetch } from "@/lib/api";
import { requireSession } from "@/lib/auth";
import { MeResponse, MotorDetailResponse } from "@/lib/types";

export default function MotorDetailPage() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const motorId = String(params?.id || "");

  const [me, setMe] = useState<MeResponse | null>(null);
  const [detail, setDetail] = useState<MotorDetailResponse | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    (async () => {
      const session = await requireSession(router);
      if (!session) return;
      try {
        const mePayload = await apiFetch<MeResponse>("/auth/me", session.access_token);
        setMe(mePayload);
        const detailPayload = await apiFetch<MotorDetailResponse>(`/motors/${encodeURIComponent(motorId)}`, session.access_token);
        setDetail(detailPayload);
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Falha ao carregar detalhe.";
        setError(msg);
      }
    })();
  }, [router, motorId]);

  if (!me) {
    return <div className="center-screen text-muted">Carregando detalhe...</div>;
  }

  return (
    <AppShell
      title={`Motor #${motorId}`}
      subtitle="Detalhamento tecnico"
      isAdmin={me.profile.is_admin}
      userLabel={me.profile.display_name || me.profile.username || me.profile.email}
      canAccessCadastro={me.profile.cadastro_allowed}
    >
      {error ? (
        <div className="error">
          {error}
          <div style={{ marginTop: 10 }}>
            <Link href="/motors" className="btn secondary">
              Voltar para consulta
            </Link>
          </div>
        </div>
      ) : null}

      {detail ? (
        <div className="card">
          <h3>
            {String(detail.item.marca || "Motor")} | {String(detail.item.modelo || "-")}
          </h3>
          <p className="text-muted">Potência: {String(detail.item.potencia || "-")}</p>
          <p className="text-muted">RPM: {String(detail.item.rpm || "-")}</p>
          <details>
            <summary>JSON técnico completo</summary>
            <pre style={{ whiteSpace: "pre-wrap", overflowWrap: "anywhere" }}>
              {JSON.stringify(detail.raw, null, 2)}
            </pre>
          </details>
        </div>
      ) : null}
    </AppShell>
  );
}
