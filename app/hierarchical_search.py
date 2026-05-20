#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Busca hierárquica (failover) de referências no acervo OFICIAL."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
from typing import Optional

from app.search_lib import (
    MotorRow,
    MatchResult,
    _geo_distance,
    find_similar,
    motor_polos_int,
    norm_carcaca,
    passo_canonical,
    passo_exact_match,
)
from app.topologia_bobinagem import norm_tipo_bobinagem, tipo_exact_match

MIN_CARCACA_FOR_GEMINI = 3

# Sincronizar com engine/outlier_filter.should_exclude_motor_row_pollution
_POLL_FRAME_LO = 80
_POLL_FRAME_HI = 90
_POLL_MIN_ESPIRAS_PRINCIPAL = 20.0
_RE_FRAME_DIGITS = re.compile(r"(\d{2,3})")


def _frame_number_from_carcaca(carcaca: str) -> Optional[int]:
    s = (carcaca or "").strip().upper()
    if not s:
        return None
    m = _RE_FRAME_DIGITS.search(s)
    return int(m.group(1)) if m else None


def _motor_row_exclude_pollution_80_90(m: MotorRow) -> bool:
    """Motores carcaça 80–90 com menos de 20 espiras são erros típicos de cadastro."""
    fn = _frame_number_from_carcaca(m.carcaca)
    if fn is None or fn < _POLL_FRAME_LO or fn > _POLL_FRAME_HI:
        return False
    if m.espiras_principal is None:
        return False
    try:
        e = float(m.espiras_principal)
    except (TypeError, ValueError):
        return False
    if e <= 0:
        return False
    return e < _POLL_MIN_ESPIRAS_PRINCIPAL


# Estator ~Ø80×70 mm (motor típico 4P/6P): cadastros 2P com <30 espiras poluem proporção — descartados.
GEO_80X70_COMPAT_DIAM_BAND = (76.0, 86.0)
GEO_80X70_COMPAT_LAM_BAND = (62.0, 80.0)
MIN_ESPIRAS_EXCLUDE_2P_UNDER_LOW_TURNS = 30.0


def _geometry_nominal_multi_pole_compat(diameter_mm: float, pacote_mm: float) -> bool:
    return (
        GEO_80X70_COMPAT_DIAM_BAND[0] <= float(diameter_mm) <= GEO_80X70_COMPAT_DIAM_BAND[1]
        and GEO_80X70_COMPAT_LAM_BAND[0] <= float(pacote_mm) <= GEO_80X70_COMPAT_LAM_BAND[1]
    )


def _motor_row_exclude_two_pole_low_turns_80_geom(
    m: MotorRow,
    *,
    apply_filter: bool,
) -> bool:
    if not apply_filter:
        return False
    p = motor_polos_int(m.polos)
    if p != 2:
        return False
    if m.espiras_principal is None:
        return False
    try:
        e = float(m.espiras_principal)
    except (TypeError, ValueError):
        return False
    if e <= 0:
        return False
    return e < MIN_ESPIRAS_EXCLUDE_2P_UNDER_LOW_TURNS


MSG_ESTIMATIVA_CARCACA = (
    "Referência exata não encontrada. Sugestão baseada em motores similares "
    "da mesma carcaça (confiança: média)."
)
MSG_ESTIMATIVA_GEOMETRIA = (
    "Referência exata não encontrada. Sugestão baseada em geometria de estator "
    "similar (confiança: média)."
)


class ReferenceTier(str, Enum):
    PASSO_EXATO_CARCACA = "passo_exato_carcaca"
    PASSO_EXATO_CARCACA_SEM_TOPO = "passo_exato_sem_topo"
    CARCACA_PASSO_DIFERENTE = "carcaca_similar"
    GEOMETRIA_ESTATOR = "geometria_estator"


TIER_UI_LABEL = {
    ReferenceTier.PASSO_EXATO_CARCACA: "Passo Exato",
    ReferenceTier.PASSO_EXATO_CARCACA_SEM_TOPO: "Passo Exato (sem filtro de topologia)",
    ReferenceTier.CARCACA_PASSO_DIFERENTE: "Carcaça Similar",
    ReferenceTier.GEOMETRIA_ESTATOR: "Geometria de Estator",
}


@dataclass
class HierarchicalSearchResult:
    tier: ReferenceTier
    tier_label: str
    calculo_baseado_em: str
    matches: list[MatchResult]
    modo_sobrevivencia: bool
    is_estimativa: bool = False
    topologia_fallback: bool = False
    mensagem_estimativa: str = ""
    n_motores_mesma_carcaca: int = 0
    forcar_gemini: bool = False


def carcaca_matches(user_carcaca: str, ref_carcaca: str) -> bool:
    uk = norm_carcaca(user_carcaca)
    rk = norm_carcaca(ref_carcaca)
    if not uk:
        return True
    if not rk:
        return False
    return uk == rk or uk in rk or rk in uk


