#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Filtro anti-contaminação de espiras no acervo (outliers de polaridade errada)."""

from __future__ import annotations

from statistics import median
from typing import Optional

from app.search_lib import MotorRow
from engine.winding_sanity import carcaca_frame_number

OUTLIER_BAND_PCT = 0.30

# Erros de cadastro: carcaça 80–90 com espiras impossivelmente baixas
FRAME_POLLUTION_LO = 80
FRAME_POLLUTION_HI = 90
MIN_ESPIRAS_EXCLUDE_POLLUTION_80_90 = 20.0


def should_exclude_motor_row_pollution(m: MotorRow) -> bool:
    """
    Um registro de motor com espiras_principal inválidas para hierarquia
    (80–90 e <20 espiras) não deve ser visto pela busca.
    """
    if m.espiras_principal is None:
        return False
    try:
        e = float(m.espiras_principal)
    except (TypeError, ValueError):
        return False
    if e <= 0:
        return False
    return should_exclude_cadastro_pollution_80_90(m.carcaca, e)


def should_exclude_cadastro_pollution_80_90(carcaca: str, espiras: float) -> bool:
    """
    Exclui registros de carcaça 80–90 com menos de 20 espiras
    (poluição / erro de cadastro — não entram na bússola).
    """
    fn = carcaca_frame_number(carcaca)
    if fn is None or espiras <= 0:
        return False
    if FRAME_POLLUTION_LO <= fn <= FRAME_POLLUTION_HI:
        return espiras < MIN_ESPIRAS_EXCLUDE_POLLUTION_80_90
    return False


def filter_outliers_median_band(
    values: list[float],
    *,
    band_pct: float = OUTLIER_BAND_PCT,
) -> list[float]:
    """
    Remove valores fora de [mediana ± band_pct].
    Elimina motores de 2 polos (ex.: 8 esp.) que poluem média de 4/6 polos (42+).
    """
    vals = sorted(v for v in values if v is not None and v > 0)
    if len(vals) < 2:
        return vals
    m = median(vals)
    if m <= 0:
        return vals
    lo = m * (1.0 - band_pct)
    hi = m * (1.0 + band_pct)
    return [v for v in vals if lo <= v <= hi]


def robust_historical_median(
    values: list[float],
    *,
    band_pct: float = OUTLIER_BAND_PCT,
) -> tuple[Optional[float], int, int]:
    """
    Mediana histórica após limpeza de outliers.
    Retorna (mediana_limpa, n_total, n_apos_filtro).
    """
    vals = [v for v in values if v is not None and v > 0]
    if not vals:
        return None, 0, 0
    cleaned = filter_outliers_median_band(vals, band_pct=band_pct)
    if not cleaned:
        cleaned = vals
    return round(median(cleaned), 1), len(vals), len(cleaned)
