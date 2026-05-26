#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Perfis de estator reais e limites de bancada para demo / testes neuro-simbólicos.

Perfil A — Ø80×70 mm (ranhura crítica)
Perfil B — Ø120×90 mm (oficina padrão)
Perfil C — Ø160×120 mm (alta potência)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

DEFAULT_J_MAX_A_MM2 = 8.0
DEFAULT_FF_MAX = 0.75


@dataclass(frozen=True)
class StatorGeometryProfile:
    profile_id: str
    label: str
    diametro_mm: float
    pacote_mm: float
    ranhuras: int
    polos: int
    carcaca: str
    passo: str
    descricao: str
    j_max_default: float = DEFAULT_J_MAX_A_MM2
    ff_max_default: float = DEFAULT_FF_MAX
    slot_severity: str = "medio"


GEOMETRIA_PERFIS: dict[str, StatorGeometryProfile] = {
    "A": StatorGeometryProfile(
        profile_id="A",
        label="Perfil A — Restritivo (Ø80×70 mm)",
        diametro_mm=80.0,
        pacote_mm=70.0,
        ranhuras=36,
        polos=4,
        carcaca="80",
        passo="10-12",
        descricao="Área de ranhura crítica; exige limites térmicos e de ff mais severos.",
        j_max_default=7.5,
        ff_max_default=0.72,
        slot_severity="critico",
    ),
    "B": StatorGeometryProfile(
        profile_id="B",
        label="Perfil B — Médio oficina (Ø120×90 mm)",
        diametro_mm=120.0,
        pacote_mm=90.0,
        ranhuras=36,
        polos=4,
        carcaca="120",
        passo="10-12",
        descricao="Geometria típica de mercado com espaço confortável na ranhura.",
        j_max_default=8.0,
        ff_max_default=0.75,
        slot_severity="medio",
    ),
    "C": StatorGeometryProfile(
        profile_id="C",
        label="Perfil C — Alta potência (Ø160×120 mm)",
        diametro_mm=160.0,
        pacote_mm=120.0,
        ranhuras=48,
        polos=6,
        carcaca="160",
        passo="12-14",
        descricao="Grande volume de ranhura; foco em alta densidade de fluxo e J moderada.",
        j_max_default=8.5,
        ff_max_default=0.78,
        slot_severity="alto",
    ),
}


def profile_select_labels() -> dict[str, str]:
    return {pid: prof.label for pid, prof in GEOMETRIA_PERFIS.items()}


def bench_from_profile(
    profile_id: str,
    *,
    j_max_override: Optional[float] = None,
    ff_max_override: Optional[float] = None,
):
    from engine.winding_optimizer import BenchCalibration

    prof = GEOMETRIA_PERFIS.get(profile_id) or GEOMETRIA_PERFIS["A"]
    j = float(j_max_override if j_max_override is not None else prof.j_max_default)
    ff = float(ff_max_override if ff_max_override is not None else prof.ff_max_default)
    return BenchCalibration(j_max_a_mm2=j, ff_max=ff, profile_id=prof.profile_id).clamp()


def stator_from_profile(profile_id: str):
    from engine.winding_optimizer import StatorInput

    prof = GEOMETRIA_PERFIS[profile_id]
    return StatorInput(
        diametro_mm=prof.diametro_mm,
        pacote_mm=prof.pacote_mm,
        ranhuras=prof.ranhuras,
        polos=prof.polos,
        carcaca=prof.carcaca,
        passo=prof.passo,
    )


def profile_form_values(profile_id: str) -> dict[str, Any]:
    prof = GEOMETRIA_PERFIS[profile_id]
    return {
        "demo_diam": str(prof.diametro_mm),
        "demo_pac": str(prof.pacote_mm),
        "demo_ranhuras": str(prof.ranhuras),
        "demo_polos": str(prof.polos),
        "demo_carc": prof.carcaca,
        "demo_passo_principal": prof.passo,
    }
