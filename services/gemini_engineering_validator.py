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


def _prompt_validacao(payload: dict[str, Any]) -> str:
    return f"""Voce e um engenheiro eletricista especialista em rebobinagem de motores.
Analise o calculo PROPORCIONAL ja aplicado (nao copie espiras do historico sem recalcular).

FORMULA OBRIGATORIA (ja usada no backend):
  Espiras_Calculadas = Espiras_Historico * (Pacote_Entrada / Pacote_Historico) * (Area_Entrada / Area_Historico)
  Area = pi * (diametro/2)^2

ENTRADA DO USUARIO:
{json.dumps(payload.get("entrada", {}), ensure_ascii=False, indent=2)}

CALCULOS PROPORCIONAIS (top similares — espiras_calculadas ja derivadas da formula):
{json.dumps(payload.get("calculos_proporcionais", []), ensure_ascii=False, indent=2)}

MEDIA PROPORCIONAL ESPIRAS (somente dos valores calculados, nao do historico): {payload.get("media_proporcional_espiras")}
DISPERSAO (coef. variacao): {payload.get("dispersao_espiras", 0)}
REFERENCIAS ESCASSAS: {payload.get("referencias_escassas", False)}
ENTRADA ENGENHEIRO — fio: {payload.get("fio_engenheiro", "")} | espiras: {payload.get("espiras_engenheiro", "")}

Responda APENAS JSON valido com estas chaves:
{{
  "sugestao_espira": <numero — baseie-se na media proporcional e ajuste se necessario por engenharia>,
  "sugestao_fio_awg": <numero AWG recomendado>,
  "justificativa_tecnica": "<texto curto explicando o calculo proporcional e a escolha>",
  "alerta_risco": "<vazio se OK, senao alerta sobre fio/espiras fora do padrao de seguranca>"
}}
"""


def validate_with_gemini(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Chama Gemini via api_manager. Retorna dict normalizado ou levanta excecao.
    """
    from config.api_manager import get_gemini_api_manager

    mgr = get_gemini_api_manager()
    prompt = _prompt_validacao(payload)
    raw = mgr.call_json(prompt)
    return _normalize_gemini_response(raw, fallback_espiras=payload.get("media_proporcional_espiras"))


def _normalize_gemini_response(raw: dict[str, Any], *, fallback_espiras: Any) -> dict[str, Any]:
    esp = raw.get("sugestao_espira")
    if esp is None:
        esp = raw.get("sugestao_espiras")
    try:
        esp_f = float(str(esp).replace(",", ".")) if esp is not None else float(fallback_espiras or 0)
    except (TypeError, ValueError):
        esp_f = float(fallback_espiras or 0)

    fio = raw.get("sugestao_fio_awg") or raw.get("sugestao_fio")
    try:
        fio_f = float(str(fio).replace(",", ".")) if fio not in (None, "") else None
    except (TypeError, ValueError):
        fio_f = None

    return {
        "sugestao_espira": round(esp_f, 1),
        "sugestao_fio_awg": fio_f,
        "justificativa_tecnica": str(raw.get("justificativa_tecnica") or "").strip(),
        "alerta_risco": str(raw.get("alerta_risco") or "").strip(),
    }
