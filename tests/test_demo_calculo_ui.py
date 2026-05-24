#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.physics_audit import MSG_B_ABORT, cenario_valido_para_painel_recomendado
from page.demo_calculo_ui import (
    KPI_NA,
    is_cenario_inviavel_visual,
    pick_primary_candidate,
    resolve_recommended_optimizer_scenario,
)
from services.gemini_engineering_validator import (
    _GEMINI_ABORT_COMENTARIO,
    validate_magnetic_with_gemini,
)


def _opt_payload(*, espiras: float, awg_text: str, alertas=None, rec="B", **extra):
    cen = {
        "cenario_id": "B",
        "espiras": espiras,
        "fio_texto": awg_text,
        "physics_confidence": extra.get("physics_confidence", 85),
        "confidence_score": extra.get("confidence_score", 85),
        "fator_ocupacao_ranhura": extra.get("fator_ocupacao_ranhura", 40.0),
        "fill_factor_ff": extra.get("fill_factor_ff", 0.40),
        "desabilitado": False,
        "alertas": alertas or [],
        "wire": {"awg": 19.0, "parallel_count": 1},
    }
    return {
        "cenario_recomendado": rec,
        "cenarios": [cen],
    }


def test_is_inviavel_visual_matches_user_hard_block():
    cen = {
        "physics_confidence": 0,
        "fill_factor_ff": 0.668,
        "alertas": ["Cálculo Abortado: Risco Severo de Saturação"],
    }
    assert is_cenario_inviavel_visual(cen)
    assert is_cenario_inviavel_visual(None)

    ok = {
        "physics_confidence": 85,
        "fill_factor_ff": 0.40,
        "alertas": [],
        "fator_ocupacao_ranhura": 40.0,
    }
    assert not is_cenario_inviavel_visual(ok)


def test_gate_rejects_ff_above_45_percent():
    cen = {
        "cenario_id": "B",
        "espiras": 45.0,
        "fill_factor_ff": 0.668,
        "physics_confidence": 0,
        "confidence_score": 0,
        "fator_ocupacao_ranhura": 68.0,
        "desabilitado": False,
        "alertas": [],
        "wire": {"awg": 15.0, "parallel_count": 1},
    }
    assert not cenario_valido_para_painel_recomendado(cen)


def test_gate_rejects_ocupacao_above_45():
    cen = {
        "cenario_id": "B",
        "espiras": 45.0,
        "fill_factor_ff": 0.40,
        "physics_confidence": 80,
        "confidence_score": 80,
        "fator_ocupacao_ranhura": 68.1,
        "desabilitado": False,
        "alertas": [],
        "wire": {"awg": 17.0, "parallel_count": 1},
    }
    assert not cenario_valido_para_painel_recomendado(cen)


def test_pick_primary_prefers_optimizer_over_twin():
    opt = _opt_payload(espiras=45.0, awg_text="Sugestão: 45 espiras, 1×19 AWG")
    twin = {
        "candidatos": [
            {
                "opcao": "A",
                "espiras_por_bobina": 36.4,
                "descricao": "1×15 AWG",
                "confianca_pct": 99,
                "ocupacao_ff": 0.68,
                "alertas": [],
            }
        ]
    }
    esp, bitola, conf, _, _ = pick_primary_candidate(twin, opt)
    assert esp == 45.0
    assert "19" in str(bitola)
    assert conf == 85


def test_pick_primary_never_uses_twin_when_optimizer_ran():
    opt = _opt_payload(
        espiras=36.4,
        awg_text="Sugestão: 36.4 espiras, 1×15 AWG",
        alertas=[MSG_B_ABORT],
        physics_confidence=0,
        fator_ocupacao_ranhura=68.0,
        fill_factor_ff=0.668,
    )
    twin = {
        "candidatos": [
            {
                "opcao": "A",
                "espiras_por_bobina": 36.4,
                "descricao": "1×15 AWG",
                "confianca_pct": 99,
                "ocupacao_ff": 0.68,
                "alertas": [],
            }
        ]
    }
    assert resolve_recommended_optimizer_scenario(opt) is None
    esp, bitola, _, _, tier = pick_primary_candidate(twin, opt)
    assert esp == KPI_NA
    assert bitola == KPI_NA
    assert tier == "red"


def test_gemini_abort_short_circuit():
    out = validate_magnetic_with_gemini({"calculo_abortado": True})
    assert out["comentario_validacao"] == _GEMINI_ABORT_COMENTARIO
    assert out["validacao_magnetica"] == "REVISAR"
