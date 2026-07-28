"use client";

import type { ReactNode } from "react";

import { normalizeMotorRowForUi } from "@/lib/motor-normalizer";

function pick(row: Record<string, unknown>, ...keys: string[]): string {
  for (const k of keys) {
    const v = row[k];
    if (v == null) continue;
    const s = String(v).trim();
    if (s && s !== "-" && s.toLowerCase() !== "null") return s;
  }
  return "";
}

function Field({ label, value, hint }: { label: string; value?: string; hint?: string }) {
  const display = value && value.trim() ? value.trim() : "—";
  const empty = display === "—";
  return (
    <div className="rounded-xl border border-border/40 bg-muted/15 px-3 py-2.5 min-h-[64px]">
      <div className="text-[10px] font-tech tracking-[0.14em] uppercase text-muted-foreground/90">{label}</div>
      <div
        className={`mt-1 text-sm font-display tracking-wide ${empty ? "text-muted-foreground/55" : "text-foreground"}`}
      >
        {display}
      </div>
      {hint ? <div className="mt-0.5 text-[10px] text-muted-foreground/70 font-tech">{hint}</div> : null}
    </div>
  );
}

function Section({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children: ReactNode;
}) {
  return (
    <section className="premium-card p-4 sm:p-5">
      <div className="border-b border-border/35 pb-3 mb-4">
        <h3 className="font-display text-sm font-bold tracking-[0.14em] text-foreground">{title}</h3>
        {subtitle ? <p className="mt-1 text-[11px] text-muted-foreground font-tech leading-relaxed">{subtitle}</p> : null}
      </div>
      {children}
    </section>
  );
}

type Props = {
  raw: Record<string, unknown>;
};

