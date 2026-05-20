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
    MSG_BUSSOLA_DIVERGENTE,
    apply_commercial_awg_preserve_copper,
    awg_for_fill_with_limits,
    busola_historica_inconsistente,
    clamp_awg_to_safe_range,
    espiras_busola_oficina,
    espiras_constante_k,
    exceeds_hist_bias,
    force_busola_if_underturn,
    is_awg_in_range,
    magnetic_reference_turns_scaled,
    polarity_sanity_alert,
    scenario_a_is_acceptable,
    should_alert_low_turns,
    should_override_hist_by_magnetic_gate,
)


def test_clamp_zero_awg_to_14_for_80a():
    awg, adj, msg = clamp_awg_to_safe_range(0.0, "80A")
    assert awg == 14.0
    assert adj
    assert msg


def test_awg_in_range_80a():
    assert is_awg_in_range(19, "80A")
    assert not is_awg_in_range(0, "80A")
    assert not is_awg_in_range(23, "80A")  # mesa 14–22


def test_espiras_constante_k_thicker_wire_fewer_turns():
    # Referência 42 espiras @ 23 AWG; fio mais grosso (19) => mais espiras? 
    # N * A = const => N_new = N * A_ref / A_new; A_19 > A_23 => N_new < N_ref
    n = espiras_constante_k(42.0, 23.0, 19.0)
    assert n < 42.0
    assert n > 20.0


def test_espiras_busola_prioriza_proporcional_nao_mediana():
    b = espiras_busola_oficina(42.0, 19.0)
    assert b == 19.0


def test_espiras_busola_usuario_100pct():
    b = espiras_busola_oficina(8.0, 19.0, espiras_usuario=42.0)
    assert b == 42.0


def test_busola_inconsistente_quando_hist_diverge():
    assert busola_historica_inconsistente(42.0, 8.0)
    assert not busola_historica_inconsistente(42.0, 40.0)
    assert MSG_BUSSOLA_DIVERGENTE


def test_exceeds_hist_bias_20pct():
    assert exceeds_hist_bias(19.0, 42.0, 0.20)
    assert not exceeds_hist_bias(40.0, 42.0, 0.20)


def test_commercial_awg_round_and_volume():
    esp, awg, adj, _ = apply_commercial_awg_preserve_copper(42.0, 16.8, "80A")
    assert awg == 17.0
    assert adj
    assert 35.0 < esp < 45.0


def test_magnetic_reference_scales_with_volume():
    n80 = magnetic_reference_turns_scaled(80.0, 70.0)
    assert 41.0 <= n80 <= 43.0
    n90 = magnetic_reference_turns_scaled(90.0, 70.0)
    assert n90 > n80


def test_should_override_hist_magnetic_2p():
    assert should_override_hist_by_magnetic_gate(2, 80, 25.0)
    assert not should_override_hist_by_magnetic_gate(2, 80, 40.0)
    assert not should_override_hist_by_magnetic_gate(4, 80, 8.0)


def test_low_turns_alert():
    assert should_alert_low_turns(19.0, 42.0, polos=2, ranhuras=36)


def test_fill_limits_never_below_14_awg():
    # slot_limit alto + poucas espiras costumava gerar 0 AWG
    awg, adj, _ = awg_for_fill_with_limits(19.0, 500.0, 0.75, "80A")
    assert awg >= 14.0
    assert awg <= 22.0


def test_force_busola_never_overrides_by_hist():
    esp, forced = force_busola_if_underturn(8.0, 42.0, diametro_mm=80, carcaca="80A")
    assert not forced
    assert esp == 8.0


def test_polarity_alert_2_poles_low_turns():
    assert polarity_sanity_alert(2, 15.0, 42.0, "80A")
    assert not polarity_sanity_alert(4, 15.0, 42.0, "80A")


def test_scenario_a_fill_only_not_hist():
    assert scenario_a_is_acceptable(19.0, 0.50)
    assert not scenario_a_is_acceptable(41.0, 0.95)
