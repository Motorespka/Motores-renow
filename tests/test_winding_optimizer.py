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
    MIN_ESPIRAS_2P_FRAME_71_90,
    MSG_ESTIMATIVA_TECNICA_FORCADA,
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
    assert 14.0 <= cen_a.wire.awg <= 22.0
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


def test_magnetic_sanity_gate_2_polos_substitutes_hist():
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
    assert res.magnetic_sanity_gate_active
    cen_b = next(c for c in res.cenarios if c.cenario_id == "B")
    assert cen_b.espiras >= float(MIN_ESPIRAS_2P_FRAME_71_90) - 0.05
    assert cen_b.confidence_score <= 40
    alerts_joined = " ".join(cen_b.alertas)
    assert MSG_ESTIMATIVA_TECNICA_FORCADA in alerts_joined