def count_carcaca_matches(pool: list[MotorRow], carcaca: str) -> int:
    if not norm_carcaca(carcaca):
        return 0
    return sum(1 for m in pool if carcaca_matches(carcaca, m.carcaca))


def stator_geometry_match(
    diametro_mm: float,
    pacote_mm: float,
    ref: MotorRow,
    *,
    max_geo_dist: float = 0.18,
) -> bool:
    dist = _geo_distance(
        diametro_mm,
        pacote_mm,
        ref.diametro_mm,
        ref.pacote_mm,
    )
    return dist <= max_geo_dist


def _topology_matches(m: MotorRow, tipo_bobinagem: str) -> bool:
    user_topo = norm_tipo_bobinagem(tipo_bobinagem)
    if not user_topo:
        return True
    ref_topo = norm_tipo_bobinagem(m.tipo_bobinagem_norm or m.tipo_bobinagem)
    if not ref_topo:
        return True
    return tipo_exact_match(tipo_bobinagem, ref_topo)


def _score_motor(
    m: MotorRow,
    *,
    diametro_mm: float,
    pacote_mm: float,
    carcaca: str,
    passo: str,
    tipo_bobinagem: str,
) -> MatchResult:
    dist = _geo_distance(diametro_mm, pacote_mm, m.diametro_mm, m.pacote_mm)
    score = 1.0 - min(dist, 1.0)
    if carcaca_matches(carcaca, m.carcaca):
        score += 0.35
    pk = passo_canonical(passo)
    if pk and passo_exact_match(passo, m.passo_principal):
        score += 0.45
    user_topo = norm_tipo_bobinagem(tipo_bobinagem)
    if user_topo:
        ref_topo = norm_tipo_bobinagem(m.tipo_bobinagem_norm or m.tipo_bobinagem)
        if tipo_exact_match(tipo_bobinagem, ref_topo):
            score += 0.25
    return MatchResult(motor=m, score=score, dist_mm=dist)


def _sort_matches(matches: list[MatchResult]) -> list[MatchResult]:
    return sorted(matches, key=lambda x: (-x.score, x.dist_mm, x.motor.sha))


def _collect_passo_carcaca(
    pool: list[MotorRow],
    *,
    diametro_mm: float,
    pacote_mm: float,
    carcaca: str,
    passo: str,
    tipo_bobinagem: str,
    require_topology: bool,
    top_k: int,
) -> list[MatchResult]:
    car_key = norm_carcaca(carcaca)
    passo_key = passo_canonical(passo)
    if not passo_key:
        return []
    out: list[MatchResult] = []
    for m in pool:
        if not stator_geometry_match(diametro_mm, pacote_mm, m):
            continue
        if car_key and not carcaca_matches(carcaca, m.carcaca):
            continue
        if not passo_exact_match(passo, m.passo_principal):
            continue
        if require_topology and not _topology_matches(m, tipo_bobinagem):
            continue
        out.append(
            _score_motor(
                m,
                diametro_mm=diametro_mm,
                pacote_mm=pacote_mm,
                carcaca=carcaca,
                passo=passo,
                tipo_bobinagem=tipo_bobinagem,
            )
        )
    return _sort_matches(out)[:top_k]


def _result_meta(
    pool: list[MotorRow],
    carcaca: str,
    matches: list[MatchResult],
) -> tuple[int, bool]:
    n_carc = count_carcaca_matches(pool, carcaca)
    forcar = n_carc >= MIN_CARCACA_FOR_GEMINI or len(matches) >= MIN_CARCACA_FOR_GEMINI
    return n_carc, forcar


