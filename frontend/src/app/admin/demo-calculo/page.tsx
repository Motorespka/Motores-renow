"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Calculator, ChevronLeft, Save, Sparkles } from "lucide-react";

import { AppShell } from "@/components/app-shell";
import { apiFetch } from "@/lib/api";
import { requireSession } from "@/lib/auth";
import { MeResponse } from "@/lib/types";

type Stats = {
  oficial_total: number;
  file_complete: number;
  with_geometry: number;
  index_generated_at: string;
};

type Hit = {
  sha: string;
  arquivo_rel: string;
  score: number;
  diametro_mm: number;
  pacote_mm: number;
  carcaca: string;
  passo_principal: string;
  ligacao: string;
  fio_principal: string;
  espiras_historico: number;
  espiras_calculadas: number;
  fio_sugerido_awg?: number | null;
  pacote_ratio?: number;
  area_ratio?: number;
};

type SuggestResponse = {
  modo_processamento: string;
  gemini_usado: boolean;
  sugestao_espira?: number | null;
  sugestao_fio_awg?: number | null;
  justificativa_tecnica: string;
  alerta_risco: string;
  dispersao_espiras: number;
  espiras_media_top5?: number | null;
  fio_medio_top5?: number | null;
  passo_moda: string;
  carcaca_moda: string;
  n_file_catalog: number;
  n_matches: number;
  top_matches: Hit[];
  validation_status: string;
  validation_message: string;
};

