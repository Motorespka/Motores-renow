"use client";

import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { Pencil, Save } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { MotorHologramPanel } from "@/components/MotorHologramPanel";
import { HOLOGRAM_PRESET_OPTIONS } from "@/lib/motor-hologram";
import {
  buildPreviewMotorRow,
  mergeDadosTecnicosJson,
  motorItemFromForm,
} from "@/lib/motor-edit-merge";
import { apiFetch } from "@/lib/api";
import { requireSession } from "@/lib/auth";
import {
  fetchMotorDetailFromSupabase,
  shouldFetchMotorsFromSupabase,
  updateMotorPrimaryRow,
} from "@/lib/motors-supabase";
import type { MeResponse, MotorDetailResponse, MotorRecord } from "@/lib/types";

function motorJsonFromRow(raw: Record<string, unknown>): Record<string, unknown> {
  const dt = raw.dados_tecnicos_json;
  if (dt && typeof dt === "object" && !Array.isArray(dt)) {
    const m = (dt as Record<string, unknown>).motor;
    if (m && typeof m === "object" && !Array.isArray(m)) return m as Record<string, unknown>;
  }
  return {};
}

function mecanicaJsonFromRow(raw: Record<string, unknown>): Record<string, unknown> {
  const dt = raw.dados_tecnicos_json;
  if (dt && typeof dt === "object" && !Array.isArray(dt)) {
    const m = (dt as Record<string, unknown>).mecanica;
    if (m && typeof m === "object" && !Array.isArray(m)) return m as Record<string, unknown>;
  }
  return {};
}

function observacoesFromRow(raw: Record<string, unknown>): string {
  const dt = raw.dados_tecnicos_json;
  if (dt && typeof dt === "object" && !Array.isArray(dt)) {
    const o = (dt as Record<string, unknown>).observacoes_gerais;
    if (o != null) return String(o);
  }
  return String(raw.observacoes ?? raw.Observacoes ?? "");
}

