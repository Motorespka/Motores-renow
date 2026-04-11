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
        <div className="card error">
          Sem permissao para cadastro. Necessario admin, plano pago ou liberacao manual.
        </div>
      ) : (
        <>
          <div className="card">
            <h3>1) Upload</h3>
            <input
              type="file"
              accept="image/*"
              multiple
              onChange={(e) => setFiles(Array.from(e.target.files || []))}
            />
            <p className="text-muted">{fileLabel}</p>
            <button className="btn" onClick={analyzeFiles} disabled={loadingAnalyze || !files.length}>
              {loadingAnalyze ? "Analisando..." : "Analisar com Gemini"}
            </button>
          </div>

          <div className="card" style={{ marginTop: 12 }}>
            <h3>2) Revisar JSON tecnico</h3>
            <textarea
              value={normalizedText}
              onChange={(e) => setNormalizedText(e.target.value)}
              rows={18}
              style={{
                width: "100%",
                borderRadius: 10,
                border: "1px solid var(--line)",
                background: "#0a1323",
                color: "var(--ink)",
                padding: 12,
                fontFamily: "Consolas, monospace"
              }}
            />
            <button className="btn" style={{ marginTop: 12 }} onClick={saveCadastro} disabled={loadingSave}>
              {loadingSave ? "Salvando..." : "Salvar cadastro no Supabase"}
            </button>
          </div>
        </>
      )}

      {error ? <div className="error" style={{ marginTop: 12 }}>{error}</div> : null}
      {okMessage ? <div className="ok" style={{ marginTop: 12 }}>{okMessage}</div> : null}

      {warnings.length ? (
        <div className="card" style={{ marginTop: 12 }}>
          <h3>Avisos</h3>
          {warnings.map((warning, idx) => (
            <p className="text-muted" key={`${warning}-${idx}`}>
              - {warning}
            </p>
          ))}
        </div>
      ) : null}
    </AppShell>
  );
}

