#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tipos de bobinagem (topologia) — categorização, filtro e fatores de correção."""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from typing import Any, Optional

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


@dataclass
class TipoInferencia:
    codigo: str
    label: str
    explicacao: str
    confianca_pct: float
    amostra: int = 0


def infer_tipo_from_referencias(
    matches: list[Any],
    *,
    motor_by_sha: Optional[dict[str, Any]] = None,
) -> Optional[TipoInferencia]:
    """
    Infere topologia a partir das referências do acervo (moda estatística).
    Usado quando o usuário não informou o tipo de bobinagem.
    """
    counts: Counter[str] = Counter()
    for mt in matches:
        motor = None
        if hasattr(mt, "motor"):
            motor = mt.motor
        elif motor_by_sha and hasattr(mt, "sha"):
            motor = motor_by_sha.get(mt.sha)
        if motor is None:
            continue
        topo = norm_tipo_bobinagem(
            getattr(motor, "tipo_bobinagem_norm", "")
            or getattr(motor, "tipo_bobinagem", "")
        )
        if topo and topo != "DESCONHECIDO":
            counts[topo] += 1

    if not counts:
        return None

    best, n_best = counts.most_common(1)[0]
    total = sum(counts.values())
    pct = round(100.0 * n_best / total, 1)
    dist_txt = ", ".join(
        f"{label_tipo(k)}: {v}" for k, v in counts.most_common(4)
    )
    explicacao = (
        f"Tipo inferido automaticamente: **{label_tipo(best)}** — "
        f"{n_best} de {total} referência(s) similares no acervo ({pct:.0f}%). "
        f"Distribuição: {dist_txt}. "
        f"Confirme na ficha do motor ou na inspeção visual da ranhura antes de bobinar."
    )
    return TipoInferencia(
        codigo=best,
        label=label_tipo(best),
        explicacao=explicacao,
        confianca_pct=pct,
        amostra=total,
    )


def usuario_informou_tipo(tipo_bobinagem: str) -> bool:
    n = norm_tipo_bobinagem(tipo_bobinagem)
    return bool(n and n != "DESCONHECIDO")


def correction_factor(ref_tipo: str, target_tipo: str) -> float:
    """Fator multiplicativo nas espiras calculadas (ref -> entrada do usuário)."""
    r = norm_tipo_bobinagem(ref_tipo)
    t = norm_tipo_bobinagem(target_tipo)
    if not r or not t or r == t or r == "DESCONHECIDO" or t == "DESCONHECIDO":
        return 1.0
    return TOPOLOGY_CORRECTION.get((r, t), DEFAULT_CROSS_TOPOLOGY_FACTOR)
