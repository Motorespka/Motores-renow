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
