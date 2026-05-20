#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Filtros de sanidade para bitola AWG e espiras (constante K de fluxo)."""

from __future__ import annotations

import math
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
ALERT_POLARIDADE = (
    "Aviso de Polaridade: A matemática para 2 Polos sugere poucas espiras, mas o histórico "
    "da oficina indica 40+. Verifique se o motor realmente é de 2 polos ou se a polaridade "
    "inserida está incorreta."
)
MSG_CENARIO_A_INVALIDO = "Cálculo Inválido por Inconsistência Física"
MSG_BUSSOLA_DIVERGENTE = (
    "Bússola histórica divergente: usando valores validados pelo usuário"
)
BUSOLA_USER_DIVERGENCE_PCT = 0.30
MIN_ESPIRAS_ESTATOR_80MM = 30

# --- Bloqueio de sanidade magnética (sobrepõe bússola estatística) ---
MSG_MAGNETIC_GATE_HIST_OVERRIDE = (
    "Atenção: Média histórica desconsiderada por inconsistência magnética. "
    "Aplicado padrão de referência seguro."
)
MSG_ESTIMATIVA_TECNICA_FORCADA = (
    "Este resultado foi classificado como **Estimativa Técnica Forçada**, "
    "e não como média direta do acervo (sanidade magnética ativa — confiança limitada)."
)
MSG_IA_CORRIGIDA_PADRAO_SEGURO = (
    "IA sugeriu valor fora da sanidade física; corrigido para padrão de referência seguro."
)
MSG_AJUSTE_MAGNETICO_PISO = (
    "Ajuste de sanidade física: espiras abaixo do piso magnético aceitável "
    "(2 polos, carcaça 71–90 mm) — elevado para referência de volume (~42 @ Ø80×70 mm escalada)."
)
MAGNETIC_REF_ESPIRAS = 42.0
MAGNETIC_REF_DIAM_MM = 80.0
MAGNETIC_REF_PACOTE_MM = 70.0
FRAME_MAGNETIC_GATE_LO = 71
FRAME_MAGNETIC_GATE_HI = 90
MIN_ESPIRAS_2P_FRAME_71_90 = 35

# Bias de engenharia (legado): comparativos texto; cenário A já não reprova só por média histórica
HIST_BIAS_MAX_DEVIATION = 0.20

# Mesa única de bitolas usadas pelo projetista — sem AWG «16,8»: sempre inteiro próximo aqui.
COMMERCIAL_BOBINAGEM_AWGS: tuple[int, ...] = (14, 15, 16, 17, 18, 19, 20, 21, 22)

# Limites ocupação ranhura (normalizado pelo limite histórico)
SLOT_FILL_SOFT_HIGH = 0.75  # dentro da zona alvo alta
SLOT_FILL_SOFT_LOW = 0.65  # zona alvo baixa
SLOT_FILL_HARD_HIGH = 0.80  # acima → afinar fio obrigatoriamente

# Carcaças até 100: apenas mesa comercial acima (grosso 14 ↔ fino 22)
AWG_THICK_MAX_FRAME_100 = 14.0
AWG_THIN_MIN_FRAME_100 = float(COMMERCIAL_BOBINAGEM_AWGS[-1])
CARCACA_FRAME_LIMIT = 100


def stator_volume_mm3(diameter_mm: float, pacote_mm: float) -> float:
    """Volume aproximado do cilindro útil V = π r² h (pacote axial)."""
    r = max(float(diameter_mm), 1e-6) / 2.0
    h = max(float(pacote_mm), 1e-6)
    return math.pi * (r**2) * h


def effective_frame_mm(carcaca: str, diameter_mm: float) -> Optional[int]:
    """Número de carcaça para regras de ferro (71–90) ou Ø em mm dentro da mesma banda."""
    fr = carcaca_frame_number(carcaca)
    if fr is not None:
        return fr
    d = diameter_mm
    if FRAME_MAGNETIC_GATE_LO <= d <= FRAME_MAGNETIC_GATE_HI:
        return int(round(d))
    return None


