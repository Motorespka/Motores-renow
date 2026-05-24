#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Testes do validador físico central (Regra de Ouro)."""

import pytest

from engine.physics_audit import audit_auditoria_user_winding
from engine.physics_validator import PhysicsValidator, PhysicsValidatorEngine


def test_wire_area_lookup_awg19():
    assert PhysicsValidator.calculate_wire_area(19) == pytest.approx(0.653, rel=1e-3)


def test_validate_wire_replacement_reproves_19_to_23():
  """Estudo de caso: 1×19 → 1×23 mantendo N → ΔA > 5%."""
  a19 = PhysicsValidator.total_copper_area_mm2(awg=19)
  a23 = PhysicsValidator.total_copper_area_mm2(awg=23)
  ok, msg = PhysicsValidator.validate_wire_replacement(a19, a23)
  assert not ok
  assert "INCOERÊNCIA FÍSICA" in msg
  delta = abs(a23 - a19) / a19
  assert delta > 0.5


def test_validate_winding_swap_stress_80x70_45esp_19_to_23():
    """
    Teste de estresse solicitado:
    motor 80×70, 45 espiras, troca fio 19 → 23 → REPROVADO.
    """
    ok, msg = PhysicsValidator.validate_winding_swap(
        awg_original=19,
        awg_novo=23,
        parallel_original=1,
        parallel_novo=1,
        espiras_original=45,
        espiras_novo=45,
    )
    assert not ok
    assert "INCOERÊNCIA" in msg.upper() or "REPROVADO" in msg.upper()

    audit = audit_auditoria_user_winding(
        espiras=45,
        awg=23,
        diametro_mm=80,
        pacote_mm=70,
        ranhuras=36,
        polos=2,
        corrente_nominal_a=3.8,
        potencia_cv=1.5,
    )
    verdict = PhysicsValidatorEngine.validate_scenario_render(
        espiras=45,
        awg=23,
        parallel_count=1,
        fill_factor_ff=audit.fill_factor_ff,
        current_density_j=audit.current_density_j,
        b_tesla=audit.flux_density_b_t,
        awg_referencia=19,
        espiras_referencia=45,
        strict_j=True,
    )
    assert verdict.reprovado_fisicamente
    assert verdict.status == "REPROVADO"
    block = PhysicsValidatorEngine.format_output_block(verdict)
    assert "STATUS: REPROVADO" in block


def test_ff_limits_use_decimal_not_percent():
    ok, _ = PhysicsValidator.validate_fill_factor(0.333)
    assert ok
    ok2, msg2 = PhysicsValidator.validate_fill_factor(0.20)
    assert not ok2
    assert "25%" in msg2 or "0,25" in msg2 or "0.25" in msg2
