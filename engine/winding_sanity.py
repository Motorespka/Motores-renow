#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Filtros de sanidade para bitola AWG e espiras (constante K de fluxo)."""

from __future__ import annotations

import re
from typing import Optional

from app.search_lib import awg_to_mm2

MSG_AJUSTE_LIMITE = "Cálculo de bitola ajustado para limite seguro da carcaça."
CALIBRE_INVALIDO = "CALIBRE INVÁLIDO"
MSG_CENARIO_A_TRAVADO = (
    "Cenário A travado: desvio superior a 20% da média histórica. "
    "Use o Cenário B (média de referência da oficina)."
)
MSG_AWG_COMERCIAL = "Bitola arredondada para calibre comercial AWG; espiras recalculadas (volume de cobre)."
ALERT_ESPIRAS_BAIXAS = (
    "Aviso: Número de espiras baixo. Verifique se o cálculo considerou a polaridade correta."
)

# Bias de engenharia: Cenário A não pode desviar mais que isto da média histórica
HIST_BIAS_MAX_DEVIATION = 0.20
PESO_MEDIA_HISTORICA_BUSOLA = 0.85

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


def espiras_busola_oficina(
    media_hist: Optional[float],
    media_prop: Optional[float],
    *,
    peso_hist: float = PESO_MEDIA_HISTORICA_BUSOLA,
) -> float:
    """Bússola principal: prioriza média histórica do passo (ex.: 42–45 espiras)."""
    if media_hist and media_hist > 0 and media_prop and media_prop > 0:
        return round(peso_hist * float(media_hist) + (1.0 - peso_hist) * float(media_prop), 1)
    if media_hist and media_hist > 0:
        return round(float(media_hist), 1)
    return round(float(media_prop or 0), 1)


def exceeds_hist_bias(
    espiras: float,
    media_hist: Optional[float],
    max_deviation: float = HIST_BIAS_MAX_DEVIATION,
) -> bool:
    if not media_hist or media_hist <= 0 or espiras <= 0:
        return False
    return abs(espiras - media_hist) / media_hist > max_deviation


def round_commercial_awg(awg: float) -> int:
    """Arredonda para AWG comercial inteiro (ex.: 16.8 → 17)."""
    return int(round(max(1.0, min(40.0, awg))))


def apply_commercial_awg_preserve_copper(
    espiras: float,
    awg_raw: float,
    carcaca: str,
) -> tuple[float, float, bool, str]:
    """
    Arredonda bitola e recalcula espiras mantendo N×seção (volume de cobre).
    Retorna (espiras, awg_comercial, foi_ajustado, mensagem).
    """
    awg_comm = float(round_commercial_awg(awg_raw))
    awg_safe, adj_lim, msg_lim = clamp_awg_to_safe_range(awg_comm, carcaca)
    esp_vol = espiras_constante_k(espiras, awg_raw, awg_safe)
    msgs: list[str] = []
    if abs(awg_safe - awg_raw) >= 0.05:
        msgs.append(MSG_AWG_COMERCIAL)
    if adj_lim and msg_lim and msg_lim != CALIBRE_INVALIDO:
        msgs.append(msg_lim)
    return esp_vol, awg_safe, bool(msgs), " ".join(msgs)


def should_alert_low_turns(
    espiras: float,
    media_hist: Optional[float],
    *,
    polos: int = 0,
    ranhuras: int = 0,
) -> bool:
    if espiras <= 0:
        return False
    if media_hist and media_hist > 0 and espiras < media_hist * 0.55:
        return True
    if espiras < 22:
        return True
    if polos == 2 and ranhuras >= 36 and espiras < 32:
        return True
    return False


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
