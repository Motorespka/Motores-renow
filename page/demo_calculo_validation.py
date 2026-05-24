#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validação de inputs do formulário Demo Cálculo (Fase 3 — caminho infeliz)."""

from __future__ import annotations

import re
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


def parse_tensao_rede(raw: Any) -> tuple[list[float], str]:
    """
    Interpreta tensão simples ou múltipla: 220, 110/220/380, 220-380-440, etc.
    Retorna (lista ordenada sem duplicatas, texto normalizado para exibição).
    """
    s = str(raw or "").strip()
    if not s:
        return [], ""
    s = (
        s.replace(",", ".")
        .replace("\\", "/")
        .replace("\u2215", "/")
        .replace("\uff0f", "/")
    )
    parts = re.split(r"[/\s;\-,]+", s)
    volts: list[float] = []
    for part in parts:
        token = part.strip().rstrip("Vv")
        if not token:
            continue
        try:
            v = float(token)
        except ValueError:
            continue
        if 24 <= v <= 15000:
            volts.append(v)
    if not volts:
        return [], s
    dedup = sorted(set(volts))
    display = "/".join(
        str(int(v)) if abs(v - int(v)) < 1e-6 else f"{v:g}" for v in dedup
    )
    return dedup, display


def primary_voltage_for_physics(
    voltages: list[float],
    *,
    tipo_motor: str = "TRIFASICO",
) -> float:
    """Escolhe uma tensão nominal para FEM / J / B quando há dupla ou tripla tensão."""
    if not voltages:
        return 220.0
    if len(voltages) == 1:
        return float(voltages[0])
    if tipo_motor == "MONOFASICO":
        for pref in (220, 127, 110, 240):
            if pref in voltages:
                return float(pref)
        return float(min(voltages))
    for pref in (380, 440, 220, 110):
        if pref in voltages:
            return float(pref)
    return float(max(voltages))


def validate_demo_submit(
    *,
    modo_op: str,
    diametro_mm: float,
    pacote_mm: float,
    ranhuras: int,
    tensao_raw: str = "",
    tensao_v: float | None = None,
    esp_eng: str,
    fio_eng: str,
    polos: int = 0,
    has_stator_images: bool = False,
    tipo_motor: str = "TRIFASICO",
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

    tensoes_parsed, _ = parse_tensao_rede(tensao_raw) if tensao_raw else ([], "")
    if tensao_v is None and tensoes_parsed:
        tensao_v = primary_voltage_for_physics(tensoes_parsed, tipo_motor=tipo_motor)

    if tensao_raw and not tensoes_parsed:
        errors.append(
            "Tensão de rede inválida. Use um valor (220) ou vários separados por / "
            "(ex.: 110/220/380 ou 220/380/440)."
        )
    elif tensao_v is None or tensao_v <= 0:
        errors.append("Informe a tensão de rede (V) antes de executar o gêmeo digital.")
    else:
        tensoes = tensoes_parsed if tensoes_parsed else [float(tensao_v)]
        for v in tensoes:
            if v < TENSAO_V_MIN or v > TENSAO_V_MAX:
                errors.append(
                    f"Tensão {v:.0f} V fora da faixa operacional ({TENSAO_V_MIN:.0f}–{TENSAO_V_MAX:.0f} V)."
                )
                break

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
