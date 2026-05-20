#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.hierarchical_search import (  # noqa: E402
    ReferenceTier,
    carcaca_matches,
    hierarchical_find_references,
)
from app.search_lib import MotorRow  # noqa: E402


def _motor(**kw) -> MotorRow:
    base = dict(
        sha=kw.get("sha", "x"),
        arquivo_rel="a.json",
        melhor_status="VERDE_SEGURO",
        carcaca=kw.get("carcaca", "80A"),
        diametro_mm=kw.get("diametro_mm", 80.0),
        pacote_mm=kw.get("pacote_mm", 70.0),
        passo_principal=kw.get("passo_principal", "1-7"),
        passo_nums_json='[1,7]',
        fio_principal=kw.get("fio_principal", "23"),
        espiras_principal=kw.get("espiras_principal", 30.0),
        fio_auxiliar="",
        espiras_auxiliar=None,
        potencia_cv="",
        polos="4",
        tipo_motor="",
        ligacao="",
        tipo_bobinagem="IMBRICADO",
        tipo_bobinagem_norm="IMBRICADO",
        is_file=1,
    )
    return MotorRow(**base)


def test_tier_a_passo_exato_carcaca():
    pool = [
        _motor(sha="1", passo_principal="1-7", carcaca="80A"),
        _motor(sha="2", passo_principal="10-12", carcaca="80A", diametro_mm=81),
    ]
    res = hierarchical_find_references(
        pool,
        diametro_mm=80,
        pacote_mm=70,
        carcaca="80A",
        passo="1:7",
        min_refs=1,
    )
    assert res.tier == ReferenceTier.PASSO_EXATO_CARCACA
    assert "Passo Exato" in res.calculo_baseado_em
    assert len(res.matches) >= 1


def test_tier_b_different_passo_same_carcaca():
    pool = [
        _motor(sha="1", passo_principal="10-12", carcaca="80A"),
    ]
    res = hierarchical_find_references(
        pool,
        diametro_mm=80,
        pacote_mm=70,
        carcaca="80A",
        passo="1:7",
        min_refs=1,
    )
    assert res.tier == ReferenceTier.CARCACA_PASSO_DIFERENTE
    assert carcaca_matches("80A", "80A")
