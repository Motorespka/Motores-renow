/**
 * Espelha `utils/motor_normalizer.py` para lista/detalhe Next.js (Supabase direto).
 */

export type MotorUiFields = Record<string, string>;

const A_PASSO_P = ["PassoPrincipal", "passo_principal", "PassosPrincipais", "passos_principais"] as const;
const A_PASSO_A = ["PassoAuxiliar", "passo_auxiliar", "PassosAuxiliares", "passos_auxiliares"] as const;
const A_ESP_P = ["EspirasPrincipal", "espiras_principal", "EspirasPrincipais", "espiras_principais"] as const;
const A_ESP_A = ["EspirasAuxiliar", "espiras_auxiliar", "EspirasAuxiliares", "espiras_auxiliares"] as const;
const A_FIO_P = ["FioPrincipal", "fio_principal", "FiosPrincipais", "fios_principais"] as const;
const A_FIO_A = ["FioAuxiliar", "fio_auxiliar", "FiosAuxiliares", "fios_auxiliares"] as const;
const A_LIG_P = ["LigacaoPrincipal", "ligacao_principal", "LigacoesPrincipais", "ligacoes_principais"] as const;
const A_LIG_A = ["LigacaoAuxiliar", "ligacao_auxiliar", "LigacoesAuxiliares", "ligacoes_auxiliares"] as const;
const A_EIXO_X = ["EixoX", "eixo_x"] as const;
const A_EIXO_Y = ["EixoY", "eixo_y"] as const;
const A_EIXO = ["Eixo", "eixo"] as const;
const A_MEDIDAS = ["Medidas", "medidas"] as const;
const A_POT = ["Potencia", "potencia"] as const;
const A_RPM = ["Rpm", "rpm", "RPM"] as const;
const A_TENSAO = ["Tensao", "tensao"] as const;
const A_CORR = ["Corrente", "corrente"] as const;
const A_FREQ = ["Frequencia", "frequencia"] as const;
const A_POLOS = ["Polos", "polos"] as const;
const A_TIPO = ["TipoMotor", "tipo_motor"] as const;
const A_CARCACA = ["Carcaca", "carcaca"] as const;
const A_PASSO_MULTI = ["Passo", "passo", "Passos", "passos"] as const;
const A_ESP_MULTI = ["Espiras", "espiras"] as const;
const A_FIO_MULTI = ["Fio", "fio", "Fios", "fios"] as const;
const A_LIG_MULTI = ["Ligacao", "ligacao", "Ligacoes", "ligacoes"] as const;

export function isEmpty(value: unknown): boolean {
  if (value === null || value === undefined) return true;
  if (typeof value === "string") {
    const t = value.trim();
    if (!t) return true;
    const low = t.toLowerCase();
    if (low === "-" || low === "null" || low === "none" || low === "nan") return true;
  }
  if (Array.isArray(value) && value.length === 0) return true;
  if (typeof value === "object" && !Array.isArray(value) && Object.keys(value as object).length === 0) return true;
  return false;
}

function variaveisSite(row: Record<string, unknown>): Record<string, unknown> {
  let raw = row.VariaveisSite ?? row.variaveis_site ?? row.Variaveis_site;
  if (raw && typeof raw === "object" && !Array.isArray(raw)) return raw as Record<string, unknown>;
  if (typeof raw === "string" && raw.trim().startsWith("{")) {
    try {
      const p = JSON.parse(raw) as unknown;
      return p && typeof p === "object" && !Array.isArray(p) ? (p as Record<string, unknown>) : {};
    } catch {
      return {};
    }
  }
  return {};
}

export function pickValue(row: Record<string, unknown>, aliases: readonly string[]): unknown {
  const vs = variaveisSite(row);
  for (const alias of aliases) {
    const v = row[alias];
    if (!isEmpty(v)) return v;
    if (Object.prototype.hasOwnProperty.call(vs, alias)) {
      const v2 = vs[alias];
      if (!isEmpty(v2)) return v2;
    }
  }
  return undefined;
}

export function asDisplayText(value: unknown): string {
  if (isEmpty(value)) return "";
  if (Array.isArray(value)) {
    const parts = value.map((x) => String(x).trim()).filter((x) => !isEmpty(x));
    return parts.join(", ");
  }
  if (value && typeof value === "object" && !Array.isArray(value)) {
    const o = value as Record<string, unknown>;
    const parts = Object.values(o)
      .map((v) => String(v).trim())
      .filter((v) => !isEmpty(v));
    return parts.join(", ");
  }
  return String(value).trim();
}

