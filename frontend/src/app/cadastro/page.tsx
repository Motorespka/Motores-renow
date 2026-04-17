"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { API_BASE, ApiRequestError, apiFetch } from "@/lib/api";
import { requireSession } from "@/lib/auth";
import {
  CadastroAnalyzeResponse,
  CadastroSaveResponse,
  MeResponse
} from "@/lib/types";

export default function CadastroPage() {
  const router = useRouter();
  const [token, setToken] = useState("");
  const [me, setMe] = useState<MeResponse | null>(null);
  const [files, setFiles] = useState<File[]>([]);
  const [normalizedText, setNormalizedText] = useState("{}");
  const [imageUrls, setImageUrls] = useState<string[]>([]);
  const [fileNames, setFileNames] = useState<string[]>([]);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [loadingAnalyze, setLoadingAnalyze] = useState(false);
  const [loadingSave, setLoadingSave] = useState(false);
  const [error, setError] = useState("");
  const [okMessage, setOkMessage] = useState("");

  const canAccessCadastro = Boolean(me?.profile?.cadastro_allowed);

  useEffect(() => {
    (async () => {
      const session = await requireSession(router);
      if (!session) return;
      setToken(session.access_token);
      const mePayload = await apiFetch<MeResponse>("/auth/me", session.access_token);
      setMe(mePayload);
    })().catch(() => {
      router.replace("/login");
    });
  }, [router]);

  const fileLabel = useMemo(() => {
    if (!files.length) return "Nenhum arquivo selecionado.";
    return `${files.length} arquivo(s): ${files.map((f) => f.name).join(", ")}`;
  }, [files]);

  async function analyzeFiles() {
    if (!token || !files.length) {
      setError("Selecione pelo menos 1 imagem para analisar.");
      return;
    }

    setError("");
    setOkMessage("");
    setLoadingAnalyze(true);
    try {
      if (token === "dev") {
        const names = files.map((f) => f.name);
        setFileNames(names);
        setImageUrls(names.map((_, idx) => `dev://image/${idx + 1}`));
        setWarnings(["Modo DEV: análise simulada (backend/Gemini não executado)."]);
        setNormalizedText(
          JSON.stringify(
            {
              fabricante: "WEG",
              modelo: "W22",
              potencia: "10 CV",
              rpm: "1750",
              tensao: "220/380V",
              observacao: "Mock local para validar o fluxo de cadastro.",
            },
            null,
            2
          )
        );
        setOkMessage("Análise simulada concluída (DEV).");
        return;
      }

      const form = new FormData();
      files.forEach((file) => form.append("files", file));
      const response = await fetch(`${API_BASE}/cadastro/analyze`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`
        },
        body: form
      });
      if (!response.ok) {
        let detail = "Falha ao analisar arquivos.";
        try {
          const payload = (await response.json()) as { detail?: string };
          if (payload.detail) detail = payload.detail;
        } catch {
          // ignore
        }
        throw new ApiRequestError(response.status, detail);
      }

      const payload = (await response.json()) as CadastroAnalyzeResponse;
      setNormalizedText(JSON.stringify(payload.normalized_data || {}, null, 2));
      setImageUrls(payload.image_urls || []);
      setFileNames(payload.file_names || []);
      setWarnings(payload.warnings || []);
      setOkMessage(payload.message || "Analise concluida.");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Falha ao analisar.";
      setError(message);
    } finally {
      setLoadingAnalyze(false);
    }
  }

  async function saveCadastro() {
    if (!token) return;
    setError("");
    setOkMessage("");
    setLoadingSave(true);
    try {
      let normalizedData: Record<string, unknown> = {};
      try {
        normalizedData = JSON.parse(normalizedText || "{}") as Record<string, unknown>;
      } catch {
        throw new Error("JSON de dados tecnicos invalido. Corrija antes de salvar.");
      }

      if (token === "dev") {
        setWarnings(["Modo DEV: salvamento simulado (não grava no Supabase)."]);
        setOkMessage("Cadastro simulado salvo (DEV). Estrategia: dev-mock | ID: dev-0001");
        return;
      }

      const payload = await apiFetch<CadastroSaveResponse>("/cadastro/save", token, {
        method: "POST",
        body: JSON.stringify({
          normalized_data: normalizedData,
          file_names: fileNames,
          image_urls: imageUrls
        })
      });
      setWarnings(payload.warnings || []);
      setOkMessage(
        `${payload.message} Estrategia: ${payload.strategy || "-"} | ID: ${String(payload.inserted_id ?? "-")}`
      );
    } catch (err) {
      const message = err instanceof Error ? err.message : "Falha ao salvar cadastro.";
      setError(message);
    } finally {
      setLoadingSave(false);
    }
  }

  if (!me) {
    return <div className="center-screen text-muted">Carregando cadastro...</div>;
  }

  return (
    <AppShell
      title="Cadastro Tecnico"
      subtitle="Upload de imagem, leitura Gemini e salvamento via backend"
      isAdmin={me.profile.is_admin}
      userLabel={me.profile.display_name || me.profile.username || me.profile.email}
      canAccessCadastro={me.profile.cadastro_allowed}
    >
      {!canAccessCadastro ? (
        <div className="p-3 rounded-lg border border-destructive/30 bg-destructive/10 text-[12px] text-destructive">
          Sem permissão para cadastro. Necessário admin, plano pago ou liberação manual.
        </div>
      ) : (
        <>
          <div className="premium-card-elevated p-5">
            <div className="flex items-center justify-between gap-2">
              <div>
                <div className="font-display text-sm tracking-wider">CADASTRO / OCR</div>
                <div className="text-[11px] text-muted-foreground font-tech mt-1">
                  Upload de imagem e extração de dados técnicos (DEV com fallback).
                </div>
              </div>
              <span className="badge-premium badge-accent">OCR</span>
            </div>

            <div className="mt-4 grid gap-3">
              <div className="premium-card p-4">
                <div className="text-[11px] text-muted-foreground font-tech">1) Upload</div>
                <input
                  className="mt-2 block w-full text-[12px] font-tech"
                  type="file"
                  accept="image/*"
                  multiple
                  onChange={(e) => setFiles(Array.from(e.target.files || []))}
                />
                <div className="mt-2 text-[11px] text-muted-foreground font-tech">{fileLabel}</div>
                <button
                  className="mt-3 h-10 px-4 rounded-xl bg-primary/15 border border-primary/25 text-primary font-semibold tracking-wider hover:bg-primary/20 transition-colors disabled:opacity-60"
                  onClick={analyzeFiles}
                  disabled={loadingAnalyze || !files.length}
                  type="button"
                >
                  {loadingAnalyze ? "Analisando..." : token === "dev" ? "Analisar (DEV)" : "Analisar com Gemini"}
                </button>
              </div>
            </div>
          </div>

          <div className="mt-3 premium-card-elevated p-5">
            <div className="flex items-center justify-between gap-2">
              <div>
                <div className="font-display text-sm tracking-wider">REVISAR JSON</div>
                <div className="text-[11px] text-muted-foreground font-tech mt-1">
                  Ajuste os dados técnicos antes de salvar.
                </div>
              </div>
              <span className="badge-premium badge-primary">DATA</span>
            </div>

            <textarea
              className="mt-4 w-full min-h-[360px] rounded-xl bg-muted/20 border border-border/40 p-3 text-[11px] font-mono-tech outline-none focus:border-primary/50 focus:shadow-[0_0_20px_rgba(var(--glow-primary-rgb),0.10)]"
              value={normalizedText}
              onChange={(e) => setNormalizedText(e.target.value)}
              rows={18}
            />

            <div className="mt-3 flex items-center gap-2 flex-wrap">
              <button
                className="h-10 px-4 rounded-xl bg-primary/15 border border-primary/25 text-primary font-semibold tracking-wider hover:bg-primary/20 transition-colors disabled:opacity-60"
                style={{ marginTop: 0 }}
                onClick={saveCadastro}
                disabled={loadingSave}
                type="button"
              >
                {loadingSave ? "Salvando..." : token === "dev" ? "Salvar (DEV)" : "Salvar cadastro no Supabase"}
              </button>
              <span className="text-[11px] text-muted-foreground font-tech">
                Backend: <span className="font-mono-tech">{API_BASE}</span>
              </span>
            </div>
          </div>
        </>
      )}

      {error ? (
        <div className="mt-3 p-3 rounded-lg border border-destructive/30 bg-destructive/10 text-[12px] text-destructive">
          {error}
        </div>
      ) : null}
      {okMessage ? (
        <div className="mt-3 p-3 rounded-lg border border-accent/30 bg-accent/10 text-[12px] text-foreground">
          {okMessage}
        </div>
      ) : null}

      {warnings.length ? (
        <div className="mt-3 premium-card p-4">
          <div className="flex items-center justify-between">
            <div className="font-display text-sm tracking-wider">AVISOS</div>
            <span className="badge-premium badge-warning">WARN</span>
          </div>
          <div className="mt-2 grid gap-1">
            {warnings.map((warning, idx) => (
              <div className="text-[12px] text-muted-foreground font-tech" key={`${warning}-${idx}`}>
                - {warning}
              </div>
            ))}
          </div>
        </div>
      ) : null}
    </AppShell>
  );
}

