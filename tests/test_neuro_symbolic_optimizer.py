#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from engine.winding_optimizer import (
    StatorInput,
    generate_inference_candidate_pool,
)
from services.gemini_evaluator import (
    combined_j_ff_error,
    deterministic_candidate_fallback,
)


def test_generate_inference_candidate_pool_size_and_fields():
    stator = StatorInput(
        diametro_mm=80.0,
        pacote_mm=70.0,
        ranhuras=36,
        polos=4,
        carcaca="nema",
        passo="10-12",
        tipo_bobinagem="",
        ligacao="Estrela",
    )
    pool = generate_inference_candidate_pool(
        stator,
        esp_ref=45.0,
        awg_base=19.0,
    )
    assert len(pool) >= 5
    for row in pool:
        assert row["espiras"] > 0
        assert row["awg"] > 0
        assert "j_a_mm2" in row
        assert "ff" in row
        assert "b_tesla" in row
        assert "violations" in row


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
