#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from page.demo_calculo_validation import (
    validate_demo_submit,
    vision_needs_manual_fallback,
)


def test_validate_rejects_zero_diameter():
    errs = validate_demo_submit(
        modo_op="Acervo proporcional",
        diametro_mm=0,
        pacote_mm=70,
        ranhuras=24,
        tensao_v=220,
        esp_eng="45",
        fio_eng="19",
    )
    assert any("Diâmetro" in e for e in errs)


def test_validate_requires_tensao():
    errs = validate_demo_submit(
        modo_op="Caixa preta — estator vazio (FEM + visão)",
        diametro_mm=80,
        pacote_mm=70,
        ranhuras=24,
        tensao_v=None,
        esp_eng="",
        fio_eng="",
    )
    assert any("tensão" in e.lower() for e in errs)


def test_validate_auditoria_requires_espiras():
    errs = validate_demo_submit(
        modo_op="Auditoria — cálculo suspeito",
        diametro_mm=80,
        pacote_mm=70,
        ranhuras=24,
        tensao_v=220,
        esp_eng="",
        fio_eng="19",
    )
    assert any("espiras" in e.lower() for e in errs)


def test_vision_manual_fallback_low_confidence():
    assert vision_needs_manual_fallback({"confianca_visao": 0.2})
    assert not vision_needs_manual_fallback({"confianca_visao": 0.85})
