#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Equivalência de seção transversal e sugestão de fios em paralelo (AWG)."""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from statistics import median
from typing import Optional

from app.search_lib import awg_from_mm2, awg_to_mm2, parse_awg_number

_RE_PARALLEL = re.compile(
    r"(?P<n>\d+)\s*[x×/]\s*(?P<awg>\d+(?:[.,]\d+)?)|"
    r"(?P<awg2>\d+(?:[.,]\d+)?)\s*[x×/]\s*(?P<n2>\d+)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class WireConfig:
    parallel_count: int
    awg: float

    @property
    def total_area_mm2(self) -> float:
        return self.parallel_count * awg_to_mm2(self.awg)

    def label(self) -> str:
        awg_i = int(self.awg) if abs(self.awg - int(self.awg)) < 1e-6 else self.awg
        if self.parallel_count <= 1:
            return f"1x {awg_i} AWG"
        return f"{self.parallel_count}x {awg_i} AWG"


def parse_wire_config(raw: str) -> Optional[WireConfig]:
    """Interpreta '23', '2x22', '2 x 23 AWG', etc."""
    s = (raw or "").strip()
    if not s:
        return None
    m = _RE_PARALLEL.search(s)
    if m:
        if m.group("n"):
            n = int(m.group("n"))
            awg = float(m.group("awg").replace(",", "."))
        else:
            n = int(m.group("n2"))
            awg = float(m.group("awg2").replace(",", "."))
        if n > 0 and awg > 0:
            return WireConfig(parallel_count=n, awg=round(awg, 1))
    awg = parse_awg_number(s)
    if awg is None:
        return None
    return WireConfig(parallel_count=1, awg=round(awg, 1))


def single_awg_from_area(area_mm2: float) -> Optional[float]:
    return awg_from_mm2(area_mm2)


def equivalent_single_awg(config: WireConfig) -> float:
    eq = single_awg_from_area(config.total_area_mm2)
    return round(eq if eq is not None else config.awg, 1)


def parallel_from_single_awg(single_awg: float, parallel_count: int = 2) -> WireConfig:
    """
    Regra prática de bancada: 1x(N) ≈ 2x(N+3) em área aproximada
    (ex.: 1x19 AWG ≈ 2x22 AWG).
    """
    return WireConfig(
        parallel_count=parallel_count,
        awg=round(single_awg + 3.0, 1),
    )


def _area_close(a: float, b: float, tol: float = 0.08) -> bool:
    if a <= 0 or b <= 0:
        return False
    return abs(a - b) / max(a, b) <= tol


def _catalog_parallel_stats(fio_samples: list[str]) -> Counter[tuple[int, float]]:
    counts: Counter[tuple[int, float]] = Counter()
    for raw in fio_samples:
        cfg = parse_wire_config(raw)
        if cfg:
            counts[(cfg.parallel_count, cfg.awg)] += 1
    return counts


def choose_wire_config(
    target_awg: float,
    fio_samples: list[str],
    *,
    prefer_parallel: bool = True,
) -> WireConfig:
    """
    Escolhe configuração determinística (mediana + moda do acervo).
    Prioriza paralelo se for padrão estatístico ou equivalente clássico 1x/2x.
    """
    target_area = awg_to_mm2(target_awg)
    base = WireConfig(parallel_count=1, awg=round(target_awg, 1))
    stats = _catalog_parallel_stats(fio_samples)

    if stats:
        if prefer_parallel:
            parallel_stats = [(k, c) for k, c in stats.items() if k[0] > 1]
            if parallel_stats:
                best_key, _ = max(parallel_stats, key=lambda x: x[1])
                return WireConfig(parallel_count=best_key[0], awg=best_key[1])
        best_key, _ = stats.most_common(1)[0]
        best = WireConfig(parallel_count=best_key[0], awg=best_key[1])
        if _area_close(best.total_area_mm2, target_area):
            return best

    if prefer_parallel and target_awg >= 17:
        return parallel_from_single_awg(target_awg, 2)

    return base


def format_wire_suggestion(espiras: float, config: WireConfig) -> str:
    esp_i = int(espiras) if abs(espiras - int(espiras)) < 1e-6 else round(espiras, 1)
    equiv = equivalent_single_awg(config)
    equiv_i = int(equiv) if abs(equiv - int(equiv)) < 1e-6 else equiv
    if config.parallel_count <= 1:
        return f"Sugestão: {esp_i} espiras, {config.label()}"
    return (
        f"Sugestão: {esp_i} espiras, {config.label()} "
        f"(Equivalente a 1x {equiv_i} AWG)"
    )


# AWG <= 19: fio grosso — sempre oferecer alternativa 2x(N+3) na interface
THICK_WIRE_AWG_MAX = 19


def parallel_alternative_for_single(single_awg: float) -> Optional[WireConfig]:
    """Alternativa em paralelo para fio grosso (ex.: 1x19 → 2x22)."""
    if single_awg <= 0 or single_awg > THICK_WIRE_AWG_MAX:
        return None
    return parallel_from_single_awg(single_awg, 2)


def wire_display_options(
    espiras: float,
    single_awg: float,
) -> dict[str, str]:
    """
    Retorna textos para UI: configuração principal (matemática) e alternativa em paralelo.
    """
    single_cfg = WireConfig(parallel_count=1, awg=round(single_awg, 1))
    principal = format_wire_suggestion(espiras, single_cfg)
    par_cfg = parallel_alternative_for_single(single_awg)
    alternativa = ""
    if par_cfg is not None:
        alternativa = format_wire_suggestion(espiras, par_cfg)
    return {
        "principal": principal,
        "alternativa_paralelo": alternativa,
        "tem_alternativa_paralelo": bool(alternativa),
    }


def median_target_awg(awg_values: list[float]) -> Optional[float]:
    vals = sorted(v for v in awg_values if v is not None and v > 0)
    if not vals:
        return None
    return round(median(vals), 1)
