#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.search_lib import (  # noqa: E402
    awg_to_mm2,
    passo_canonical,
    passo_exact_match,
    slot_fill_units,
)
from app.oficial_engine import ProportionalHit, _apply_slot_law  # noqa: E402


def test_passo_exact_match():
    assert passo_exact_match("10-12", "10 : 12")
    assert passo_exact_match("10-12", "10-12")
    assert not passo_exact_match("10-12", "1:7")
    assert passo_canonical("10-12") == "10-12"


def test_slot_law_thins_wire_when_espiras_rise():
    hits = [
        ProportionalHit(
            sha="a",
            arquivo_rel="x",
            score=1.0,
            diametro_mm=80,
            pacote_mm=70,
            carcaca="80A",
            passo_principal="10-12",
            ligacao="",
            fio_principal="23",
            espiras_historico=30.0,
            espiras_calculadas=36.0,
            fio_sugerido_awg=23.0,
        ),
    ]
    fio, logs, limite, actual = _apply_slot_law(hits, esp_sug=36.0, fio_base=23.0)
    assert fio is not None
    assert fio >= 23.0
    assert limite is not None
    assert actual is not None
    assert actual <= limite * 1.03
    assert any("ranhura" in x.lower() for x in logs)


def test_awg_area_monotonic():
    assert awg_to_mm2(20) > awg_to_mm2(23)
