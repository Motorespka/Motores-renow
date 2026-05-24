#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from page.demo_calculo_validation import (
    parse_tensao_rede,
    primary_voltage_for_physics,
    validate_demo_submit,
    vision_needs_manual_fallback,
)


def test_parse_tensao_rede_multi():
    volts, display = parse_tensao_rede("110/220/380")
    assert volts == [110.0, 220.0, 380.0]
    assert display == "110/220/380"


def test_parse_tensao_rede_dedup_sort():
    volts, display = parse_tensao_rede("380/220/380")
    assert volts == [220.0, 380.0]
    assert display == "220/380"


def test_primary_voltage_trifasico():
    assert primary_voltage_for_physics([110, 220, 380], tipo_motor="TRIFASICO") == 380.0
    assert primary_voltage_for_physics([220, 380, 440], tipo_motor="TRIFASICO") == 380.0


def test_primary_voltage_monofasico():
    assert primary_voltage_for_physics([110, 220], tipo_motor="MONOFASICO") == 220.0


def test_validate_accepts_multi_tensao():
    errs = validate_demo_submit(
        modo_op="Acervo proporcional",
        diametro_mm=80,
        pacote_mm=70,
        ranhuras=24,
        tensao_raw="110/220/380",
        esp_eng="45",
        fio_eng="19",
    )
    assert not errs


def test_validate_rejects_invalid_tensao():
    errs = validate_demo_submit(
        modo_op="Acervo proporcional",
        diametro_mm=80,
        pacote_mm=70,
        ranhuras=24,
        tensao_raw="abc",
        esp_eng="45",
        fio_eng="19",
    )
    assert any("inválida" in e.lower() for e in errs)
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
