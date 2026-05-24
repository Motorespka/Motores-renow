#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.winding_optimizer import (  # noqa: E402
    StatorInput,
    WindingOptimizer,
)
from engine.winding_sanity import (  # noqa: E402
    CALIBRE_INVALIDO,
)
from app.search_lib import MotorRow  # noqa: E402


def _motor(**kw) -> MotorRow:
    return MotorRow(
        sha=kw.get("sha", "x"),
        arquivo_rel="a.json",
        melhor_status="VERDE_SEGURO",
        carcaca=kw.get("carcaca", "80A"),
        diametro_mm=kw.get("diametro_mm", 80.0),
        pacote_mm=kw.get("pacote_mm", 70.0),
        passo_principal=kw.get("passo_principal", "1-7"),
        passo_nums_json="[1,7]",
        fio_principal=kw.get("fio_principal", "23"),
        espiras_principal=kw.get("espiras_principal", 30.0),
        fio_auxiliar="",
        espiras_auxiliar=None,
        potencia_cv="",
        polos="4",
        tipo_motor="",
        ligacao="",
        tipo_bobinagem="IMBRICADO",
        tipo_bobinagem_norm="IMBRICADO",
        is_file=1,
    )


def test_optimize_returns_three_scenarios():
    pool = [
        _motor(sha="1", espiras_principal=42.0, fio_principal="17"),
        _motor(sha="2", passo_principal="1-7", espiras_principal=42.0, fio_principal="17"),
    ]
    opt = WindingOptimizer(pool)
    res = opt.optimize(
        StatorInput(
            diametro_mm=80,
            pacote_mm=70,
            ranhuras=36,
            polos=4,
            carcaca="80A",
            passo="1:7",
            tipo_bobinagem="IMBRICADO",
        ),
        use_gemini=False,
    )
    assert len(res.cenarios) == 3
    ids = {c.cenario_id for c in res.cenarios}
    assert ids == {"A", "B", "C"}


def test_scenario_a_awg_within_safe_range():
    pool = [_motor(sha="1", espiras_principal=42.0, fio_principal="17")]
    res = WindingOptimizer(pool).optimize(
        StatorInput(
            diametro_mm=80,
            pacote_mm=70,
            ranhuras=36,
            polos=4,
            carcaca="80A",
            passo="1:7",
        ),
        use_gemini=False,
    )
    cen_a = next(c for c in res.cenarios if c.cenario_id == "A")
    assert 10.0 <= cen_a.wire.awg <= 36.0
    assert cen_a.fio_texto != CALIBRE_INVALIDO or cen_a.desabilitado


def test_mandatory_fields_block():
    opt = WindingOptimizer([])
    res = opt.optimize(
        StatorInput(diametro_mm=80, pacote_mm=70, ranhuras=0, polos=4),
    )
    assert res.validation_status == "INCOMPLETO"
    assert not res.cenarios


def test_optimize_without_polos_is_allowed():
    pool = [
        _motor(sha="1", espiras_principal=42.0, fio_principal="17"),
        _motor(sha="2", passo_principal="1-7", espiras_principal=42.0, fio_principal="17"),
    ]
    res = WindingOptimizer(pool).optimize(
        StatorInput(
            diametro_mm=80,
            pacote_mm=70,
            ranhuras=36,
            polos=None,
            carcaca="80A",
            passo="1:7",
        ),
        use_gemini=False,
    )
    assert res.validation_status != "INCOMPLETO"
    assert len(res.cenarios) >= 2


def test_optimize_recommended_passes_ff_cap():
    pool = [_motor(sha="1", espiras_principal=42.0, fio_principal="17")]
    res = WindingOptimizer(pool).optimize(
        StatorInput(
            diametro_mm=80,
            pacote_mm=70,
            ranhuras=24,
            polos=2,
            carcaca="80A",
            passo="1:7",
        ),
        use_gemini=False,
    )
    rec_id = res.cenario_recomendado
    assert rec_id, "esperado cenário recomendado com ff dentro do limite"
    rec = next(c for c in res.cenarios if c.cenario_id == rec_id)
    assert rec.fill_factor_ff is None or rec.fill_factor_ff <= 0.451
    assert rec.espiras >= 35