export default function AdminDemoCalculoPage() {
  const router = useRouter();
  const [token, setToken] = useState("");
  const [me, setMe] = useState<MeResponse | null>(null);
  const [stats, setStats] = useState<Stats | null>(null);
  const [result, setResult] = useState<SuggestResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [okMessage, setOkMessage] = useState("");

  const [diametro, setDiametro] = useState("");
  const [pacote, setPacote] = useState("");
  const [carcaca, setCarcaca] = useState("");
  const [passo, setPasso] = useState("");
  const [ligacao, setLigacao] = useState("");
  const [fioEng, setFioEng] = useState("");
  const [espEng, setEspEng] = useState("");

  useEffect(() => {
    (async () => {
      const session = await requireSession(router);
      if (!session) return;
      setToken(session.access_token);
      const mePayload = await apiFetch<MeResponse>("/auth/me", session.access_token);
      if (!mePayload.profile.is_admin) {
        router.replace("/dashboard");
        return;
      }
      setMe(mePayload);
      try {
        const s = await apiFetch<Stats>("/admin/demo-calculo/stats", session.access_token);
        setStats(s);
      } catch {
        setStats(null);
      }
    })().catch(() => router.replace("/login"));
  }, [router]);

  async function onSuggest(e: FormEvent) {
    e.preventDefault();
    if (!token) return;
    setError("");
    setOkMessage("");
    setLoading(true);
    try {
      const d = parseFloat(diametro.replace(",", "."));
      const p = parseFloat(pacote.replace(",", "."));
      if (!d || !p) {
        setError("Informe diametro e pacote (mm) validos.");
        return;
      }
      const res = await apiFetch<SuggestResponse>("/admin/demo-calculo/suggest", token, {
        method: "POST",
        body: JSON.stringify({
          diametro_mm: d,
          pacote_mm: p,
          carcaca,
          passo,
          ligacao,
          fio_engenheiro: fioEng,
          espiras_engenheiro: espEng,
        }),
      });
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao gerar sugestao.");
    } finally {
      setLoading(false);
    }
  }

  async function onSaveOficial() {
    if (!token || !result) return;
    setError("");
    setOkMessage("");
    try {
      const d = parseFloat(diametro.replace(",", "."));
      const p = parseFloat(pacote.replace(",", "."));
      const esp = espEng || String(result.sugestao_espira ?? result.espiras_media_top5 ?? "");
      const fio = fioEng || String(result.sugestao_fio_awg ?? result.fio_medio_top5 ?? "");
      await apiFetch("/admin/demo-calculo/save-oficial", token, {
        method: "POST",
        body: JSON.stringify({
          diametro_mm: d,
          pacote_mm: p,
          carcaca,
          passo,
          ligacao,
          fio_principal: fio,
          espiras_principal: esp,
          observacoes: "Validado no admin demo-calculo",
        }),
      });
      setOkMessage("Calculo salvo no manifesto OFICIAL. Reindexe com: python scripts/index_for_search.py");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao salvar.");
    }
  }

  if (!me) {
    return <div className="center-screen">Carregando...</div>;
  }

  return (
    <AppShell
      title="Demo Calculo â€” Acervo Oficial"
      subtitle="Motor proporcional sobre 1.062 motores OFICIAIS (somente registro completo)"
      isAdmin
      userLabel={me.profile.display_name || me.profile.username || me.profile.email}
      canAccessCadastro={me.profile.cadastro_allowed}
    >
      <Link
        href="/admin"
        className="inline-flex items-center gap-1 text-[12px] text-muted-foreground hover:text-primary mb-3"
      >
        <ChevronLeft className="w-4 h-4" />
        Voltar ao painel admin
      </Link>

      {stats ? (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-4">
          <div className="premium-card p-3">
            <div className="text-[10px] text-muted-foreground">OFICIAIS</div>
            <div className="text-lg font-display">{stats.oficial_total}</div>
          </div>
          <div className="premium-card p-3">
            <div className="text-[10px] text-muted-foreground">FILE (completos)</div>
            <div className="text-lg font-display text-primary">{stats.file_complete}</div>
          </div>
          <div className="premium-card p-3">
            <div className="text-[10px] text-muted-foreground">Com geometria</div>
            <div className="text-lg font-display">{stats.with_geometry}</div>
          </div>
          <div className="premium-card p-3 col-span-2 md:col-span-1">
            <div className="text-[10px] text-muted-foreground">Indice</div>
            <div className="text-[10px] font-mono-tech truncate">{stats.index_generated_at || "â€”"}</div>
          </div>
        </div>
      ) : null}

      <form onSubmit={onSuggest} className="premium-card-elevated p-5 space-y-4">
        <div className="flex items-center gap-2">
          <Calculator className="w-5 h-5 text-primary" />
          <div className="font-display text-sm tracking-wider">ENTRADA DO MOTOR</div>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
          <Field label="Diametro estator (mm)" value={diametro} onChange={setDiametro} placeholder="80" />
          <Field label="Comprimento pacote (mm)" value={pacote} onChange={setPacote} placeholder="70" />
          <Field label="CarcaÃ§a NEMA/IEC" value={carcaca} onChange={setCarcaca} placeholder="80A" />
          <Field label="Passos bobinagem" value={passo} onChange={setPasso} placeholder="10-12 ou 1:7" />
          <Field label="Tipo de ligacao" value={ligacao} onChange={setLigacao} placeholder="Estrela / Triangulo" />
        </div>

        <div className="border-t border-border/40 pt-4">
          <div className="text-[11px] text-muted-foreground font-tech mb-2">SEU CALCULO (validacao)</div>
          <div className="grid md:grid-cols-2 gap-3">
            <Field label="Fio AWG" value={fioEng} onChange={setFioEng} placeholder="23" />
            <Field label="Espiras" value={espEng} onChange={setEspEng} placeholder="35" />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="h-11 w-full rounded-xl bg-primary/15 border border-primary/30 text-primary font-semibold tracking-wider flex items-center justify-center gap-2"
        >
          <Sparkles className="w-4 h-4" />
          {loading ? "Calculando..." : "Gerar Sugestao de Calculo"}
        </button>
      </form>

      {error ? (
        <div className="mt-3 p-3 rounded-lg border border-destructive/30 bg-destructive/10 text-[12px] text-destructive">
          {error}
        </div>
      ) : null}
      {okMessage ? (
        <div className="mt-3 p-3 rounded-lg border border-accent/30 bg-accent/10 text-[12px]">
          {okMessage}
        </div>
      ) : null}

      {result ? (
        <div className="mt-4 grid lg:grid-cols-3 gap-3">
          <Panel title="Sugestao do Sistema">
            <Row label="Modo" value={result.modo_processamento} />
            <Row label="Espiras (IA + proporcional)" value={result.sugestao_espira ?? "—"} />
            <Row label="Fio AWG sugerido" value={result.sugestao_fio_awg ?? "—"} />
            <Row label="Media proporcional (ref.)" value={result.espiras_media_top5 ?? "—"} />
            <Row label="Gemini" value={result.gemini_usado ? "Sim" : "Nao"} />
            <p className="text-[11px] text-muted-foreground mt-2 leading-relaxed">
              {result.justificativa_tecnica || "—"}
            </p>
            {result.alerta_risco ? (
              <p className="text-[11px] text-amber-400 mt-2">{result.alerta_risco}</p>
            ) : null}
          </Panel>
          <Panel title="Sua Entrada">
            <Row label="Estator" value={`${diametro} x ${pacote} mm`} />
            <Row label="CarcaÃ§a" value={carcaca || "â€”"} />
            <Row label="Passo" value={passo || "â€”"} />
            <Row label="Ligacao" value={ligacao || "â€”"} />
            <Row label="Fio / Espiras" value={`${fioEng || "â€”"} / ${espEng || "â€”"}`} />
          </Panel>
          <Panel title="Status de Validacao">
            <div className={`text-sm font-semibold status-${result.validation_status}`}>
              {result.validation_status || "â€”"}
            </div>
            <div className="text-[12px] text-muted-foreground mt-2">{result.validation_message}</div>
            <button
              type="button"
              onClick={onSaveOficial}
              className="mt-4 h-10 w-full rounded-xl border border-accent/40 bg-accent/10 flex items-center justify-center gap-2 text-[12px] font-semibold"
            >
              <Save className="w-4 h-4" />
              Salvar Novo Calculo Oficial
            </button>
          </Panel>
        </div>
      ) : null}

      {result?.top_matches?.length ? (
        <div className="mt-4 premium-card-elevated p-5 overflow-x-auto">
          <div className="font-display text-sm mb-3">Top 5 â€” proporcao aplicada</div>
          <table className="w-full text-[11px] font-tech">
            <thead>
              <tr className="text-muted-foreground text-left">
                <th className="pb-2">Arquivo</th>
                <th>Ã˜/pacote</th>
                <th>Esp. hist.</th>
                <th>Esp. calc.</th>
                <th>R pacote</th>
                <th>R area</th>
                <th>Score</th>
              </tr>
            </thead>
            <tbody>
              {result.top_matches.map((h) => (
                <tr key={h.sha} className="border-t border-border/30">
                  <td className="py-2 pr-2 max-w-[200px] truncate">{h.arquivo_rel}</td>
                  <td>
                    {h.diametro_mm}x{h.pacote_mm}
                  </td>
                  <td>{h.espiras_historico}</td>
                  <td className="text-primary font-semibold">{h.espiras_calculadas}</td>
                  <td>{h.pacote_ratio?.toFixed(3) ?? "—"}</td>
                  <td>{h.area_ratio?.toFixed(3) ?? "—"}</td>
                  <td>{h.score.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="text-[10px] text-muted-foreground mt-3">
            Formula: Espiras = Espiras_hist x (Pacote_in / Pacote_hist) x (Area_in / Area_hist)
          </div>
        </div>
      ) : null}
    </AppShell>
  );
}

function Field({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <div className="space-y-1">
      <label className="text-[11px] text-muted-foreground font-tech">{label}</label>
      <input
        className="w-full h-10 px-3 rounded-xl bg-muted/40 border border-border/50 text-sm font-tech outline-none focus:border-primary/50"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
      />
    </div>
  );
}

function Panel({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="premium-card-elevated p-4">
      <div className="font-display text-sm tracking-wider mb-3">{title}</div>
      {children}
    </div>
  );
}

function Row({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex justify-between gap-2 text-[12px] py-1 border-b border-border/20">
      <span className="text-muted-foreground">{label}</span>
      <span className="font-mono-tech text-right">{value}</span>
    </div>
  );
}

