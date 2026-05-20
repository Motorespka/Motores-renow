#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Filtros de sanidade para bitola AWG e espiras (constante K de fluxo)."""

from __future__ import annotations

import re
from typing import Optional

from app.search_lib import awg_to_mm2

MSG_AJUSTE_LIMITE = "Cálculo de bitola ajustado para limite seguro da carcaça."
CALIBRE_INVALIDO = "CALIBRE INVÁLIDO"

# Carcaças NEMA/IEC até 100: fio entre 14 AWG (mais grosso) e 26 AWG (mais fino)
AWG_THICK_MAX_FRAME_100 = 14.0
AWG_THIN_MIN_FRAME_100 = 26.0
CARCACA_FRAME_LIMIT = 100


def carcaca_frame_number(carcaca: str) -> Optional[int]:
    """Extrai número da carcaça (ex.: '80A' -> 80, '100' -> 100)."""
    s = (carcaca or "").strip().upper()
    if not s:
        return None
    m = re.search(r"(\d{2,3})", s)
    if not m:
        return None
    return int(m.group(1))


def awg_limits_for_carcaca(carcaca: str) -> tuple[float, float]:
    """
    Retorna (awg_min, awg_max) onde awg_min é o fio mais grosso permitido (14)
    e awg_max o mais fino (26) para carcaças até 100.
    """
    frame = carcaca_frame_number(carcaca)
    if frame is not None and frame <= CARCACA_FRAME_LIMIT:
        return AWG_THICK_MAX_FRAME_100, AWG_THIN_MIN_FRAME_100
    return 12.0, 28.0


def is_awg_in_range(awg: float, carcaca: str) -> bool:
    if awg <= 0 or awg > 40:
        return False
    lo, hi = awg_limits_for_carcaca(carcaca)
    return lo <= awg <= hi


def clamp_awg_to_safe_range(awg: float, carcaca: str) -> tuple[float, bool, str]:
    """
    Travaila AWG no intervalo realista.
    Retorna (awg_seguro, foi_ajustado, mensagem).
    """
    lo, hi = awg_limits_for_carcaca(carcaca)
    if awg <= 0 or awg > 40:
        return lo, True, CALIBRE_INVALIDO
    if awg < lo:
        return round(lo, 1), True, MSG_AJUSTE_LIMITE
    if awg > hi:
        return round(hi, 1), True, MSG_AJUSTE_LIMITE
    return round(awg, 1), False, ""


def espiras_constante_k(
    espiras_ref: float,
    awg_ref: float,
    awg_novo: float,
) -> float:
    """
    Mantém K ∝ N × seção do fio: ao mudar a bitola, recalcula espiras
    para preservar o fluxo magnético em relação à referência proporcional.
    """
    if espiras_ref <= 0:
        return espiras_ref
    a_ref = awg_to_mm2(awg_ref)
    a_novo = awg_to_mm2(awg_novo)
    if a_ref <= 0 or a_novo <= 0:
        return round(espiras_ref, 1)
    return round(espiras_ref * (a_ref / a_novo), 1)


def awg_for_fill_with_limits(
    espiras: float,
    slot_limit: float,
    occupation: float,
    carcaca: str,
) -> tuple[float, bool, str]:
    """Bitola alvo por ocupação de ranhura, já limitada ao intervalo da carcaça."""
    from app.search_lib import awg_from_mm2

    if espiras <= 0 or slot_limit <= 0:
        awg, adj, msg = clamp_awg_to_safe_range(23.0, carcaca)
        return awg, adj, msg
    area = (occupation * slot_limit) / espiras
    raw = awg_from_mm2(max(area, 1e-9))
    if raw is None:
        return clamp_awg_to_safe_range(23.0, carcaca)
    return clamp_awg_to_safe_range(raw, carcaca)
