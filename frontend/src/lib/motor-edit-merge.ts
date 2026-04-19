import type { MotorRecord } from "@/lib/types";

function asRecord(v: unknown): Record<string, unknown> {
  return v && typeof v === "object" && !Array.isArray(v) ? (v as Record<string, unknown>) : {};
}

/**
 * Junta alterações do formulário sobre `dados_tecnicos_json` e colunas de topo,
 * para pré-visualização (holograma) e persistência.
 */
export function mergeDadosTecnicosJson(
  baseRow: Record<string, unknown>,
  motorPatch: Record<string, unknown>,
  mecanicaPatch: Record<string, unknown>,
  observacoesGerais: string,
): Record<string, unknown> {
  const prev = asRecord(baseRow.dados_tecnicos_json);
  const prevMotor = asRecord(prev.motor);
  const prevMec = asRecord(prev.mecanica);
  return {
    ...prev,
    motor: { ...prevMotor, ...motorPatch },
    mecanica: { ...prevMec, ...mecanicaPatch },
    observacoes_gerais: observacoesGerais,
  };
}

export function buildPreviewMotorRow(
  baseRow: Record<string, unknown>,
  motorPatch: Record<string, unknown>,
  mecanicaPatch: Record<string, unknown>,
  observacoesGerais: string,
): Record<string, unknown> {
  const dados = mergeDadosTecnicosJson(baseRow, motorPatch, mecanicaPatch, observacoesGerais);
  return {
    ...baseRow,
    dados_tecnicos_json: dados,
    rpm: motorPatch.rpm ?? baseRow.rpm,
    tensao: motorPatch.tensao ?? baseRow.tensao,
    corrente: motorPatch.corrente ?? baseRow.corrente,
    carcaca: mecanicaPatch.carcaca ?? baseRow.carcaca,
  };
}

export function motorItemFromForm(
  baseItem: MotorRecord,
  motorPatch: Record<string, unknown>,
): MotorRecord {
  return {
    ...baseItem,
    marca: String(motorPatch.marca ?? baseItem.marca ?? ""),
    modelo: String(motorPatch.modelo ?? baseItem.modelo ?? ""),
    potencia: String(motorPatch.potencia ?? baseItem.potencia ?? ""),
    rpm: String(motorPatch.rpm ?? baseItem.rpm ?? ""),
    tensao: String(motorPatch.tensao ?? baseItem.tensao ?? ""),
    corrente: String(motorPatch.corrente ?? baseItem.corrente ?? ""),
  };
}
