#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from engine.physics_audit import (
    B_ABORT_TESLA,
    FF_IDEAL,
    J_IDEAL_A_MM2,
    MSG_B_ABORT,
    audit_auditoria_user_winding,
    audit_winding_physics,
    check_extreme_saturation_abort,
    check_required_inputs,
    estimate_operating_flux_density_t,
    espiras_weg_fem,
    physics_confidence_score,
)
from engine.winding_sanity import espiras_from_fem_equation
from services.digital_twin_engine import run_auditoria, run_caixa_preta


def test_fem_80x70_two_poles():
    n = espiras_from_fem_equation(80, 70, 2)
    assert 40 <= n <= 46


def test_weg_fem_in_band():
    z = espiras_weg_fem(diametro_mm=80, pacote_mm=70, polos=2)
    assert 35 <= z <= 55


def test_audit_24_2_45_19():
    r = audit_winding_physics(
        espiras=45,
        awg=19,
        diametro_mm=80,
        pacote_mm=70,
        ranhuras=24,
        polos=2,
        carcaca="80A",
    )
    assert r.espiras >= 40
    assert 0.2 <= r.fill_factor_ff <= 0.55
    assert r.flux_density_ok


def test_confidence_ideal():
    assert physics_confidence_score(
        j_a_mm2=J_IDEAL_A_MM2, ff=FF_IDEAL, flux_ok=True, survival_pass=True
    ) >= 85


def test_blocks_low_turns_2p_aborts_instead_of_guard():
    """8 espiras em 2p/80mm: B > 1.8 T → aborta (não altera espiras via guarda)."""
    r = audit_winding_physics(
        espiras=8,
        awg=14,
        diametro_mm=80,
        pacote_mm=70,
        ranhuras=24,
        polos=2,
        carcaca="80A",
    )
    assert r.calculation_aborted
    assert r.espiras == 8.0
    assert r.confidence_score == 0


def test_checklist_missing_voltage():
    ok, missing = check_required_inputs(
        {"diametro_mm": 80, "pacote_mm": 70, "ranhuras": 24},
        modo="caixa_preta",
    )
    assert not ok
    assert any("Tensão" in m for m in missing)


def test_checklist_ok_with_tensao():
    ok, missing = check_required_inputs(
        {
            "diametro_mm": 80,
            "pacote_mm": 70,
            "ranhuras": 24,
            "tensao_v": 220,
        },
        modo="caixa_preta",
    )
    assert ok
    assert not missing


def test_caixa_preta_complete():
    twin = run_caixa_preta(
        {
            "diametro_mm": 80,
            "pacote_mm": 70,
            "ranhuras": 24,
            "polos": 2,
            "carcaca": "80A",
            "ligacao": "Estrela",
            "tensao_v": 220,
        },
        use_vision=False,
    )
    assert twin.completo
    assert len(twin.candidatos) >= 3


def test_b_exceeds_abort_threshold():
    b = estimate_operating_flux_density_t(8, 80, 70, 2)
    assert b > B_ABORT_TESLA
    aborted, b2, msg = check_extreme_saturation_abort(8, 80, 70, 2)
    assert aborted
    assert MSG_B_ABORT in msg


def test_audit_auditoria_abort_zero_confidence():
    r = audit_auditoria_user_winding(
        espiras=8,
        awg=14,
        diametro_mm=80,
        pacote_mm=70,
        ranhuras=24,
        polos=2,
    )
    assert r.calculation_aborted
    assert r.confidence_score == 0
    assert r.espiras == 8.0
    assert MSG_B_ABORT in r.alerts[0]


def test_auditoria_suspeito():
    twin = run_auditoria(
        {
            "diametro_mm": 80,
            "pacote_mm": 70,
            "ranhuras": 24,
            "polos": 2,
            "espiras_engenheiro": 8,
            "fio_engenheiro": 14,
            "tensao_v": 220,
        },
        use_gemini=False,
    )
    assert twin.completo
    assert twin.saturacao_abortada
    assert twin.candidatos[0].opcao == "SUSPEITO"
    assert twin.candidatos[0].confianca_pct == 0
    assert any(MSG_B_ABORT in (a or "") for a in twin.candidatos[0].alertas)
    assert len(twin.candidatos) == 1
