"""Testes para equivalencias de oficina (fio, espiras, tensao)."""

from __future__ import annotations

import math

from services.motor_rebobinagem.wire_gauge import awg_integer_to_mm2
from services.oficina_rebobinagem_equiv import (
    area_total_mm2,
    equivalent_num_parallel,
    parallel_branch_current_split,
    series_total_turns,
    suggest_awg_combos_for_area,
    turns_for_voltage_ratio,
)


def test_area_total_mm2_one_awg19() -> None:
    a19 = awg_integer_to_mm2(19)
    assert a19 is not None
    tot = area_total_mm2(1, 19)
    assert tot is not None
    assert math.isclose(tot, a19, rel_tol=1e-9)


def test_equivalent_num_parallel_same_awg_is_one() -> None:
    eq = equivalent_num_parallel(1, 19, 19)
    assert eq is not None
    assert eq["n_parallel_ceil"] == 1
    assert eq["n_parallel_floor"] == 1


def test_turns_for_voltage_220_to_380() -> None:
    n2 = turns_for_voltage_ratio(100.0, 220.0, 380.0)
    assert n2 is not None
    assert math.isclose(n2, 100.0 * 380.0 / 220.0, rel_tol=1e-9)


def test_series_total_turns() -> None:
    assert series_total_turns([10.0, 5.0, 2.0]) == 17.0


def test_parallel_branch_current_split() -> None:
    assert parallel_branch_current_split(6.0, 2) == 3.0
    assert parallel_branch_current_split(6.0, 1) == 6.0


def test_suggest_awg_combos_sorted_by_error() -> None:
    target = 0.65
    sugs = suggest_awg_combos_for_area(target, max_parallel=4)
    assert len(sugs) >= 1
    assert len(sugs) <= 12
    if len(sugs) > 1:
        assert sugs[0]["rel_error"] <= sugs[1]["rel_error"]
