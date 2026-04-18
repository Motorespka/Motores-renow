"""
Coerção de linhas Supabase / payloads de UI para o formato esperado pela camada técnica.

Read-only: não modifica o dicionário original (cópia superficial dos blocos mutáveis usados).
"""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any, Dict


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(v).strip() for v in value if str(v).strip())
    return str(value).strip()


def coerce_supabase_motor_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Combina ``dados_tecnicos_json`` (ou equivalente) com colunas planas comuns da tabela ``motores``.

    Prioridade: JSON estruturado; colunas planas preenchem lacunas no bloco ``motor``.
    """
    raw = row.get("dados_tecnicos_json") or row.get("leitura_gemini_json")
    if isinstance(raw, str) and raw.strip().startswith("{"):
        try:
            data = json.loads(raw)
        except Exception:
            data = {}
    elif isinstance(raw, dict):
        data = deepcopy(raw)
    else:
        data = {}

    motor = dict(data.get("motor") or {})

    def fill_motor(key: str, *sources: Any) -> None:
        if _to_text(motor.get(key)):
            return
        for s in sources:
            t = _to_text(s)
            if t:
                motor[key] = t
                return

    fill_motor("marca", row.get("marca"), row.get("Marca"))
    fill_motor("modelo", row.get("modelo"), row.get("Modelo"))
    fill_motor("rpm", row.get("rpm_nominal"), row.get("rpm"), row.get("Rpm"))
    fill_motor("potencia", row.get("potencia"), row.get("potencia_hp_cv"), row.get("Potencia"))
    fill_motor("polos", row.get("polos"), row.get("Polos"))
    fill_motor("frequencia", row.get("frequencia_hz"), row.get("frequencia"), row.get("Frequencia"))
    fill_motor("tipo_motor", row.get("tipo_motor"), row.get("TipoMotor"))

    if not motor.get("tensao"):
        tv = row.get("tensao_v") or row.get("tensao") or row.get("Tensao")
        if tv is not None:
            motor["tensao"] = tv if isinstance(tv, list) else _to_text(tv)

    if not motor.get("corrente"):
        ca = row.get("corrente_nominal_a") or row.get("corrente") or row.get("Corrente")
        if ca is not None:
            motor["corrente"] = ca if isinstance(ca, list) else _to_text(ca)

    if not _to_text(motor.get("fases")):
        fz = _to_text(row.get("fases") or row.get("Fases"))
        if fz:
            motor["fases"] = fz

    data["motor"] = motor
    return data
