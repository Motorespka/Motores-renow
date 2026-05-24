#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Critérios de qualidade / certificação — alinhados à view motores_certificados."""

from __future__ import annotations

import json
import re
from typing import Any, Optional

from app.search_lib import parse_awg_number, parse_mm, parse_scalar

MSG_CALCULO_SEM_HISTORICO_OFICINA = (
    "Atenção: Dados geométricos insuficientes. Cálculo baseado apenas em física teórica "
    "(sem histórico de oficina)."
)

_RE_CV_FRAC = re.compile(
    r"^(\d+(?:[.,]\d+)?)\s*/\s*(\d+(?:[.,]\d+)?)",
    re.IGNORECASE,
)


def _json_list_nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, list):
        return any(str(x).strip() for x in value)
    if isinstance(value, str):
        s = value.strip()
        if not s or s in ("[]", "null"):
            return False
        try:
            parsed = json.loads(s)
            if isinstance(parsed, list):
                return any(str(x).strip() for x in parsed)
        except json.JSONDecodeError:
            pass
        return bool(s)
    return False


def parse_cv_display(raw: Any) -> str:
    if raw is None:
        return ""
    return str(raw).strip()


def parse_cv_numeric(raw: Any) -> Optional[float]:
    s = parse_cv_display(raw).lower().replace(",", ".")
    if not s:
        return None
    m = _RE_CV_FRAC.match(s)
    if m:
        den = float(m.group(2))
        if den > 0:
            return round(float(m.group(1)) / den, 4)
    m2 = re.search(r"(\d+(?:\.\d+)?)\s*cv", s)
    if m2:
        return float(m2.group(1))
    nums = re.findall(r"\d+(?:\.\d+)?", s)
    if nums:
        v = float(nums[0])
        return v if v <= 500 else None
    return None


def avaliar_qualidade_motor(row: dict[str, Any]) -> dict[str, Any]:
    """
    Retorna flags de qualidade para uma linha da tabela motores (ou payload equivalente).
    """
    diam = parse_mm(str(row.get("diametro_mm") or row.get("diametro") or ""))
    pac = parse_mm(str(row.get("pacote_mm") or row.get("pacote") or ""))
    ran = parse_scalar(str(row.get("ranhuras") or ""))
    if ran is None:
        m = re.search(r"\d+", str(row.get("ranhuras") or ""))
        ran = float(m.group()) if m else None

    fio_ok = _json_list_nonempty(row.get("fio"))
    if not fio_ok:
        fio_ok = bool(parse_awg_number(str(row.get("fio_principal") or row.get("fio_engenheiro") or "")))

    esp_ok = _json_list_nonempty(row.get("espiras"))
    if not esp_ok:
        esp_ok = bool(
            parse_scalar(str(row.get("espiras_principal") or row.get("espiras_engenheiro") or ""))
        )

    flags = {
        "tem_diametro": diam is not None and diam > 0,
        "tem_pacote": pac is not None and pac > 0,
        "tem_ranhuras": ran is not None and ran > 0,
        "tem_fio": fio_ok,
        "tem_espiras": esp_ok,
    }
    flags["certificado"] = all(flags.values())
    return {
        "id": row.get("id") or row.get("Id") or "",
        "carcaca": str(row.get("carcaca") or row.get("Carcaca") or "").strip(),
        "cv": parse_cv_display(row.get("potencia") or row.get("potencia_cv") or row.get("cv")),
        "polos": str(row.get("polos") or row.get("Polos") or "").strip(),
        **flags,
    }


def entrada_pode_usar_historico_oficina(entrada: Optional[dict[str, Any]]) -> bool:
    """Mesmos critérios da view motores_certificados aplicados ao formulário de cálculo."""
    if not entrada:
        return False
    return bool(avaliar_qualidade_motor(entrada).get("certificado"))


def resumo_lacunas(rows: list[dict[str, Any]]) -> dict[str, int]:
    """Conta quantos registros faltam cada campo (não certificados)."""
    lacunas = {
        "diametro": 0,
        "pacote": 0,
        "ranhuras": 0,
        "fio": 0,
        "espiras": 0,
    }
    for r in rows:
        if r.get("certificado"):
            continue
        if not r.get("tem_diametro"):
            lacunas["diametro"] += 1
        if not r.get("tem_pacote"):
            lacunas["pacote"] += 1
        if not r.get("tem_ranhuras"):
            lacunas["ranhuras"] += 1
        if not r.get("tem_fio"):
            lacunas["fio"] += 1
        if not r.get("tem_espiras"):
            lacunas["espiras"] += 1
    return lacunas
