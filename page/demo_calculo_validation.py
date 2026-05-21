#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validação de inputs do formulário Demo Cálculo (Fase 3 — caminho infeliz)."""

from __future__ import annotations

from typing import Any

from app.search_lib import parse_awg_number, parse_scalar

# Limites físicos aceitáveis na UI
DIAMETRO_MM_MIN = 20.0
DIAMETRO_MM_MAX = 500.0
PACOTE_MM_MIN = 5.0
PACOTE_MM_MAX = 800.0
RANHURAS_MIN = 1
RANHURAS_MAX = 120
POLOS_MAX = 12
TENSAO_V_MIN = 110
TENSAO_V_MAX = 480
ESPIRAS_MAX = 5000
AWG_MIN = 8
AWG_MAX = 36

MSG_VISAO_UI = (
    "A IA não conseguiu identificar a escala ou as ranhuras com segurança. "
    "Por favor, preencha os dados manualmente abaixo."
)


def validate_demo_submit(
    *,
    modo_op: str,
    diametro_mm: float,
    pacote_mm: float,
    ranhuras: int,
    tensao_v: float | None,
    esp_eng: str,
    fio_eng: str,
    polos: int = 0,
    has_stator_images: bool = False,
) -> list[str]:
    """
    Sanity check antes de chamar motor / API.
    Retorna lista de mensagens (vazia = OK).
    """
    errors: list[str] = []

    if diametro_mm <= 0:
        errors.append("Diâmetro interno deve ser maior que zero (mm).")
    elif diametro_mm < DIAMETRO_MM_MIN or diametro_mm > DIAMETRO_MM_MAX:
        errors.append(
            f"Diâmetro fora da faixa operacional ({DIAMETRO_MM_MIN:.0f}–{DIAMETRO_MM_MAX:.0f} mm)."
        )

    if pacote_mm <= 0:
        errors.append("Comprimento do pacote deve ser maior que zero (mm).")
    elif pacote_mm < PACOTE_MM_MIN or pacote_mm > PACOTE_MM_MAX:
        errors.append(
            f"Pacote fora da faixa operacional ({PACOTE_MM_MIN:.0f}–{PACOTE_MM_MAX:.0f} mm)."
        )

    if ranhuras < RANHURAS_MIN or ranhuras > RANHURAS_MAX:
        errors.append(f"Ranhuras devem estar entre {RANHURAS_MIN} e {RANHURAS_MAX}.")

    if polos < 0 or polos > POLOS_MAX:
        errors.append(f"Polos inválidos (0 = auto, ou 2–{POLOS_MAX}).")

    if tensao_v is None or tensao_v <= 0:
        errors.append("Informe a tensão de rede (V) antes de executar o gêmeo digital.")
    elif tensao_v < TENSAO_V_MIN or tensao_v > TENSAO_V_MAX:
        errors.append(f"Tensão deve estar entre {TENSAO_V_MIN} e {TENSAO_V_MAX} V.")

    is_caixa = "Caixa preta" in modo_op
    is_auditoria = "Auditoria" in modo_op

    if is_caixa and not has_stator_images and ranhuras <= 0:
        errors.append("Modo caixa preta: envie fotos com escala ou informe o número de ranhuras.")

    if is_auditoria:
        esp = parse_scalar(str(esp_eng).strip()) if str(esp_eng).strip() else None
        if esp is None or esp <= 0:
            errors.append("Modo auditoria: informe as espiras do cálculo suspeito.")
        elif esp > ESPIRAS_MAX:
            errors.append(f"Espiras acima do limite seguro ({ESPIRAS_MAX}).")
        awg = parse_awg_number(str(fio_eng).strip()) if str(fio_eng).strip() else None
        if awg is None:
            errors.append("Modo auditoria: informe a bitola AWG do cálculo suspeito.")
        elif awg < AWG_MIN or awg > AWG_MAX:
            errors.append(f"AWG deve estar entre {AWG_MIN} e {AWG_MAX}.")

    return errors


def vision_needs_manual_fallback(visao: dict[str, Any] | None) -> bool:
    if not visao:
        return False
    from services.stator_vision_ingest import (
        VISION_MIN_CONFIDENCE,
        normalize_vision_response,
    )

    v = normalize_vision_response(visao)
    try:
        conf = float(v.get("confianca_visao") or 0)
    except (TypeError, ValueError):
        conf = 0.0
    return bool(
        v.get("visao_ilegivel")
        or v.get("exige_entrada_manual")
        or conf < VISION_MIN_CONFIDENCE
    )
