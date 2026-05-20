#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Busca hierárquica (failover) de referências no acervo OFICIAL."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from app.search_lib import (
    MotorRow,
    MatchResult,
    _geo_distance,
    find_similar,
    norm_carcaca,
    passo_canonical,
    passo_exact_match,
)
from app.topologia_bobinagem import norm_tipo_bobinagem, tipo_exact_match


class ReferenceTier(str, Enum):
    PASSO_EXATO_CARCACA = "passo_exato_carcaca"
    CARCACA_PASSO_DIFERENTE = "carcaca_similar"
    GEOMETRIA_ESTATOR = "geometria_estator"


TIER_UI_LABEL = {
    ReferenceTier.PASSO_EXATO_CARCACA: "Passo Exato",
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


def carcaca_matches(user_carcaca: str, ref_carcaca: str) -> bool:
    uk = norm_carcaca(user_carcaca)
    rk = norm_carcaca(ref_carcaca)
    if not uk:
        return True
    if not rk:
        return False
    return uk == rk or uk in rk or rk in uk


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
      a) Mesmo passo + mesma carcaça
      b) Passos diferentes + mesma carcaça
      c) Mesmo estator (Ø/pacote) + outros passos/carcaças
    """
    passo_key = passo_canonical(passo)
    modo_sobrevivencia = not bool(passo_key)
    car_key = norm_carcaca(carcaca)

    tier_a: list[MatchResult] = []
    if passo_key:
        for m in pool:
            if not stator_geometry_match(diametro_mm, pacote_mm, m):
                continue
            if car_key and not carcaca_matches(carcaca, m.carcaca):
                continue
            if not passo_exact_match(passo, m.passo_principal):
                continue
            tier_a.append(
                _score_motor(
                    m,
                    diametro_mm=diametro_mm,
                    pacote_mm=pacote_mm,
                    carcaca=carcaca,
                    passo=passo,
                    tipo_bobinagem=tipo_bobinagem,
                )
            )
        tier_a = _sort_matches(tier_a)[:top_k]
        if len(tier_a) >= min_refs:
            lbl = TIER_UI_LABEL[ReferenceTier.PASSO_EXATO_CARCACA]
            return HierarchicalSearchResult(
                tier=ReferenceTier.PASSO_EXATO_CARCACA,
                tier_label=lbl,
                calculo_baseado_em=f"Cálculo baseado em: {lbl}",
                matches=tier_a,
                modo_sobrevivencia=False,
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
            lbl = TIER_UI_LABEL[ReferenceTier.CARCACA_PASSO_DIFERENTE]
            return HierarchicalSearchResult(
                tier=ReferenceTier.CARCACA_PASSO_DIFERENTE,
                tier_label=lbl,
                calculo_baseado_em=f"Cálculo baseado em: {lbl}",
                matches=tier_b,
                modo_sobrevivencia=modo_sobrevivencia,
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
        tipo_bobinagem=tipo_bobinagem,
        topology_exact=False,
    )
    tier_c = [
        mt
        for mt in tier_c
        if stator_geometry_match(diametro_mm, pacote_mm, mt.motor)
    ]
    tier_c = _sort_matches(tier_c)
    lbl = TIER_UI_LABEL[ReferenceTier.GEOMETRIA_ESTATOR]
    if modo_sobrevivencia and tier_c:
        lbl_surv = "Modo Sobrevivência — Estimativa de Ferro"
        return HierarchicalSearchResult(
            tier=ReferenceTier.GEOMETRIA_ESTATOR,
            tier_label=lbl_surv,
            calculo_baseado_em=f"Cálculo baseado em: {lbl_surv} ({lbl})",
            matches=tier_c[:top_k],
            modo_sobrevivencia=True,
        )
    return HierarchicalSearchResult(
        tier=ReferenceTier.GEOMETRIA_ESTATOR,
        tier_label=lbl,
        calculo_baseado_em=f"Cálculo baseado em: {lbl}",
        matches=tier_c[:top_k],
        modo_sobrevivencia=modo_sobrevivencia,
    )