def magnetic_reference_turns_scaled(diameter_mm: float, pacote_mm: float) -> float:
    """
    Referência proporcional física ~42 espiras em Ø80 × 70 mm pacote,
    escalada pelo volume útil π r² h.
    """
    v = stator_volume_mm3(diameter_mm, pacote_mm)
    v0 = stator_volume_mm3(MAGNETIC_REF_DIAM_MM, MAGNETIC_REF_PACOTE_MM)
    if v0 <= 0:
        return round(MAGNETIC_REF_ESPIRAS, 1)
    return round(MAGNETIC_REF_ESPIRAS * (v / v0), 1)


def magnetic_gate_applies(polos: int, frame_mm: Optional[int]) -> bool:
    """Motor 2 polos entre carcaça 71 e 90: mínimos magnéticos rígidos."""
    if polos != 2 or frame_mm is None:
        return False
    return FRAME_MAGNETIC_GATE_LO <= frame_mm <= FRAME_MAGNETIC_GATE_HI


def should_override_hist_by_magnetic_gate(
    polos: int,
    frame_mm: Optional[int],
    media_hist: Optional[float],
) -> bool:
    """Histórico < 35 espiras sob 2 p em 71–90 exige sobrescrita (não usar bússola)."""
    if not magnetic_gate_applies(polos, frame_mm):
        return False
    if media_hist is None or media_hist <= 0:
        return False
    return media_hist < float(MIN_ESPIRAS_2P_FRAME_71_90)