/** Ficha de bancada — linguagem de oficina, sem dump JSON. */
export function MotorFichaOficina({ raw }: Props) {
  const ui = normalizeMotorRowForUi(raw);
  const marca = pick(raw, "marca", "Marca");
  const modelo = pick(raw, "modelo", "Modelo");
  const fabricante = pick(raw, "fabricante", "Fabricante") || marca;
  const numSerie = pick(raw, "num_serie", "numero_serie", "NumeroSerie", "n_serie");
  const potencia = ui.potencia || pick(raw, "potencia", "Potencia");
  const rpm = ui.rpm || pick(raw, "rpm", "Rpm", "RPM");
  const tensao = ui.tensao || pick(raw, "tensao", "Tensao");
  const corrente = ui.corrente || pick(raw, "corrente", "Corrente");
  const polos = ui.polos || pick(raw, "polos", "Polos");
  const frequencia = ui.frequencia || pick(raw, "frequencia", "Frequencia") || "60";
  const carcaca = ui.carcaca || pick(raw, "carcaca", "Carcaca");
  const norma = pick(raw, "norma", "Norma");
  const isolacao = pick(raw, "isolacao", "Isolacao", "classe_isolacao");
  const ip = pick(raw, "ip", "IP", "grau_protecao");
  const regime = pick(raw, "regime", "Regime");
  const fs = pick(raw, "fator_servico", "FatorServico", "fs");
  const tipo = ui.tipo_motor || pick(raw, "tipo_motor", "TipoMotor", "fases");
  const obs = pick(raw, "observacoes", "Observacoes", "obs");
  const passoP = ui.passo_principal || pick(raw, "passo_principal", "PassoPrincipal");
  const espP = ui.espiras_principal || pick(raw, "espiras_principal", "espira_principal", "EspirasPrincipal");
  const fioP = ui.fio_principal || pick(raw, "fio_principal", "FioPrincipal");
  const ligP = ui.ligacao_principal || pick(raw, "ligacao_principal", "LigacaoPrincipal");
  const passoA = ui.passo_auxiliar || pick(raw, "passo_auxiliar", "PassoAuxiliar");
  const espA = ui.espiras_auxiliar || pick(raw, "espiras_auxiliar", "espira_auxiliar", "EspirasAuxiliar");
  const fioA = ui.fio_auxiliar || pick(raw, "fio_auxiliar", "FioAuxiliar");
  const ligA = ui.ligacao_auxiliar || pick(raw, "ligacao_auxiliar", "LigacaoAuxiliar");
  const eixo = ui.eixo || pick(raw, "eixo", "Eixo");
  const medidas = ui.medidas || pick(raw, "medidas", "Medidas");

  const syncRpm =
    rpm && polos && frequencia
      ? (() => {
          const p = Number(String(polos).replace(/[^\d.]/g, ""));
          const f = Number(String(frequencia).replace(/[^\d.]/g, "")) || 60;
          if (!p || p < 2) return "";
          const ns = Math.round((120 * f) / p);
          return `Síncrono teórico ≈ ${ns} rpm (${f} Hz / ${p} pólos)`;
        })()
      : "";

  return (
    <div className="space-y-4">
      <Section
        title="Identificação da placa"
        subtitle="Dados elétricos de identificação — o que o técnico confirma antes de abrir o motor."
      >
        <div className="grid gap-2.5 sm:grid-cols-2 lg:grid-cols-4">
          <Field label="Marca" value={marca} />
          <Field label="Modelo" value={modelo} />
          <Field label="Fabricante" value={fabricante} />
          <Field label="Nº de série" value={numSerie} />
          <Field label="Potência" value={potencia} hint="CV / kW da placa" />
          <Field label="RPM" value={rpm} hint={syncRpm || "Placa ou referência"} />
          <Field label="Tensão" value={tensao} hint="V (ex.: 220/380)" />
          <Field label="Corrente" value={corrente} hint="A por tensão" />
          <Field label="Pólos" value={polos} />
          <Field label="Frequência" value={frequencia ? `${frequencia} Hz` : ""} />
          <Field label="Tipo / fases" value={tipo} />
          <Field label="Carcaça" value={carcaca} hint="IEC / NEMA" />
        </div>
      </Section>

      <Section
        title="Rebobinagem"
        subtitle="Receita de enrolamento para a bancada — principal e auxiliar (quando existir)."
      >
        <div className="grid gap-4 lg:grid-cols-2">
          <div>
            <p className="mb-2 text-[10px] font-tech tracking-[0.16em] text-primary/80">ENROLAMENTO PRINCIPAL</p>
            <div className="grid gap-2.5 sm:grid-cols-2">
              <Field label="Passo" value={passoP} />
              <Field label="Espiras" value={espP} />
              <Field label="Bitola / fio" value={fioP} hint="AWG ou mm²" />
              <Field label="Ligação" value={ligP} hint="Y / Δ / série-paralelo" />
            </div>
          </div>
          <div>
            <p className="mb-2 text-[10px] font-tech tracking-[0.16em] text-accent/80">ENROLAMENTO AUXILIAR</p>
            <div className="grid gap-2.5 sm:grid-cols-2">
              <Field label="Passo" value={passoA} />
              <Field label="Espiras" value={espA} />
              <Field label="Bitola / fio" value={fioA} />
              <Field label="Ligação" value={ligA} />
            </div>
            {!passoA && !espA && !fioA ? (
              <p className="mt-2 text-[11px] text-muted-foreground/80 font-tech">
                Sem bobina auxiliar nesta ficha (típico trifásico).
              </p>
            ) : null}
          </div>
        </div>
      </Section>

      <Section title="Mecânica e proteção" subtitle="Carcaça, isolamento e montagem — útil para peça e laudo.">
        <div className="grid gap-2.5 sm:grid-cols-2 lg:grid-cols-4">
          <Field label="Norma" value={norma} />
          <Field label="Classe de isolação" value={isolacao} />
          <Field label="Grau IP" value={ip} />
          <Field label="Regime" value={regime} />
          <Field label="Fator de serviço" value={fs} />
          <Field label="Eixo" value={eixo} />
          <Field label="Medidas" value={medidas} />
          <Field label="Carcaça (mecânica)" value={carcaca} />
        </div>
      </Section>

      {obs ? (
        <Section title="Observações técnicas" subtitle="Notas da oficina sobre este registo.">
          <p className="text-[13px] leading-relaxed text-foreground/90 whitespace-pre-wrap">{obs}</p>
        </Section>
      ) : null}
    </div>
  );
}
