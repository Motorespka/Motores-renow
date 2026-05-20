#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validador magnético via Gemini — nunca altera espiras nem fio calculados."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _prompt_validacao_magnetica(payload: dict[str, Any]) -> str:
    return f"""Voce e um engenheiro eletricista especialista em rebobinagem de motores.
Sua funcao e APENAS validar se o resultado deterministico faz sentido magnetico.
NAO altere, NAO recalcule e NAO sugira novos numeros de espiras ou AWG.

FORMULA JA APLICADA (fonte da verdade):
  N_novo = N_hist * (L_novo/L_hist) * (A_novo/A_hist)
  Lei da ranhura: (Espiras * Secao_Fio) <= limite historico; se espiras sobem, bitola deve cair.

ENTRADA:
{json.dumps(payload.get("entrada", {}), ensure_ascii=False, indent=2)}

RESULTADO FIXO (valide coerencia magnetica apenas):
  Espiras: {payload.get("sugestao_espira")}
  Fio: {payload.get("sugestao_fio_texto") or payload.get("sugestao_fio_awg")}
  Media proporcional: {payload.get("media_proporcional_espiras")}
  Media historica: {payload.get("media_historica_espiras")}
  Enchimento ranhura: {payload.get("slot_fill_actual')} / limite {payload.get("slot_fill_limit")}
  Base do calculo: {payload.get("calculo_baseado_em", "")}
  Estimativa (referencia parcial): {payload.get("is_estimativa", False)}
  Interpolacao proporcional solicitada: {payload.get("interpolacao_proporcional", False)}

REFERENCIAS (amostra):
{json.dumps(payload.get("calculos_proporcionais", [])[:3], ensure_ascii=False, indent=2)}

Responda APENAS JSON:
{{
  "validacao_magnetica": "OK" ou "REVISAR",
  "comentario_validacao": "<1-3 frases: densidade de fluxo, relacao espiras/fio, ranhura>",
  "alerta_risco": "<vazio se OK; senao alerta fisico sem alterar numeros>"
}}
"""


def validate_magnetic_with_gemini(payload: dict[str, Any]) -> dict[str, Any]:
    """Gemini como validador tecnico — temperatura 0.1 no api_manager."""
    from config.api_manager import get_gemini_api_manager

    mgr = get_gemini_api_manager()
    raw = mgr.call_json(_prompt_validacao_magnetica(payload))
    status = str(raw.get("validacao_magnetica") or "OK").strip().upper()
    if status not in ("OK", "REVISAR"):
        status = "REVISAR"
    return {
        "validacao_magnetica": status,
        "comentario_validacao": str(raw.get("comentario_validacao") or "").strip(),
        "alerta_risco": str(raw.get("alerta_risco") or "").strip(),
    }


def justify_with_gemini(payload: dict[str, Any]) -> dict[str, Any]:
    """Compat: delega para validacao magnetica."""
    gem = validate_magnetic_with_gemini(payload)
    return {
        "justificativa_tecnica": gem.get("comentario_validacao", ""),
        "alerta_risco": gem.get("alerta_risco", ""),
        "validacao_magnetica": gem.get("validacao_magnetica", ""),
    }


def validate_with_gemini(payload: dict[str, Any]) -> dict[str, Any]:
    return validate_magnetic_with_gemini(payload)