function itemsFromMultivalue(raw: unknown): string[] {
  if (isEmpty(raw)) return [];
  if (Array.isArray(raw)) {
    const out: string[] = [];
    for (const x of raw) {
      const s = asDisplayText(x);
      if (s) out.push(s);
    }
    return out;
  }
  if (typeof raw === "string") {
    const t = raw.trim();
    if (!t) return [];
    const parts = t.split(/\s*[,;]\s*/).filter((p) => p.trim());
    return parts.length > 1 ? parts : [t];
  }
  const s = asDisplayText(raw);
  return s ? [s] : [];
}

export function normalizeMotorRowForUi(row: Record<string, unknown> | null | undefined): MotorUiFields {
  const r = row || {};

  let passoPrincipal = asDisplayText(pickValue(r, A_PASSO_P));
  let passoAuxiliar = asDisplayText(pickValue(r, A_PASSO_A));
  let espirasPrincipal = asDisplayText(pickValue(r, A_ESP_P));
  let espirasAuxiliar = asDisplayText(pickValue(r, A_ESP_A));
  let fioPrincipal = asDisplayText(pickValue(r, A_FIO_P));
  let fioAuxiliar = asDisplayText(pickValue(r, A_FIO_A));
  let ligacaoPrincipal = asDisplayText(pickValue(r, A_LIG_P));
  let ligacaoAuxiliar = asDisplayText(pickValue(r, A_LIG_A));

  const eixoX = asDisplayText(pickValue(r, A_EIXO_X));
  const eixoY = asDisplayText(pickValue(r, A_EIXO_Y));
  let eixo = asDisplayText(pickValue(r, A_EIXO));
  let medidas = asDisplayText(pickValue(r, A_MEDIDAS));

  const potencia = asDisplayText(pickValue(r, A_POT));
  const rpm = asDisplayText(pickValue(r, A_RPM));
  const tensao = asDisplayText(pickValue(r, A_TENSAO));
  const corrente = asDisplayText(pickValue(r, A_CORR));
  const frequencia = asDisplayText(pickValue(r, A_FREQ));
  const polos = asDisplayText(pickValue(r, A_POLOS));
  const tipoMotor = asDisplayText(pickValue(r, A_TIPO));
  const carcaca = asDisplayText(pickValue(r, A_CARCACA));

  const passoItems = itemsFromMultivalue(pickValue(r, A_PASSO_MULTI));
  if (!passoPrincipal && passoItems.length) passoPrincipal = passoItems[0]!;
  if (!passoAuxiliar && passoItems.length >= 2) passoAuxiliar = passoItems[1]!;

  const espItems = itemsFromMultivalue(pickValue(r, A_ESP_MULTI));
  if (!espirasPrincipal && espItems.length) espirasPrincipal = espItems[0]!;
  if (!espirasAuxiliar && espItems.length >= 2) espirasAuxiliar = espItems[1]!;

  const fioItems = itemsFromMultivalue(pickValue(r, A_FIO_MULTI));
  if (!fioPrincipal && fioItems.length) fioPrincipal = fioItems[0]!;
  if (!fioAuxiliar && fioItems.length >= 2) fioAuxiliar = fioItems[1]!;

  const ligItems = itemsFromMultivalue(pickValue(r, A_LIG_MULTI));
  if (!ligacaoPrincipal && ligItems.length) ligacaoPrincipal = ligItems[0]!;
  if (!ligacaoAuxiliar && ligItems.length >= 2) ligacaoAuxiliar = ligItems[1]!;

  if (!eixo && (eixoX || eixoY)) {
    eixo = `X:${eixoX || "-"} | Y:${eixoY || "-"}`;
  }
  if (!medidas && (eixoX || eixoY)) {
    medidas = eixoX && eixoY ? `${eixoX} x ${eixoY}` : eixoX || eixoY;
  }

  return {
    passo_principal: passoPrincipal,
    passo_auxiliar: passoAuxiliar,
    espiras_principal: espirasPrincipal,
    espiras_auxiliar: espirasAuxiliar,
    fio_principal: fioPrincipal,
    fio_auxiliar: fioAuxiliar,
    ligacao_principal: ligacaoPrincipal,
    ligacao_auxiliar: ligacaoAuxiliar,
    eixo_x: eixoX,
    eixo_y: eixoY,
    eixo,
    medidas,
    potencia,
    rpm,
    tensao,
    corrente,
    frequencia,
    polos,
    tipo_motor: tipoMotor,
    carcaca,
  };
}