def test_user_validation_overrides_historical_busola():
    pool = [
        _motor(sha="1", espiras_principal=8.0),
        _motor(sha="2", espiras_principal=42.0, passo_principal="1-7"),
    ]
    res = WindingOptimizer(pool).optimize(
        StatorInput(
            diametro_mm=80,
            pacote_mm=70,
            ranhuras=36,
            polos=4,
            carcaca="80A",
            passo="1:7",
            espiras_validacao_usuario=42.0,
            fio_validacao_usuario_awg=23.0,
        ),
        use_gemini=False,
    )
    cen_b = next(c for c in res.cenarios if c.cenario_id == "B")
    assert res.usa_validacao_usuario
    assert cen_b.espiras == 42.0


def test_motor_24_2_45_19_awg_validation():
    """Motor real: 24 ranhuras, 2 polos, 45 espiras, 1×19 AWG."""
    pool = [
        _motor(sha="1", espiras_principal=8.0, polos="2"),
        _motor(sha="2", espiras_principal=42.0, passo_principal="1-7", polos="4"),
    ]
    res = WindingOptimizer(pool).optimize(
        StatorInput(
            diametro_mm=80,
            pacote_mm=70,
            ranhuras=24,
            polos=2,
            carcaca="80A",
            passo="1:7",
            espiras_validacao_usuario=45.0,
            fio_validacao_usuario_awg=19.0,
        ),
        use_gemini=False,
    )
    cen_b = next(c for c in res.cenarios if c.cenario_id == "B")
    cen_c = next(c for c in res.cenarios if c.cenario_id == "C")
    assert res.usa_validacao_usuario
    assert cen_b.espiras == 45.0
    assert cen_b.wire.awg == 19.0
    assert cen_b.wire.parallel_count == 1
    assert "2x 22" in (cen_b.fio_alternativa_paralelo or "")
    assert cen_c.espiras == 45.0
    assert cen_c.wire.parallel_count == 2
    assert cen_c.wire.awg == 22.0
    assert cen_b.fator_ocupacao_ranhura <= 85.0


def test_fem_blocks_8_turns_proportional_2p():
    """Estatística contaminada (8 esp) → FEM força ~45 espiras."""
    pool = [
        _motor(sha="1", espiras_principal=8.0, polos="2", passo_principal="1-7"),
        _motor(sha="2", espiras_principal=42.0, polos="2", passo_principal="1-7"),
    ]
    res = WindingOptimizer(pool).optimize(
        StatorInput(
            diametro_mm=80,
            pacote_mm=70,
            ranhuras=24,
            polos=2,
            carcaca="80A",
            passo="1:7",
        ),
        use_gemini=False,
    )
    cen_b = next(c for c in res.cenarios if c.cenario_id == "B")
    assert cen_b.espiras >= 40.0
    assert cen_b.fator_ocupacao_ranhura <= 90.0


def test_magnetic_sanity_gate_2_polos_uses_proportional_not_hist():
    pool = [
        _motor(
            sha="a",
            espiras_principal=25.0,
            passo_principal="1-7",
            polos="2",
            carcaca="80",
        ),
        _motor(
            sha="b",
            espiras_principal=25.0,
            passo_principal="1-7",
            polos="2",
            carcaca="80B",
        ),
    ]
    res = WindingOptimizer(pool).optimize(
        StatorInput(
            diametro_mm=80,
            pacote_mm=70,
            ranhuras=36,
            polos=2,
            carcaca="80A",
            passo="1:7",
        ),
        use_gemini=False,
    )
    assert not res.magnetic_sanity_gate_active
    cen_b = next(c for c in res.cenarios if c.cenario_id == "B")
    assert cen_b.espiras >= 20
