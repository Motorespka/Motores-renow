#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.fio_paralelo import (  # noqa: E402
    choose_wire_config,
    format_wire_suggestion,
    get_equivalent_wire,
    get_single_from_parallel,
    parallel_from_single_awg,
    parse_wire_config,
    wire_display_options,
)


def test_parse_wire_parallel():
    cfg = parse_wire_config("2x22")
    assert cfg is not None
    assert cfg.parallel_count == 2
    assert cfg.awg == 22.0


def test_format_suggestion_parallel():
    cfg = parallel_from_single_awg(19.0)
    txt = format_wire_suggestion(42, cfg)
    assert "42" in txt
    assert "2x 22" in txt
    assert "Equivalente" in txt


def test_choose_wire_prefers_catalog_parallel():
    cfg = choose_wire_config(19.0, ["2x22", "2x22", "19"], prefer_parallel=True)
    assert cfg.parallel_count == 2
    assert cfg.awg == 22.0


def test_wire_display_always_offers_parallel_for_thick():
    opts = wire_display_options(40, 19.0)
    assert opts["tem_alternativa_paralelo"]
    assert "2x 22" in opts["alternativa_paralelo"]


def test_awg_equivalence_rule_n_plus_3():
    """2×N ≡ 1×(N−3): 2×22=19, 2×20=17, 2×18=15 — nunca 2×20=14."""
    assert get_single_from_parallel(22.0, 2) == 19.0
    assert get_single_from_parallel(20.0, 2) == 17.0
    assert get_single_from_parallel(18.0, 2) == 15.0
    w19 = get_equivalent_wire(19.0, 2)
    assert w19.parallel_count == 2 and w19.awg == 22.0
    w17 = get_equivalent_wire(17.0, 2)
    assert w17.awg == 20.0
    w15 = get_equivalent_wire(15.0, 2)
    assert w15.awg == 18.0
    assert get_single_from_parallel(20.0, 2) != 14.0
