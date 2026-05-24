#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from engine.copper_inventory import (
    calculate_copper_weight,
    estimate_copper_from_winding,
)
from engine.physics_validator import PhysicsValidator


def test_calculate_copper_weight_positive():
    kg = calculate_copper_weight(45, 12, 0.65, mean_turn_length_mm=250.0)
    assert kg > 0.1


def test_estimate_from_winding():
    est = estimate_copper_from_winding(
        espiras=45,
        awg=23,
        ranhuras=36,
        diametro_estator_mm=80,
        pacote_mm=70,
    )
    assert est.peso_kg > 0
    assert "kg" in est.as_table_row()["Quantidade"]


def test_stress_19_to_23_area_incoherent():
    a19 = PhysicsValidator.total_copper_area_mm2(awg=19)
    a23 = PhysicsValidator.total_copper_area_mm2(awg=23)
    ok, _ = PhysicsValidator.validate_wire_replacement(a19, a23)
    assert not ok
