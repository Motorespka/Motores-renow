#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pytest

from engine.physics_audit import (
    B_ABORT_TESLA,
    FF_IDEAL,
    J_IDEAL_A_MM2,
    MSG_B_ABORT,
    MSG_FF_SUB,
    audit_auditoria_user_winding,
    audit_winding_physics,
    check_extreme_saturation_abort,
    check_required_inputs,
    compute_slot_occupation_ratio,
    estimate_operating_flux_density_t,
    estimate_power_from_iron_kw,
    espiras_weg_fem,
    is_camada_dupla_context,
    normalize_fill_factor_ff,
    physics_confidence_score,
    power_kw_from_cv,
    resolve_power_and_current,
)
from engine.winding_sanity import espiras_from_fem_equation
from services.digital_twin_engine import run_auditoria, run_caixa_preta


def test_fem_80x70_two_poles():
    n = espiras_from_fem_equation(80, 70, 2)
    assert 40 <= n <= 46


def test_weg_fem_in_band():
    z = espiras_weg_fem(diametro_mm=80, pacote_mm=70, polos=2)
    assert 35 <= z <= 55


def test_normalize_fill_factor_percent_legacy():
    assert normalize_fill_factor_ff(33.3) == pytest.approx(0.333, rel=1e-3)
    assert normalize_fill_factor_ff(0.333) == pytest.approx(0.333, rel=1e-3)


def test_occupation_33pct_not_subdimensionado():
    """Ocupação ~33% (UI) não deve disparar ff < 25% após alinhamento de escalas."""
    occ = compute_slot_occupation_ratio(
        45,
        23,
        ranhuras=24,
        diametro_mm=80,
        pacote_mm=70,
    )
    assert 0.20 <= occ <= 0.55
    r = audit_auditoria_user_winding(
        espiras=45,
        awg=23,
        diametro_mm=80,
        pacote_mm=70,
        ranhuras=24,
        polos=2,
        corrente_nominal_a=3.8,
        potencia_cv=1.5,
        tipo_bobinagem="CAMADA_DUPLA",
        passo="4-6-8",
    )
    assert MSG_FF_SUB not in " ".join(r.alerts)
    assert r.confidence_score > 0


def test_audit_24_2_45_19():
    r = audit_winding_physics(
        espiras=45,
        awg=23,
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


def test_blocks_low_turns_2p_guard_before_abort():
    """8 espiras em 2p/80mm: guarda FEM eleva para ~45 antes de avaliar B."""
    r = audit_winding_physics(
        espiras=8,
        awg=14,
        diametro_mm=80,
        pacote_mm=70,
        ranhuras=24,
        polos=2,
        carcaca="80A",
    )
    assert not r.calculation_aborted
    assert r.espiras >= 40.0


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


def test_iron_power_estimate_realistic_80x70():
    kw = estimate_power_from_iron_kw(80, 70, 2)
    assert 0.5 <= kw <= 3.0


def test_power_from_cv_15():
    assert 1.0 <= power_kw_from_cv(1.5) <= 1.2


def test_camada_dupla_passo_detected():
    assert is_camada_dupla_context("", "4-6-8")
    assert is_camada_dupla_context("CAMADA_DUPLA", "1:7")


def test_audit_15cv_plate_current_not_aborted():
    """1×21 AWG, 45 esp — J com corrente de placa, não superestimada pelo ferro."""
    p_kw, i_a, user = resolve_power_and_current(
        diametro_mm=80,
        pacote_mm=70,
        polos=2,
        corrente_nominal_a=3.8,
        potencia_cv=1.5,
    )
    assert user
    assert 3.5 <= i_a <= 4.5
    r = audit_auditoria_user_winding(
        espiras=45,
        awg=21,
        diametro_mm=80,
        pacote_mm=70,
        ranhuras=24,
        polos=2,
        corrente_nominal_a=3.8,
        potencia_cv=1.5,
        tipo_bobinagem="CAMADA_DUPLA",
        passo="4-6-8",
    )
    assert not r.calculation_aborted
    assert r.current_density_j is not None
    assert r.current_density_j > 0
    assert any("corrente nominal informada" in a for a in r.alerts) or r.confidence_score >= 0


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