export default function MotorEditPage() {
  const router = useRouter();
  const params = useParams<{ id: string }>();
  const searchParams = useSearchParams();
  const motorId = String(params?.id || "");
  const cadastroSeqQ = searchParams.get("cadastro_seq");

  const [me, setMe] = useState<MeResponse | null>(null);
  const [detail, setDetail] = useState<MotorDetailResponse | null>(null);
  const [error, setError] = useState("");
  const [saveMsg, setSaveMsg] = useState("");
  const [saving, setSaving] = useState(false);

  const [marca, setMarca] = useState("");
  const [modelo, setModelo] = useState("");
  const [potencia, setPotencia] = useState("");
  const [rpm, setRpm] = useState("");
  const [polos, setPolos] = useState("");
  const [tensao, setTensao] = useState("");
  const [corrente, setCorrente] = useState("");
  const [hologramaPreset, setHologramaPreset] = useState("auto");
  const [hologramaGlbUrl, setHologramaGlbUrl] = useState("");
  const [carcaca, setCarcaca] = useState("");
  const [observacoesGerais, setObservacoesGerais] = useState("");

  useEffect(() => {
    (async () => {
      const session = await requireSession(router);
      if (!session) return;
      try {
        const mePayload = await apiFetch<MeResponse>("/auth/me", session.access_token);
        setMe(mePayload);
        if (!mePayload.profile.is_admin) {
          setError("Apenas administradores podem editar fichas técnicas.");
          return;
        }
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
            session.access_token,
          );
        }
        setDetail(detailPayload);
        const raw = detailPayload.raw;
        const mj = motorJsonFromRow(raw);
        const mec = mecanicaJsonFromRow(raw);
        setMarca(String(mj.marca ?? raw.marca ?? raw.Marca ?? ""));
        setModelo(String(mj.modelo ?? raw.modelo ?? raw.Modelo ?? ""));
        setPotencia(String(mj.potencia ?? raw.potencia ?? raw.Potencia ?? ""));
        setRpm(String(mj.rpm ?? raw.rpm ?? raw.Rpm ?? ""));
        setPolos(String(mj.polos ?? ""));
        const t = mj.tensao;
        setTensao(Array.isArray(t) ? t.join(", ") : String(t ?? raw.tensao ?? raw.Tensao ?? ""));
        const c = mj.corrente;
        setCorrente(Array.isArray(c) ? c.join(", ") : String(c ?? raw.corrente ?? raw.Corrente ?? ""));
        setHologramaPreset(String(mj.holograma_preset || "auto").toLowerCase().replace(/\s+/g, "_") || "auto");
        setHologramaGlbUrl(String(mj.holograma_glb_url ?? ""));
        setCarcaca(String(mec.carcaca ?? raw.carcaca ?? ""));
        setObservacoesGerais(observacoesFromRow(raw));
      } catch (err) {
        setError(err instanceof Error ? err.message : "Falha ao carregar motor.");
      }
    })();
  }, [router, motorId, cadastroSeqQ]);

  const motorPatch = useMemo(
    () => ({
      marca,
      modelo,
      potencia,
      rpm,
      polos,
      tensao,
      corrente,
      holograma_preset: hologramaPreset,
      holograma_glb_url: hologramaGlbUrl.trim(),
    }),
    [marca, modelo, potencia, rpm, polos, tensao, corrente, hologramaPreset, hologramaGlbUrl],
  );

  const mecanicaPatch = useMemo(() => ({ carcaca }), [carcaca]);

  const previewRaw = useMemo(() => {
    if (!detail) return {};
    return buildPreviewMotorRow(detail.raw, motorPatch, mecanicaPatch, observacoesGerais);
  }, [detail, motorPatch, mecanicaPatch, observacoesGerais]);

  const previewItem = useMemo(() => {
    if (!detail) return {} as MotorRecord;
    return motorItemFromForm(detail.item, motorPatch);
  }, [detail, motorPatch]);

  async function onSave() {
    if (!detail || !me?.profile.is_admin) return;
    setSaving(true);
    setSaveMsg("");
    setError("");
    try {
      const mergedJson = mergeDadosTecnicosJson(detail.raw, motorPatch, mecanicaPatch, observacoesGerais);
      const patch: Record<string, unknown> = {
        marca,
        modelo,
        potencia,
        rpm,
        tensao,
        corrente,
        observacoes: observacoesGerais,
        dados_tecnicos_json: mergedJson,
      };
      const session = await requireSession(router);
      if (!session) return;
      if (shouldFetchMotorsFromSupabase()) {
        const { error: upErr } = await updateMotorPrimaryRow(motorId, patch);
        if (upErr) {
          setError(upErr);
          return;
        }
      } else {
        await apiFetch<{ ok?: boolean }>(`/motors/${encodeURIComponent(motorId)}`, session.access_token, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(patch),
        });
      }
      setSaveMsg("Alterações gravadas.");
      router.push(
        cadastroSeqQ
          ? `/motors/${encodeURIComponent(motorId)}?cadastro_seq=${encodeURIComponent(cadastroSeqQ)}`
          : `/motors/${encodeURIComponent(motorId)}`,
      );
    } catch (e) {
      setError(e instanceof Error ? e.message : "Falha ao gravar.");
    } finally {
      setSaving(false);
    }
  }

  if (!me) {
    return <div className="center-screen text-muted">Carregando…</div>;
  }

  if (!me.profile.is_admin) {
    return (
      <AppShell
        title="Edição"
        subtitle="Acesso restrito"
        isAdmin={false}
        userLabel={me.profile.display_name || me.profile.username || me.profile.email}
        canAccessCadastro={me.profile.cadastro_allowed}
      >
        <div className="premium-card p-5 border border-destructive/30 text-destructive text-sm">{error}</div>
        <Link href="/motors" className="mt-4 inline-block text-primary text-sm">
          Voltar à consulta
        </Link>
      </AppShell>
    );
  }

  return (
    <AppShell
      title="Editar motor"
      subtitle={`ID ${motorId}${cadastroSeqQ ? ` · cadastro #${cadastroSeqQ}` : ""}`}
      isAdmin={me.profile.is_admin}
      userLabel={me.profile.display_name || me.profile.username || me.profile.email}
      canAccessCadastro={me.profile.cadastro_allowed}
    >
      {error ? (
        <div className="mb-4 p-3 rounded-lg border border-destructive/30 bg-destructive/10 text-[12px] text-destructive">
          {error}
        </div>
      ) : null}
      {saveMsg ? (
        <div className="mb-4 p-3 rounded-lg border border-primary/30 bg-primary/10 text-[12px] text-primary">{saveMsg}</div>
      ) : null}

      {!detail ? (
        <div className="text-muted text-sm">A carregar ficha…</div>
      ) : (
        <div className="grid gap-4 lg:grid-cols-3">
          <div className="lg:col-span-2 space-y-4">
            <div className="premium-card-elevated p-5">
              <div className="flex items-center gap-2 text-primary mb-4">
                <Pencil className="w-4 h-4" />
                <span className="font-display text-sm tracking-wider">IDENTIFICAÇÃO</span>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <label className="text-[11px] text-muted-foreground font-tech">
                  Marca
                  <input
                    className="mt-1 w-full rounded-xl border border-border/50 bg-muted/20 px-3 py-2 text-sm"
                    value={marca}
                    onChange={(e) => setMarca(e.target.value)}
                  />
                </label>
                <label className="text-[11px] text-muted-foreground font-tech">
                  Modelo
                  <input
                    className="mt-1 w-full rounded-xl border border-border/50 bg-muted/20 px-3 py-2 text-sm"
                    value={modelo}
                    onChange={(e) => setModelo(e.target.value)}
                  />
                </label>
                <label className="text-[11px] text-muted-foreground font-tech">
                  Potência
                  <input
                    className="mt-1 w-full rounded-xl border border-border/50 bg-muted/20 px-3 py-2 text-sm"
                    value={potencia}
                    onChange={(e) => setPotencia(e.target.value)}
                  />
                </label>
                <label className="text-[11px] text-muted-foreground font-tech">
                  RPM
                  <input
                    className="mt-1 w-full rounded-xl border border-border/50 bg-muted/20 px-3 py-2 text-sm"
                    value={rpm}
                    onChange={(e) => setRpm(e.target.value)}
                  />
                </label>
                <label className="text-[11px] text-muted-foreground font-tech">
                  Polos
                  <input
                    className="mt-1 w-full rounded-xl border border-border/50 bg-muted/20 px-3 py-2 text-sm"
                    value={polos}
                    onChange={(e) => setPolos(e.target.value)}
                  />
                </label>
                <label className="text-[11px] text-muted-foreground font-tech">
                  Tensão (texto ou lista separada por vírgula)
                  <input
                    className="mt-1 w-full rounded-xl border border-border/50 bg-muted/20 px-3 py-2 text-sm"
                    value={tensao}
                    onChange={(e) => setTensao(e.target.value)}
                  />
                </label>
                <label className="text-[11px] text-muted-foreground font-tech">
                  Corrente
                  <input
                    className="mt-1 w-full rounded-xl border border-border/50 bg-muted/20 px-3 py-2 text-sm"
                    value={corrente}
                    onChange={(e) => setCorrente(e.target.value)}
                  />
                </label>
              </div>
            </div>

            <div className="premium-card-elevated p-5">
              <div className="font-display text-sm tracking-wider text-foreground mb-3">HOLOGRAMA 3D</div>
              <label className="text-[11px] text-muted-foreground font-tech block mb-3">
                Preset
                <select
                  className="mt-1 w-full rounded-xl border border-border/50 bg-muted/20 px-3 py-2 text-sm"
                  value={hologramaPreset}
                  onChange={(e) => setHologramaPreset(e.target.value)}
                >
                  {HOLOGRAM_PRESET_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="text-[11px] text-muted-foreground font-tech block">
                URL GLB (https, opcional)
                <input
                  className="mt-1 w-full rounded-xl border border-border/50 bg-muted/20 px-3 py-2 text-sm font-mono-tech"
                  value={hologramaGlbUrl}
                  onChange={(e) => setHologramaGlbUrl(e.target.value)}
                  placeholder="https://.../modelo.glb"
                />
              </label>
            </div>

            <div className="premium-card-elevated p-5">
              <div className="font-display text-sm tracking-wider text-foreground mb-3">MECÂNICA</div>
              <label className="text-[11px] text-muted-foreground font-tech block">
                Carcaça
                <input
                  className="mt-1 w-full rounded-xl border border-border/50 bg-muted/20 px-3 py-2 text-sm"
                  value={carcaca}
                  onChange={(e) => setCarcaca(e.target.value)}
                />
              </label>
            </div>

            <div className="premium-card-elevated p-5">
              <div className="font-display text-sm tracking-wider text-foreground mb-3">OBSERVAÇÕES</div>
              <textarea
                className="w-full min-h-[100px] rounded-xl border border-border/50 bg-muted/20 px-3 py-2 text-sm"
                value={observacoesGerais}
                onChange={(e) => setObservacoesGerais(e.target.value)}
              />
            </div>

            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                disabled={saving}
                onClick={() => void onSave()}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-primary text-primary-foreground text-sm font-semibold disabled:opacity-50"
              >
                <Save className="w-4 h-4" />
                {saving ? "A gravar…" : "Gravar"}
              </button>
              {!shouldFetchMotorsFromSupabase() ? (
                <span className="text-[11px] text-muted-foreground self-center">
                  Modo API: PATCH em <code className="text-primary/80">/motors/&lt;id&gt;</code> (mock dev se token local).
                </span>
              ) : null}
              <Link
                href={
                  cadastroSeqQ
                    ? `/motors/${encodeURIComponent(motorId)}?cadastro_seq=${encodeURIComponent(cadastroSeqQ)}`
                    : `/motors/${encodeURIComponent(motorId)}`
                }
                className="inline-flex items-center px-4 py-2 rounded-xl border border-border/50 text-sm hover:bg-muted/30"
              >
                Cancelar
              </Link>
            </div>
          </div>

          <div className="space-y-3">
            <MotorHologramPanel raw={previewRaw} item={previewItem} />
            <p className="text-[10px] text-muted-foreground font-tech leading-relaxed">
              Pré-visualização com dados do formulário. A gravação actualiza <code className="text-primary/80">motores</code>{" "}
              (tabela <code className="text-primary/80">NEXT_PUBLIC_SUPABASE_PRIMARY_TABLE</code>) e{" "}
              <code className="text-primary/80">dados_tecnicos_json</code>.
            </p>
          </div>
        </div>
      )}
    </AppShell>
  );
}