def hierarchical_find_references(
    pool: list[MotorRow],
    *,
    diametro_mm: float,
    pacote_mm: float,
    carcaca: str,
    passo: str,
    tipo_bobinagem: str = "",
    top_k: int = 25,
    min_refs: int = 1,
) -> HierarchicalSearchResult:
    """
    Failover:
      a) Mesmo passo + mesma carcaça + mesma topologia (se informada)
      a2) Mesmo passo + mesma carcaça (sem filtro de topologia)
      b) Passos diferentes + mesma carcaça
      c) Mesmo estator (Ø/pacote)

    Registros carcaça 80–90 com <20 espiras são excluídos do pool (cadastro sujo).
    Com geometria Ø80×70 compatível com 4/6 polos típicos, motores cadastrados como 2P
    e com <30 espiras não entram na hierarquia.
    """
    pool = [m for m in pool if not _motor_row_exclude_pollution_80_90(m)]
    geom_multi = _geometry_nominal_multi_pole_compat(diametro_mm, pacote_mm)
    pool = [
        m for m in pool if not _motor_row_exclude_two_pole_low_turns_80_geom(m, apply_filter=geom_multi)
    ]
    passo_key = passo_canonical(passo)
    modo_sobrevivencia = not bool(passo_key)
    car_key = norm_carcaca(carcaca)
    user_topo = norm_tipo_bobinagem(tipo_bobinagem)

    if passo_key and car_key:
        tier_topo = _collect_passo_carcaca(
            pool,
            diametro_mm=diametro_mm,
            pacote_mm=pacote_mm,
            carcaca=carcaca,
            passo=passo,
            tipo_bobinagem=tipo_bobinagem,
            require_topology=bool(user_topo),
            top_k=top_k,
        )
        if len(tier_topo) >= min_refs:
            n_carc, forcar = _result_meta(pool, carcaca, tier_topo)
            lbl = TIER_UI_LABEL[ReferenceTier.PASSO_EXATO_CARCACA]
            return HierarchicalSearchResult(
                tier=ReferenceTier.PASSO_EXATO_CARCACA,
                tier_label=lbl,
                calculo_baseado_em=f"Cálculo baseado em: {lbl}",
                matches=tier_topo,
                modo_sobrevivencia=False,
                is_estimativa=False,
                topologia_fallback=False,
                n_motores_mesma_carcaca=n_carc,
                forcar_gemini=forcar,
            )

        tier_passo = _collect_passo_carcaca(
            pool,
            diametro_mm=diametro_mm,
            pacote_mm=pacote_mm,
            carcaca=carcaca,
            passo=passo,
            tipo_bobinagem=tipo_bobinagem,
            require_topology=False,
            top_k=top_k,
        )
        if len(tier_passo) >= min_refs:
            n_carc, forcar = _result_meta(pool, carcaca, tier_passo)
            lbl = TIER_UI_LABEL[ReferenceTier.PASSO_EXATO_CARCACA_SEM_TOPO]
            topo_note = (
                f" (topologia '{user_topo}' sem match — usando passo {passo_key} na carcaça {carcaca})"
                if user_topo
                else ""
            )
            return HierarchicalSearchResult(
                tier=ReferenceTier.PASSO_EXATO_CARCACA_SEM_TOPO,
                tier_label=lbl,
                calculo_baseado_em=f"Cálculo baseado em: {lbl}{topo_note}",
                matches=tier_passo,
                modo_sobrevivencia=False,
                is_estimativa=False,
                topologia_fallback=bool(user_topo),
                n_motores_mesma_carcaca=n_carc,
                forcar_gemini=forcar,
            )

    tier_b: list[MatchResult] = []
    if car_key:
        for m in pool:
            if not stator_geometry_match(diametro_mm, pacote_mm, m):
                continue
            if not carcaca_matches(carcaca, m.carcaca):
                continue
            if passo_key and passo_exact_match(passo, m.passo_principal):
                continue
            tier_b.append(
                _score_motor(
                    m,
                    diametro_mm=diametro_mm,
                    pacote_mm=pacote_mm,
                    carcaca=carcaca,
                    passo=passo,
                    tipo_bobinagem=tipo_bobinagem,
                )
            )
        tier_b = _sort_matches(tier_b)[:top_k]
        if len(tier_b) >= min_refs:
            n_carc, forcar = _result_meta(pool, carcaca, tier_b)
            return HierarchicalSearchResult(
                tier=ReferenceTier.CARCACA_PASSO_DIFERENTE,
                tier_label=TIER_UI_LABEL[ReferenceTier.CARCACA_PASSO_DIFERENTE],
                calculo_baseado_em=MSG_ESTIMATIVA_CARCACA,
                matches=tier_b,
                modo_sobrevivencia=modo_sobrevivencia,
                is_estimativa=True,
                topologia_fallback=True,
                mensagem_estimativa=MSG_ESTIMATIVA_CARCACA,
                n_motores_mesma_carcaca=n_carc,
                forcar_gemini=forcar,
            )

    tier_c = find_similar(
        pool,
        diametro_mm=diametro_mm,
        pacote_mm=pacote_mm,
        carcaca="",
        passo="",
        top_k=top_k,
        max_geo_dist=0.18,
        passo_exact=False,
        tipo_bobinagem="",
        topology_exact=False,
    )
    tier_c = [
        mt
        for mt in tier_c
        if stator_geometry_match(diametro_mm, pacote_mm, mt.motor)
    ]
    tier_c = _sort_matches(tier_c)
    lbl = TIER_UI_LABEL[ReferenceTier.GEOMETRIA_ESTATOR]
    n_carc, forcar = _result_meta(pool, carcaca, tier_c)
    msg_est = MSG_ESTIMATIVA_GEOMETRIA if tier_c else ""
    if modo_sobrevivencia and tier_c:
        calculo = f"Modo Sobrevivência — Estimativa de Ferro. {msg_est}"
    elif tier_c:
        calculo = msg_est or f"Cálculo baseado em: {lbl}"
    else:
        calculo = f"Cálculo baseado em: {lbl}"
    return HierarchicalSearchResult(
        tier=ReferenceTier.GEOMETRIA_ESTATOR,
        tier_label=lbl,
        calculo_baseado_em=calculo,
        matches=tier_c[:top_k],
        modo_sobrevivencia=modo_sobrevivencia,
        is_estimativa=bool(tier_c),
        topologia_fallback=True,
        mensagem_estimativa=msg_est,
        n_motores_mesma_carcaca=n_carc,
        forcar_gemini=forcar,
    )
