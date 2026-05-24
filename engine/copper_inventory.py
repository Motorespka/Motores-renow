#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Estimativa de material (cobre) para rebobinagem — bancada.

Volume ≈ comprimento_total × área_seção; peso = volume × densidade Cu.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

from engine.physics_validator import PhysicsValidator

# Cobre eletrolítico (g/cm³)
COPPER_DENSITY_G_PER_CM3: float = 8.96


def awg_to_diameter_mm(awg: int | float) -> float:
    """Diâmetro nominal do fio (mm) a partir da área AWG (mm²)."""
    area = PhysicsValidator.calculate_wire_area(awg)
    if area <= 0:
        return 0.0
    return round(2.0 * math.sqrt(area / math.pi), 4)


def estimate_mean_turn_length_mm(
    *,
    diametro_estator_mm: float,
    pacote_mm: float,
) -> float:
    """Comprimento médio aproximado de uma espira (mm)."""
    d = max(float(diametro_estator_mm), 1.0)
    p = max(float(pacote_mm), 1.0)
    return round(math.pi * (d + p * 0.35), 2)


def calculate_copper_weight(
    espiras: float,
    n_bobinas: int,
    diametro_fio_mm: float,
    *,
    mean_turn_length_mm: Optional[float] = None,
    diametro_estator_mm: float = 80.0,
    pacote_mm: float = 70.0,
    parallel_count: int = 1,
) -> float:
    """
    Peso aproximado de cobre (kg).

    Args:
        espiras: espiras por bobina (por fase/ranhura conforme convenção da bancada).
        n_bobinas: número de bobinas / grupos de bobina.
        diametro_fio_mm: diâmetro do condutor (mm).
        mean_turn_length_mm: opcional; se omitido, estimado pela geometria do estator.
        parallel_count: condutores em paralelo por ranhura.
    """
    if espiras <= 0 or n_bobinas <= 0 or diametro_fio_mm <= 0:
        return 0.0
    turn_len = mean_turn_length_mm
    if turn_len is None or turn_len <= 0:
        turn_len = estimate_mean_turn_length_mm(
            diametro_estator_mm=diametro_estator_mm,
            pacote_mm=pacote_mm,
        )
    area_mm2 = math.pi * (float(diametro_fio_mm) / 2.0) ** 2
    length_mm = float(espiras) * int(n_bobinas) * float(turn_len)
    volume_mm3 = length_mm * area_mm2 * max(1, int(parallel_count))
    # mm³ → cm³ (÷1000); g = cm³ × 8.96; kg = g/1000
    mass_kg = (volume_mm3 / 1000.0) * COPPER_DENSITY_G_PER_CM3 / 1000.0
    return round(max(0.0, mass_kg), 3)


@dataclass
class CopperMaterialEstimate:
    peso_kg: float
    espiras: float
    n_bobinas: int
    awg: float
    diametro_fio_mm: float
    comprimento_total_m: float
    paralelos: int

    def as_table_row(self) -> dict[str, str]:
        return {
            "Item": "Fio de cobre (estimado)",
            "Especificação": f"{self.espiras:.0f} esp × {self.n_bobinas} bob · "
            f"1×{int(round(self.awg))} AWG (Ø {self.diametro_fio_mm:.2f} mm)",
            "Quantidade": f"{self.peso_kg:.2f} kg",
        }


def estimate_copper_from_winding(
    *,
    espiras: float,
    awg: float,
    ranhuras: int,
    diametro_estator_mm: float,
    pacote_mm: float,
    parallel_count: int = 1,
    ligacao: str = "",
) -> CopperMaterialEstimate:
    """
    Estimativa para UI: n_bobinas ≈ ranhuras / grupos (simplificado trifásico).
    """
    n_bob = max(1, int(ranhuras) // 3) if int(ranhuras) >= 3 else max(1, int(ranhuras))
    d_wire = awg_to_diameter_mm(awg)
    turn_len = estimate_mean_turn_length_mm(
        diametro_estator_mm=diametro_estator_mm,
        pacote_mm=pacote_mm,
    )
    peso = calculate_copper_weight(
        espiras,
        n_bob,
        d_wire,
        mean_turn_length_mm=turn_len,
        parallel_count=parallel_count,
    )
    length_m = round(espiras * n_bob * turn_len / 1000.0 * parallel_count, 2)
    _ = ligacao
    return CopperMaterialEstimate(
        peso_kg=peso,
        espiras=float(espiras),
        n_bobinas=n_bob,
        awg=float(awg),
        diametro_fio_mm=d_wire,
        comprimento_total_m=length_m,
        paralelos=parallel_count,
    )
