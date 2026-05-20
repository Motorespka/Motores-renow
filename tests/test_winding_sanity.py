#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.winding_sanity import (  # noqa: E402
    CALIBRE_INVALIDO,
    awg_for_fill_with_limits,
    clamp_awg_to_safe_range,
    espiras_constante_k,
    is_awg_in_range,
)


def test_clamp_zero_awg_to_14_for_80a():
    awg, adj, msg = clamp_awg_to_safe_range(0.0, "80A")
    assert awg == 14.0
    assert adj
    assert msg


def test_awg_in_range_80a():
    assert is_awg_in_range(19, "80A")
    assert not is_awg_in_range(0, "80A")
    assert not is_awg_in_range(30, "80A")


def test_espiras_constante_k_thicker_wire_fewer_turns():
    # Referência 42 espiras @ 23 AWG; fio mais grosso (19) => mais espiras? 
    # N * A = const => N_new = N * A_ref / A_new; A_19 > A_23 => N_new < N_ref
    n = espiras_constante_k(42.0, 23.0, 19.0)
    assert n < 42.0
    assert n > 20.0


def test_fill_limits_never_below_14_awg():
    # slot_limit alto + poucas espiras costumava gerar 0 AWG
    awg, adj, _ = awg_for_fill_with_limits(19.0, 500.0, 0.75, "80A")
    assert awg >= 14.0
    assert awg <= 26.0
