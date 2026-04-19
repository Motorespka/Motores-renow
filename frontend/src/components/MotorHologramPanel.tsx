"use client";

import { useEffect, useState } from "react";
import type { DetailedHTMLProps, HTMLAttributes } from "react";

import {
  hologramPresetLabel,
  iec132SomenteFichaMecanica,
  nema42SomenteFichaMecanica,
  nema56SomenteFichaMecanica,
  resolveHologramGlbUrl,
} from "@/lib/motor-hologram";
import type { MotorRecord } from "@/lib/types";

type ModelViewerProps = DetailedHTMLProps<HTMLAttributes<HTMLElement>, HTMLElement> & {
  src?: string;
  alt?: string;
  "camera-controls"?: boolean;
  "auto-rotate"?: boolean;
  "shadow-intensity"?: string;
  "interaction-prompt"?: string;
  "touch-action"?: string;
};

declare global {
  // eslint-disable-next-line @typescript-eslint/no-namespace
  namespace JSX {
    interface IntrinsicElements {
      "model-viewer": ModelViewerProps;
    }
  }
}

let modelViewerLoader: Promise<void> | null = null;

function ensureModelViewer(): Promise<void> {
  if (typeof window === "undefined") return Promise.resolve();
  if (customElements.get("model-viewer")) return Promise.resolve();
  if (!modelViewerLoader) {
    modelViewerLoader = new Promise((resolve, reject) => {
      const existing = document.querySelector('script[data-mr-model-viewer="1"]');
      if (existing) {
        const t = window.setInterval(() => {
          if (customElements.get("model-viewer")) {
            window.clearInterval(t);
            resolve();
          }
        }, 40);
        window.setTimeout(() => {
          window.clearInterval(t);
          resolve();
        }, 8000);
        return;
      }
      const s = document.createElement("script");
      s.type = "module";
      s.src = "https://cdn.jsdelivr.net/npm/@google/model-viewer@4.0.0/dist/model-viewer.min.js";
      s.setAttribute("data-mr-model-viewer", "1");
      s.onload = () => resolve();
      s.onerror = () => reject(new Error("Falha ao carregar model-viewer"));
      document.head.appendChild(s);
    });
  }
  return modelViewerLoader;
}

type Props = {
  raw: Record<string, unknown>;
  item: MotorRecord;
};

