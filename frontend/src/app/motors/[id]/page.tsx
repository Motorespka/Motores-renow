"use client";

import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { ClipboardList, Pencil, Wrench } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { MotorFichaOficina } from "@/components/MotorFichaOficina";
import { MotorHologramPanel } from "@/components/MotorHologramPanel";
import { apiFetch } from "@/lib/api";
import { profileFromSession, requireSession } from "@/lib/auth";
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
        if (shouldFetchMotorsFromSupabase()) {
          setMe(profileFromSession(session) as MeResponse);
        } else {
          try {
            setMe(await apiFetch<MeResponse>("/auth/me", session.access_token));
          } catch {
            setMe(profileFromSession(session) as MeResponse);
          }
        }

        let detailPayload: MotorDetailResponse;
        if (shouldFetchMotorsFromSupabase()) {
          const direct = await fetchMotorDetailFromSupabase(motorId, cadastroSeqQ);
          if (!direct) {
            setError("Motor não encontrado ou sem permissão de leitura.");
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
    return <div className="center-screen">A carregar ficha do motor…</div>;
  }

  const marca = String(detail?.item.marca || "Motor");
  const modelo = String(detail?.item.modelo || "");
  const title = `${marca}${modelo ? ` ${modelo}` : ""}`.trim();

  return (
    <AppShell
      title={title}
      subtitle="Ficha técnica de oficina"
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
        <div className="space-y-4">
          <div className="premium-card-elevated p-4 sm:p-5 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <span className="badge-premium badge-primary">FICHA TÉCNICA</span>
                <span className="badge-premium badge-accent">OFICINA</span>
              </div>
              <h1 className="mt-2 font-display text-xl font-bold tracking-wide text-foreground sm:text-2xl truncate">
                {title}
              </h1>
              <p className="mt-1 text-[12px] text-muted-foreground font-tech">
                {detail.item.cadastro_seq != null ? (
                  <>
                    Cadastro #{detail.item.cadastro_seq}
                    <span className="text-muted-foreground/60"> · </span>
                    ID <span className="font-mono-tech">{motorId}</span>
                  </>
                ) : (
                  <>
                    ID <span className="font-mono-tech">{motorId}</span>
                  </>
                )}
                <span className="text-muted-foreground/60"> · </span>
                Potência {String(detail.item.potencia || "—")}
                <span className="text-muted-foreground/60"> · </span>
                {String(detail.item.rpm || "—")} rpm
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2 shrink-0">
              {(me.profile.is_admin || me.profile.cadastro_allowed) && (
                <Link
                  href={
                    cadastroSeqQ
                      ? `/motors/${encodeURIComponent(motorId)}/edit?cadastro_seq=${encodeURIComponent(cadastroSeqQ)}`
                      : `/motors/${encodeURIComponent(motorId)}/edit`
                  }
                  className="text-[11px] px-3 py-2 rounded-xl border border-primary/30 bg-primary/10 text-primary hover:bg-primary/15 transition-colors inline-flex items-center gap-1.5"
                >
                  <Pencil className="w-3.5 h-3.5" />
                  Editar ficha
                </Link>
              )}
              <Link
                href="/motors"
                className="text-[11px] px-3 py-2 rounded-xl border border-border/40 bg-muted/20 hover:bg-muted/40 text-muted-foreground hover:text-foreground transition-colors"
              >
                Voltar à consulta
              </Link>
            </div>
          </div>

          <div className="grid gap-4 xl:grid-cols-[1.35fr_0.65fr]">
            <MotorFichaOficina raw={detail.raw} />

            <aside className="space-y-4 xl:sticky xl:top-4 xl:self-start">
              <MotorHologramPanel raw={detail.raw} item={detail.item} />

              <div className="premium-card-elevated p-4 space-y-3">
                <div className="flex items-center gap-2">
                  <Wrench className="h-4 w-4 text-primary" />
                  <div className="font-display text-sm tracking-wider text-foreground">OPERAÇÃO</div>
                </div>
                <p className="text-[11px] text-muted-foreground font-tech leading-relaxed">
                  Atalhos de oficina para este motor — OS, diagnóstico e novo cadastro.
                </p>
                <div className="grid gap-2">
                  <Link
                    href="/diagnostico"
                    className="w-full text-center h-10 flex items-center justify-center gap-2 rounded-xl bg-muted/30 border border-border/40 text-foreground/90 hover:bg-muted/50 transition-colors text-[12px]"
                  >
                    <ClipboardList className="h-3.5 w-3.5" />
                    Abrir diagnóstico
                  </Link>
                  <Link
                    href="/conferencia"
                    className="w-full text-center h-10 flex items-center justify-center rounded-xl bg-muted/30 border border-border/40 text-foreground/90 hover:bg-muted/50 transition-colors text-[12px]"
                  >
                    Conferência técnica
                  </Link>
                  <Link
                    href="/cadastro"
                    className="w-full text-center h-10 flex items-center justify-center rounded-xl bg-primary/15 border border-primary/25 text-primary font-semibold tracking-wider hover:bg-primary/20 transition-colors text-[12px]"
                  >
                    Novo cadastro / OCR
                  </Link>
                </div>
              </div>
            </aside>
          </div>
        </div>
      ) : !error ? (
        <div className="center-screen text-muted-foreground font-tech text-sm">A montar ficha…</div>
      ) : null}
    </AppShell>
  );
}
