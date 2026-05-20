#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validador de engenharia via Gemini para demo-calculo (proporcional + acervo)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Optional

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from services.gemini_ocr_fallback import _extract_json  # noqa: E402


def _prompt_justificativa(payload: dict[str, Any]) -> str:
    return f"""Voce e um engenheiro eletricista especialista em rebobinagem de motores.
Os valores de ESPIRAS e FIO AWG ja foram calculados deterministicamente pelo sistema (NAO altere numeros).

FORMULA (fonte da verdade — ja aplicada):
  Espiras_Calculadas = Espiras_Historico * (Pacote_Entrada / Pacote_Historico) * (Area_Entrada / Area_Historico)
  Lei da ranhura: (Espiras * Secao_Fio) <= limite historico do passo; se espiras sobem, bitola deve cair.

ENTRADA:
{json.dumps(payload.get("entrada", {}), ensure_ascii=False, indent=2)}

SUGESTAO FINAL (fixa — apenas explique):
  Espiras: {payload.get("sugestao_espira")}
  Fio AWG: {payload.get("sugestao_fio_awg")}
  Media proporcional espiras: {payload.get("media_proporcional_espiras")}
  Media historica espiras (mesmo passo): {payload.get("media_historica_espiras")}
  Limite enchimento ranhura: {payload.get("slot_fill_limit")}
  Enchimento calculado: {payload.get("slot_fill_actual")}

REFERENCIAS (amostra):
{json.dumps(payload.get("calculos_proporcionais", [])[:3], ensure_ascii=False, indent=2)}

Responda APENAS JSON:
{{
  "justificativa_tecnica": "<2-4 frases explicando a formula e a escolha do fio pela lei da ranhura>",
  "alerta_risco": "<vazio se OK; senao alerta fisico sobre ranhura, passo ou divergencia>"
}}
"""


def justify_with_gemini(payload: dict[str, Any]) -> dict[str, Any]:
    """Gemini apenas redige justificativa — nao altera espiras nem fio."""
    from config.api_manager import get_gemini_api_manager

    mgr = get_gemini_api_manager()
    raw = mgr.call_json(_prompt_justificativa(payload))
    return {
        "justificativa_tecnica": str(raw.get("justificativa_tecnica") or "").strip(),
        "alerta_risco": str(raw.get("alerta_risco") or "").strip(),
    }


def validate_with_gemini(payload: dict[str, Any]) -> dict[str, Any]:
    """Compat: delega para justify_with_gemini (modo deterministico)."""
    return justify_with_gemini(payload)