export function MotorHologramPanel({ raw, item }: Props) {
  const [ready, setReady] = useState(false);
  const [loadErr, setLoadErr] = useState("");

  const glbUrl = resolveHologramGlbUrl(raw);
  const presetLabel = hologramPresetLabel(raw);
  const rpm = String(item.rpm ?? "-");
  const tensao = String(item.tensao ?? "-");
  const corrente = String(item.corrente ?? "-");
  const n56 = nema56SomenteFichaMecanica(raw);
  const n42 = nema42SomenteFichaMecanica(raw);

  useEffect(() => {
    if (!glbUrl) return;
    let cancelled = false;
    ensureModelViewer()
      .then(() => {
        if (!cancelled) setReady(true);
      })
      .catch(() => {
        if (!cancelled) setLoadErr("Não foi possível carregar o visualizador 3D.");
      });
    return () => {
      cancelled = true;
    };
  }, [glbUrl]);

  if (!glbUrl) {
    return (
      <div className="premium-card p-4 border border-border/50">
        <div className="font-display text-sm tracking-wider text-foreground">Holograma 3D</div>
        <p className="text-[11px] text-muted-foreground font-tech mt-2 leading-relaxed">
          Sem malha GLB resolvida para este registo. No Streamlit, use <code className="text-primary/90">holograma_glb_url</code>{" "}
          em <code className="text-primary/90">dados_tecnicos_json.motor</code>, ou configure{" "}
          <code className="text-primary/90">NEXT_PUBLIC_HOLOGRAM_GLB_NEMA56</code>,{" "}
          <code className="text-primary/90">NEXT_PUBLIC_HOLOGRAM_GLB_NEMA42</code>,{" "}
          <code className="text-primary/90">NEXT_PUBLIC_HOLOGRAM_GLB_IEC132</code> /{" "}
          <code className="text-primary/90">NEXT_PUBLIC_HOLOGRAM_GLB_DEFAULT</code> no Vercel.
          {n56 ? (
            <>
              {" "}
              Ficha indica família <span className="text-primary/90">NEMA 56</span>; confirme URL NEMA56 ou JSON.
            </>
          ) : null}
          {n42 && !n56 ? (
            <>
              {" "}
              Ficha indica <span className="text-primary/90">NEMA 42</span> (ex.: NEMA42); confirme{" "}
              <code className="text-primary/90">NEXT_PUBLIC_HOLOGRAM_BAKED_NEMA42_GLB</code> e URL Supabase.
            </>
          ) : null}
          {iec132SomenteFichaMecanica(raw) && !n56 && !n42 ? (
            <>
              {" "}
              Ficha indica <span className="text-primary/90">IEC 132</span>; confirme{" "}
              <code className="text-primary/90">NEXT_PUBLIC_HOLOGRAM_BAKED_IEC132_GLB</code> e URL GLB.
            </>
          ) : null}
        </p>
        <div className="mt-2 text-[10px] text-muted-foreground/80 font-tech">Preset: {presetLabel}</div>
      </div>
    );
  }

  if (loadErr) {
    return (
      <div className="premium-card p-4 border border-destructive/30 bg-destructive/10 text-[12px] text-destructive">
        {loadErr}
      </div>
    );
  }

  return (
    <div className="premium-card overflow-hidden border border-cyan-500/25">
      <div className="flex items-center justify-between gap-2 px-3 py-2 border-b border-cyan-500/20 bg-muted/10">
        <div>
          <div className="font-display text-xs tracking-[0.12em] text-cyan-300/90">HOLOGRAMA 3D</div>
          <div className="text-[10px] text-muted-foreground font-tech mt-0.5">{presetLabel}</div>
        </div>
        <div className="text-[10px] text-right text-muted-foreground font-mono-tech leading-tight">
          <div>RPM {rpm}</div>
          <div>
            {tensao} V · {corrente} A
          </div>
        </div>
      </div>
      <div className="relative holo-mv-shell bg-gradient-to-b from-cyan-500/[0.07] to-background">
        {!ready ? (
          <div className="h-[240px] flex items-center justify-center text-[11px] text-muted-foreground font-tech">
            A carregar modelo…
          </div>
        ) : (
          // @ts-expect-error custom element from model-viewer
          <model-viewer
            src={glbUrl}
            alt="Holograma do motor"
            crossOrigin="anonymous"
            camera-controls
            auto-rotate
            shadow-intensity="0.85"
            interaction-prompt="none"
            touch-action="pan-y"
            style={{
              width: "100%",
              height: 240,
              background: "transparent",
              filter: "contrast(1.08) saturate(0.95) brightness(1.04) drop-shadow(0 0 14px rgba(34,211,238,0.35))",
            }}
          />
        )}
        <div
          className="pointer-events-none absolute inset-0 z-[1] opacity-[0.88] mix-blend-soft-light"
          style={{
            backgroundImage:
              "repeating-linear-gradient(0deg, transparent 0 3px, rgba(34,211,238,0.045) 3px 4px), linear-gradient(115deg, rgba(125,252,255,0.06) 0%, transparent 45%, rgba(34,211,238,0.04) 100%)",
          }}
        />
        <div className="pointer-events-none absolute inset-0 z-[2] shadow-[inset_0_0_28px_rgba(6,182,212,0.12)]" />
      </div>
      <p className="text-[9px] text-muted-foreground/85 px-3 py-2 leading-snug border-t border-border/30">
        Malha GLB com camada holográfica (scanline). Gire com o rato ou toque. Hotspots avançados chegam numa
        migração futura (paridade com Streamlit).
      </p>
    </div>
  );
}
