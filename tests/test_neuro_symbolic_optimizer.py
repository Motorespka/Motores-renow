#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from unittest.mock import patch

from engine.winding_optimizer import (
    StatorInput,
    generate_inference_candidate_pool,
)
from services.gemini_evaluator import (
    combined_j_ff_error,
    deterministic_candidate_fallback,
    evaluate_candidate_pool_with_gemini,
    resolve_best_candidate,
)


def test_inference_candidate_has_audit_soft_structure():
    stator = StatorInput(
        diametro_mm=80.0,
        pacote_mm=70.0,
        ranhuras=36,
        polos=4,
        carcaca="nema",
        passo="10-12",
    )
    pool = generate_inference_candidate_pool(stator, esp_ref=45.0, awg_base=19.0)
    aud = pool[0].get("audit_soft") or {}
    assert "d_w_mm_nominal_formula" in aud
    assert "ff_packaging_square_theory" in aud
    assert "ff_packaging_hex_theory" in aud
    assert "warn_ff_above_075" in aud
    assert "warn_j_above_8" in aud


def test_resolve_best_candidate_invalid_index_uses_fallback():
    pool = [{"espiras": 10.0, "awg": 20.0, "j_a_mm2": 9.0, "ff": 0.5}]
    ev, best = resolve_best_candidate(pool, {"status": "INVIÁVEL", "best_candidate_index": 99})
    assert best is pool[0]
    assert ev.get("fallback") is True


def test_generate_inference_candidate_pool_never_empty_for_stator_80():
    stator = StatorInput(
        diametro_mm=80.0,
        pacote_mm=70.0,
        ranhuras=36,
        polos=4,
        carcaca="nema",
        passo="10-12",
    )
    pool = generate_inference_candidate_pool(
        stator,
        esp_ref=45.0,
        awg_base=19.0,
    )
    assert 5 <= len(pool) <= 8
    assert all(c.get("espiras", 0) > 0 for c in pool)


def test_generate_inference_candidate_pool_survives_audit_exception():
    """Se audit_winding_physics falha, stub mantém o pool preenchido."""
    stator = StatorInput(
        diametro_mm=80.0,
        pacote_mm=70.0,
        ranhuras=36,
        polos=4,
        carcaca="nema",
        passo="10-12",
    )
    with patch("engine.physics_audit.audit_winding_physics", side_effect=RuntimeError("simulated crash")):
        pool = generate_inference_candidate_pool(stator, esp_ref=45.0, awg_base=19.0)
    assert len(pool) >= 5
    for c in pool:
        assert "espiras" in c


def test_evaluate_candidate_pool_gemini_fallback_when_no_api_key():
    """Sem chave: deve cair em fallback determinístico com índice válido."""
    candidates = [
        {"index": 0, "espiras": 45.0, "awg": 19.0, "parallel_count": 1, "j_a_mm2": 7.0, "ff": 0.44},
        {"index": 1, "espiras": 50.0, "awg": 18.0, "parallel_count": 1, "j_a_mm2": 5.0, "ff": 0.38},
    ]
    with patch("services.gemini_evaluator._api_key", return_value=""):
        out = evaluate_candidate_pool_with_gemini(candidates, {"diametro_mm": 80})
    assert out.get("fallback") is True
    idx = int(out.get("best_candidate_index", -1))
    assert 0 <= idx < len(candidates)


def test_deterministic_fallback_picks_lowest_penalty():
    candidates = [
        {"espiras": 45, "awg": 19, "j_a_mm2": 7.8, "ff": 0.45},
        {"espiras": 48, "awg": 17, "j_a_mm2": 5.2, "ff": 0.42},
        {"espiras": 42, "awg": 21, "j_a_mm2": 6.5, "ff": 0.47},
    ]
    result = deterministic_candidate_fallback(candidates)
    assert result["fallback"] is True
    assert result["best_candidate_index"] == 1
    assert result["status"] in ("APROVADO", "APROVADO_COM_RESSALVAS", "INVIÁVEL")


def test_combined_j_ff_error_prefers_lower_j():
    high_j = combined_j_ff_error({"j_a_mm2": 7.5, "ff": 0.40})
    low_j = combined_j_ff_error({"j_a_mm2": 4.5, "ff": 0.40})
    assert low_j < high_j
