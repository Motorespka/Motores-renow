#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from engine.physics_validator import PhysicsValidatorEngine
from page.demo_calculo_diagnostics import (
    WindingSnapshot,
    build_physics_verdict,
)
from services.laudo_rebobinagem_pdf import build_laudo_pdf_bytes


def test_build_laudo_pdf_bytes():
    orig = WindingSnapshot(
        titulo="Original",
        espiras=45.0,
        awg=19.0,
        fio_texto="1×19 AWG",
        j_a_mm2=4.2,
        ff=0.33,
        b_tesla=1.2,
    )
    prop = WindingSnapshot(
        titulo="Proposta",
        espiras=45.0,
        awg=23.0,
        fio_texto="1×23 AWG",
        j_a_mm2=6.5,
        ff=0.28,
        b_tesla=1.25,
    )
    verdict = build_physics_verdict(orig, prop)
    pdf = build_laudo_pdf_bytes(
        motor_modelo="Ø80×70 · 80A",
        original=orig,
        proposed=prop,
        verdict=verdict,
        entrada={"diametro_mm": 80, "pacote_mm": 70, "ranhuras": 36, "carcaca": "80A"},
    )
    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 500
    assert verdict.status == "REPROVADO"
