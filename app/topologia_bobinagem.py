#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tipos de bobinagem (topologia) — categorização, filtro e fatores de correção."""

from __future__ import annotations

import re
import unicodedata
from typing import Optional

# Códigos internos (norm) -> rótulo PT para UI
TIPOS_BOBINAGEM: dict[str, str] = {
    "IMBRICADO": "Imbricado",
    "TRES_E_TRES": "3 e 3",
    "CONCENTRICO": "Concêntrico",
    "DUPLO": "Dupla camada",
    "CAMPANULA": "Campânula",
    "DESCONHECIDO": "Desconhecido",
}

# Ordem preferida no select da UI
TIPOS_UI_ORDER = ["IMBRICADO", "TRES_E_TRES", "CONCENTRICO", "DUPLO", "CAMPANULA", "DESCONHECIDO"]

# Fator aplicado às espiras proporcionais quando a referência é de outro tipo (fluxo distinto)
TOPOLOGY_CORRECTION: dict[tuple[str, str], float] = {
    ("IMBRICADO", "TRES_E_TRES"): 0.94,
    ("TRES_E_TRES", "IMBRICADO"): 0.94,
    ("IMBRICADO", "CONCENTRICO"): 0.92,
    ("CONCENTRICO", "IMBRICADO"): 0.92,
    ("TRES_E_TRES", "CONCENTRICO"): 0.90,
    ("CONCENTRICO", "TRES_E_TRES"): 0.90,
}

DEFAULT_CROSS_TOPOLOGY_FACTOR = 0.93


def _strip_accents(s: str) -> str:
    n = unicodedata.normalize("NFD", s)
    return "".join(c for c in n if unicodedata.category(c) != "Mn")


def norm_tipo_bobinagem(raw: str) -> str:
    """Normaliza entrada do usuário ou texto OCR para código interno."""
    if not (raw or "").strip():
        return ""
    raw_s = str(raw).strip()
    if raw_s.upper() in TIPOS_BOBINAGEM:
        return raw_s.upper()
    t = _strip_accents(raw_s.lower())
    t = re.sub(r"\s+", " ", t)
    if not t or t in {"?", "n/a", "na", "-"}:
        return ""

    # Aliases explícitos
    aliases = {
        "imbricado": "IMBRICADO",
        "imbricada": "IMBRICADO",
        "lap": "IMBRICADO",
        "lap winding": "IMBRICADO",
        "3 e 3": "TRES_E_TRES",
        "3e3": "TRES_E_TRES",
        "3 x 3": "TRES_E_TRES",
        "3x3": "TRES_E_TRES",
        "tres e tres": "TRES_E_TRES",
        "três e três": "TRES_E_TRES",
        "concentrico": "CONCENTRICO",
        "concêntrico": "CONCENTRICO",
        "concentric": "CONCENTRICO",
        "cc": "CONCENTRICO",
        "dupla camada": "DUPLO",
        "duplo": "DUPLO",
        "campanula": "CAMPANULA",
        "campânula": "CAMPANULA",
        "desconhecido": "DESCONHECIDO",
    }
    if t in aliases:
        return aliases[t]
    for k, v in aliases.items():
        if k in t:
            return v

    # Padrões no texto
    if re.search(r"\b3\s*e\s*3\b|\b3\s*x\s*3\b|\b3-3\b", t):
        return "TRES_E_TRES"
    if "imbric" in t or "sobrepost" in t:
        return "IMBRICADO"
    if "concent" in t or re.search(r"\bcc\b", t):
        return "CONCENTRICO"
    if "campanul" in t:
        return "CAMPANULA"
    if "dupl" in t and "camad" in t:
        return "DUPLO"

    # Passo estilo 1:7 / 1-7 costuma ser imbricado em fichas BR (heurística fraca)
    if re.match(r"^1\s*[:/-]\s*\d+$", t.replace(" ", "")):
        return "IMBRICADO"

    return "DESCONHECIDO"


def label_tipo(codigo: str) -> str:
    return TIPOS_BOBINAGEM.get(codigo, codigo or "—")


def tipo_exact_match(user_tipo: str, ref_tipo: str) -> bool:
    u = norm_tipo_bobinagem(user_tipo)
    r = norm_tipo_bobinagem(ref_tipo)
    if not u:
        return True
    if not r or r == "DESCONHECIDO":
        return False
    return u == r


def infer_tipo_bobinagem(
    *,
    passo_principal: str = "",
    passo_auxiliar: str = "",
    observacoes: str = "",
    texto_ocr: str = "",
    rebobinagem_sidecar: Optional[dict] = None,
    explicit: str = "",
) -> str:
    """Infere topologia a partir de campos disponíveis no acervo."""
    if explicit:
        n = norm_tipo_bobinagem(explicit)
        if n:
            return n

    reb: dict = rebobinagem_sidecar if isinstance(rebobinagem_sidecar, dict) else {}
    for key in ("tipo_bobinagem", "topologia", "tipo_enrolamento", "bobinagem_tipo"):
        v = reb.get(key) or (reb.get("_gemini_nested_principal") or {}).get(key)
        if v:
            n = norm_tipo_bobinagem(str(v))
            if n and n != "DESCONHECIDO":
                return n

    blob = " ".join(
        x
        for x in (
            passo_principal,
            passo_auxiliar,
            observacoes,
            texto_ocr,
            str(reb.get("passo_principal", "")),
        )
        if x
    )
    n = norm_tipo_bobinagem(blob)
    return n or "DESCONHECIDO"


def correction_factor(ref_tipo: str, target_tipo: str) -> float:
    """Fator multiplicativo nas espiras calculadas (ref -> entrada do usuário)."""
    r = norm_tipo_bobinagem(ref_tipo)
    t = norm_tipo_bobinagem(target_tipo)
    if not r or not t or r == t or r == "DESCONHECIDO" or t == "DESCONHECIDO":
        return 1.0
    return TOPOLOGY_CORRECTION.get((r, t), DEFAULT_CROSS_TOPOLOGY_FACTOR)
