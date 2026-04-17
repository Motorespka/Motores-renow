"use client";

import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { Cpu, FileJson, Gauge, Tag } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { apiFetch } from "@/lib/api";
import { requireSession } from "@/lib/auth";
import { fetchMotorDetailFromSupabase, shouldFetchMotorsFromSupabase } from "@/lib/motors-supabase";
import { MeResponse, MotorDetailResponse } from "@/lib/types";

export default function MotorDetailPage() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const motorId = String(params?.id || "");
  const cadastroSeqQ = searchParams.get("cadastro_seq");

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
        let detailPayload: MotorDetailResponse;
        if (shouldFetchMotorsFromSupabase()) {
          const direct = await fetchMotorDetailFromSupabase(motorId, cadastroSeqQ);
          if (!direct) {
            setError("Motor nao encontrado ou sem permissao (RLS).");
            return;
          }
          detailPayload = direct;
        } else {
          detailPayload = await apiFetch<MotorDetailResponse>(
            `/motors/${encodeURIComponent(motorId)}`,
            session.access_token
          );
        }
        setDetail(detailPayload);
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Falha ao carregar detalhe.";
        setError(msg);
      }
    })();
  }, [router, motorId, cadastroSeqQ]);

  if (!me) {
    return <div className="center-screen text-muted">Carregando detalhe...</div>;
  }

  return (
    <AppShell
      title={
        cadastroSeqQ
          ? `Motor cadastro #${cadastroSeqQ}`
          : `Motor #${motorId}`
      }
      subtitle={
        cadastroSeqQ
          ? `Referencia interna Supabase: ${motorId}`
          : "Detalhamento tecnico"
      }
      isAdmin={me.profile.is_admin}
      userLabel={me.profile.display_name || me.profile.username || me.profile.email}
      canAccessCadastro={me.profile.cadastro_allowed}
    >
      {error ? (
        <div className="p-3 rounded-lg border border-destructive/30 bg-destructive/10 text-[12px] text-destructive">
          {error}
          <div className="mt-3">
            <Link
              href="/motors"
              className="text-[11px] px-3 py-2 rounded-xl border border-border/40 bg-muted/20 hover:bg-muted/40 text-muted-foreground hover:text-foreground transition-colors"
            >
              Voltar para consulta
            </Link>
          </div>
        </div>
      ) : null}

      {detail ? (
        <div className="grid gap-3 lg:grid-cols-3">
          <div className="lg:col-span-2 premium-card-elevated p-5">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="badge-premium badge-primary">MOTOR</span>
                  <span className="badge-premium badge-accent">TECH</span>
                </div>
                <div className="mt-2 font-display text-base tracking-wider text-foreground">
                  {String(detail.item.marca || "Motor")} {String(detail.item.modelo || "-")}
                </div>
                <div className="text-[11px] text-muted-foreground font-tech mt-1">
                  {detail.item.cadastro_seq != null ? (
                    <>
                      Cadastro #{detail.item.cadastro_seq}
                      <span className="text-muted-foreground/70"> · ref </span>
                      <span className="font-mono-tech">{motorId}</span>
                    </>
                  ) : (
                    <>
                      ID: <span className="font-mono-tech">{motorId}</span>
                    </>
                  )}
                </div>
              </div>
              <Link
                href="/motors"
                className="text-[11px] px-3 py-2 rounded-xl border border-border/40 bg-muted/20 hover:bg-muted/40 text-muted-foreground hover:text-foreground transition-colors shrink-0"
              >
                Voltar
              </Link>
            </div>

            <div className="mt-4 grid gap-3 md:grid-cols-3">
              <div className="premium-card p-4">
                <div className="flex items-center justify-between">
                  <div className="text-[11px] text-muted-foreground font-tech">Potência</div>
                  <Cpu className="w-4 h-4 text-primary" />
                </div>
                <div className="mt-1 font-display text-lg tracking-wider">{String(detail.item.potencia || "-")}</div>
              </div>
              <div className="premium-card p-4">
                <div className="flex items-center justify-between">
                  <div className="text-[11px] text-muted-foreground font-tech">RPM</div>
                  <Gauge className="w-4 h-4 text-primary" />
                </div>
                <div className="mt-1 font-display text-lg tracking-wider">{String(detail.item.rpm || "-")}</div>
              </div>
              <div className="premium-card p-4">
                <div className="flex items-center justify-between">
                  <div className="text-[11px] text-muted-foreground font-tech">Modelo</div>
                  <Tag className="w-4 h-4 text-primary" />
                </div>
                <div className="mt-1 font-display text-lg tracking-wider">{String(detail.item.modelo || "-")}</div>
              </div>
            </div>

            <div className="mt-4 premium-card p-4">
              <div className="flex items-center justify-between gap-2">
                <div>
                  <div className="font-display text-sm tracking-wider">JSON TÉCNICO</div>
                  <div className="text-[11px] text-muted-foreground font-tech mt-1">
                    Estrutura completa (útil para depuração/validação).
                  </div>
                </div>
                <FileJson className="w-4 h-4 text-primary" />
              </div>
              <pre className="mt-3 text-[11px] leading-relaxed bg-muted/20 border border-border/40 rounded-xl p-3 overflow-auto max-h-[420px] font-mono-tech">
                {JSON.stringify(detail.raw, null, 2)}
              </pre>
            </div>
          </div>

          <div className="premium-card-elevated p-5">
            <div className="font-display text-sm tracking-wider">AÇÕES</div>
            <div className="text-[11px] text-muted-foreground font-tech mt-1">Atalhos relacionados a este motor.</div>

            <div className="mt-4 grid gap-2">
              <Link
                href="/motors"
                className="w-full text-center h-10 flex items-center justify-center rounded-xl bg-muted/30 border border-border/40 text-foreground/90 hover:bg-muted/50 transition-colors"
              >
                Voltar para lista
              </Link>
              <Link
                href="/cadastro"
                className="w-full text-center h-10 flex items-center justify-center rounded-xl bg-primary/15 border border-primary/25 text-primary font-semibold tracking-wider hover:bg-primary/20 transition-colors"
              >
                Novo cadastro / OCR
              </Link>
            </div>
          </div>
        </div>
      ) : null}
    </AppShell>
  );
}