def apply_magnetic_floor_two_pole_frame(
    espiras: float,
    *,
    polos: int,
    carcaca: str,
    diametro_mm: float,
    pacote_mm: float,
    cite_ia_correction_msg: bool,
) -> tuple[float, list[str]]:
    """
    Camada 2 genérica: corrige espiras abaixo do piso 2p (71–90) com referência de volume.
    cite_ia_correction_msg=True → mensagem explícita sobre correção da sugestão IA.
    """
    msgs: list[str] = []
    out = round(float(espiras), 4)
    fr = effective_frame_mm(carcaca, diametro_mm)
    if not magnetic_gate_applies(polos, fr) or out >= float(MIN_ESPIRAS_2P_FRAME_71_90) - 1e-6:
        return round(out, 1), msgs
    ref_vol = magnetic_reference_turns_scaled(diametro_mm, pacote_mm)
    corrected = round(
        max(ref_vol, float(MIN_ESPIRAS_2P_FRAME_71_90), out),
        1,
    )
    if corrected > out + 0.05:
        if cite_ia_correction_msg:
            msgs.append(MSG_IA_CORRIGIDA_PADRAO_SEGURO)
        else:
            msgs.append(MSG_AJUSTE_MAGNETICO_PISO)
        return corrected, msgs
    return round(out, 1), msgs


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
    Retorna (awg_min, awg_max) dentro da mesa comercial bobinável (14…22).
    """
    frame = carcaca_frame_number(carcaca)
    if frame is not None and frame <= CARCACA_FRAME_LIMIT:
        return AWG_THICK_MAX_FRAME_100, AWG_THIN_MIN_FRAME_100
    return AWG_THICK_MAX_FRAME_100, AWG_THIN_MIN_FRAME_100


def is_awg_in_range(awg: float, carcaca: str) -> bool:
    if awg <= 0 or awg > 40:
        return False
    lo, hi = awg_limits_for_carcaca(carcaca)
    return lo <= awg <= hi


def clamp_awg_to_safe_range(awg: float, carcaca: str) -> tuple[float, bool, str]:
    """
    Travaila AWG na mesa 14–22 (carcaças típicas).
    Retorna (awg_seguro, foi_ajustado, mensagem).
    """
    lo, hi = awg_limits_for_carcaca(carcaca)
    if awg <= 0 or awg > 40:
        return float(nearest_awg_from_table(lo)), True, CALIBRE_INVALIDO
    if awg < lo:
        return float(nearest_awg_from_table(lo)), True, MSG_AJUSTE_LIMITE
    if awg > hi:
        return float(nearest_awg_from_table(hi)), True, MSG_AJUSTE_LIMITE
    snap = float(nearest_awg_from_table(awg))
    return snap, abs(snap - round(awg, 4)) >= 0.05, ""


def espiras_busola_oficina(
    media_hist: Optional[float],
    media_prop: Optional[float],
    *,
    espiras_usuario: Optional[float] = None,
) -> float:
    """
    Referência de espiras (legado compat).
    Com validação do usuário: 100% o valor informado.
    Sem validação: **projetista proporcional primeiro** — cálculo do motor proporcional ao ferro,
    não a mediana histórica do acervo como bússola.
    """
    if espiras_usuario is not None and espiras_usuario > 0:
        return round(float(espiras_usuario), 1)
    if media_prop and media_prop > 0:
        return round(float(media_prop), 1)
    if media_hist and media_hist > 0:
        return round(float(media_hist), 1)
    return 0.0


def busola_historica_inconsistente(
    espiras_usuario: float,
    media_hist: Optional[float],
    *,
    threshold: float = BUSOLA_USER_DIVERGENCE_PCT,
) -> bool:
    """Histórico diverge >30% do valor validado pelo usuário."""
    if not media_hist or media_hist <= 0 or espiras_usuario <= 0:
        return False
    return abs(espiras_usuario - media_hist) / media_hist > threshold


def exceeds_hist_bias(
    espiras: float,
    media_hist: Optional[float],
    max_deviation: float = HIST_BIAS_MAX_DEVIATION,
) -> bool:
    if not media_hist or media_hist <= 0 or espiras <= 0:
        return False
    return abs(espiras - media_hist) / media_hist > max_deviation


def nearest_awg_from_table(awg_raw: float) -> int:
    """AWG inteiro mais próximo na mesa fixa 14–22 (ex.: 16,8 → 17)."""
    if not COMMERCIAL_BOBINAGEM_AWGS:
        return max(14, min(22, int(round(awg_raw))))
    clamped = max(float(COMMERCIAL_BOBINAGEM_AWGS[0]), min(float(COMMERCIAL_BOBINAGEM_AWGS[-1]), float(awg_raw)))
    return min(COMMERCIAL_BOBINAGEM_AWGS, key=lambda z: abs(float(z) - clamped))


def awg_table_index(awg: float) -> int:
    wi = nearest_awg_from_table(awg)
    return COMMERCIAL_BOBINAGEM_AWGS.index(wi)


def round_commercial_awg(awg: float) -> int:
    """Compat: usa mesa 14–22."""
    return nearest_awg_from_table(awg)


def apply_commercial_awg_preserve_copper(
    espiras: float,
    awg_raw: float,
    carcaca: str,
) -> tuple[float, float, bool, str]:
    """
    Arredonda bitola e recalcula espiras mantendo N×seção (volume de cobre).
    Retorna (espiras, awg_comercial, foi_ajustado, mensagem).
    """
    awg_comm = float(nearest_awg_from_table(awg_raw))
    awg_safe, adj_lim, msg_lim = clamp_awg_to_safe_range(awg_comm, carcaca)
    esp_vol = espiras_constante_k(espiras, awg_raw, awg_safe)
    msgs: list[str] = []
    if abs(awg_safe - awg_raw) >= 0.05:
        msgs.append(MSG_AWG_COMERCIAL)
    if adj_lim and msg_lim and msg_lim != CALIBRE_INVALIDO:
        msgs.append(msg_lim)
    return esp_vol, awg_safe, bool(msgs), " ".join(msgs)


def polarity_sanity_alert(
    polos: int,
    espiras_sugeridas: float,
    media_hist: Optional[float],
    carcaca: str = "",
) -> bool:
    if polos != 2:
        return False
    if not media_hist or media_hist < 35:
        return False
    return espiras_sugeridas < 20


def force_busola_if_underturn(
    espiras: float,
    media_hist: Optional[float],
    *,
    diametro_mm: float = 0,
    carcaca: str = "",
) -> tuple[float, bool]:
    """Compatível: projeto não corrige mais espiras apenas por mediana do acervo."""
    return round(espiras, 1), False


def scenario_a_is_acceptable(
    espiras_a: float,
    fill_ratio: float,
    *,
    max_fill: float = max(SLOT_FILL_HARD_HIGH + 0.06, 0.88),
    _ignored_media_hist: Optional[float] = None,
    _ignored_max_deviation: Optional[float] = None,
) -> bool:
    """
    Cenário A: apenas sanidade física de ranhura (não reprova só por média histórica).
    """
    return fill_ratio <= max_fill + 1e-9


MSG_AVISO_DESVIO_HIST = (
    "Comparativo: desvio forte em relação à mediana histórica do passo/carcaça — "
    "revisar projeto no motor real; valores mantidos pela projeção proporcional."
)


def proportional_vs_hist_alert(
    espiras_ref: float,
    media_hist: Optional[float],
    *,
    threshold: float = 0.25,
) -> Optional[str]:
    """Apenas aviso textual; não altera espiras."""
    if not media_hist or media_hist <= 0 or espiras_ref <= 0:
        return None
    if abs(espiras_ref - media_hist) / media_hist >= threshold:
        return MSG_AVISO_DESVIO_HIST
    return None


def tune_slot_occupation_band(
    espiras: float,
    awg: float,
    slot_limit: float,
    *,
    hard_high: float = SLOT_FILL_HARD_HIGH,
    soft_high: float = SLOT_FILL_SOFT_HIGH,
    soft_low: float = SLOT_FILL_SOFT_LOW,
) -> tuple[float, float, list[str]]:
    """
    Se ocupação (fill/limit) >80 %, afina AWG na mesa e recalcula espiras (N×A constante)
    até aproximar a faixa 65–75 % quando possível.
    """
    from app.search_lib import slot_fill_units

    msgs: list[str] = []
    lim = float(slot_limit)
    if lim <= 0:
        return round(float(espiras), 1), float(nearest_awg_from_table(float(awg))), msgs

    a = float(nearest_awg_from_table(float(awg)))
    e = round(float(espiras), 4)
    e = round(espiras_constante_k(e, awg, a), 1)

    def _ratio(ee: float, aa: float) -> float:
        if lim <= 0 or ee <= 0 or aa <= 0:
            return 0.0
        return slot_fill_units(ee, aa) / lim

    bumped_hard = False
    for _ in range(18):
        r = _ratio(e, a)
        if soft_low <= r <= soft_high:
            break
        idx = awg_table_index(a)
        if r > hard_high:
            bumped_hard = True
            if idx >= len(COMMERCIAL_BOBINAGEM_AWGS) - 1:
                msgs.append(
                    "Ocupação de ranhura elevada (>80 %) mesmo em AWG 22 — revise ranhura/passo ou espiras-base."
                )
                break
            new_a = float(COMMERCIAL_BOBINAGEM_AWGS[idx + 1])
            e = round(espiras_constante_k(e, a, new_a), 1)
            a = new_a
            continue
        if r > soft_high:
            if idx >= len(COMMERCIAL_BOBINAGEM_AWGS) - 1:
                break
            new_a = float(COMMERCIAL_BOBINAGEM_AWGS[idx + 1])
            e_n = round(espiras_constante_k(e, a, new_a), 1)
            e, a = e_n, new_a
            continue
        if r > 0 and r < soft_low:
            if idx <= 0:
                break
            new_a = float(COMMERCIAL_BOBINAGEM_AWGS[idx - 1])
            e_n = round(espiras_constante_k(e, a, new_a), 1)
            e, a = e_n, new_a
            continue
        break

    rf = _ratio(e, a)
    if bumped_hard or rf > soft_high:
        msgs.append(
            "Ocupação de ranhura ajustada: bitola refinada quando >80 %; "
            "espiras recalculadas com volume de cobre constante (N×A)."
        )
    elif rf < soft_low and rf > 0:
        msgs.append("Ocupação baixa (<65 %): espiras/bitola reposicionadas na mesa comercial.")

    return round(e, 1), a, msgs


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
    """Bitola alvo por ocupação de ranhura, projetada pela mesa 14–22."""
    from app.search_lib import awg_from_mm2

    if espiras <= 0 or slot_limit <= 0:
        awg, adj, msg = clamp_awg_to_safe_range(23.0, carcaca)
        return float(nearest_awg_from_table(awg)), adj, msg
    area = (occupation * slot_limit) / espiras
    raw = awg_from_mm2(max(area, 1e-9))
    if raw is None:
        awg, adj, msg = clamp_awg_to_safe_range(23.0, carcaca)
        return float(nearest_awg_from_table(awg)), adj, msg
    awg, adj, msg = clamp_awg_to_safe_range(raw, carcaca)
    snapped = float(nearest_awg_from_table(awg))
    adj = adj or abs(snapped - round(float(raw), 4)) >= 0.05
    return snapped, adj, msg
