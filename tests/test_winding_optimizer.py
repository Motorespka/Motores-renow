#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.winding_optimizer import (  # noqa: E402
    ALERT_DESVIO_HIST,
    StatorInput,
    WindingOptimizer,
    _confidence_score,
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
    pool = [_motor(sha="1"), _motor(sha="2", passo_principal="1-7")]
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


def test_confidence_low_on_saturation():
    score, alerts = _confidence_score(
        espiras=20,
        media_prop=40,
        media_hist=38,
        fill_ratio=0.5,
        flux_index=0.01,
        flux_ref=0.005,
        n_refs=5,
    )
    assert score < 50
    assert any("Saturação" in a for a in alerts)


def test_mandatory_fields_block():
    opt = WindingOptimizer([])
    res = opt.optimize(
        StatorInput(diametro_mm=80, pacote_mm=70, ranhuras=0, polos=4),
    )
    assert res.validation_status == "INCOMPLETO"
    assert not res.cenarios
