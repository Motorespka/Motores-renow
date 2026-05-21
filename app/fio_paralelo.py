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

# Regra rigorosa de bancada: 2×(N) AWG ≡ 1×(N−3) AWG  →  fios em paralelo = single + 3
PARALLEL_STRAND_DELTA = 3

# Tabela obrigatória: (n_paralelo, awg_fio) -> awg_equivalente_unico
_EQUIVALENCE_CANONICAL: dict[tuple[int, int], int] = {
    (2, 22): 19,
    (2, 20): 17,
    (2, 18): 15,
    (2, 23): 20,
    (2, 21): 18,
    (2, 24): 21,
    (2, 25): 22,
}

# Inverso: single -> (n, strand_awg)
_SINGLE_TO_PARALLEL: dict[int, tuple[int, int]] = {
    19: (2, 22),
    17: (2, 20),
    15: (2, 18),
}

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


def get_equivalent_wire(single_awg: float, parallel_count: int = 2) -> WireConfig:
    """
    Equivalência AWG regra N-3 nos fios em paralelo (2×N ≡ 1×(N-3)):
    1×19 ≡ 2×22; 1×17 ≡ 2×20; 1×15 ≡ 2×18 — nunca 2×20 = 1×14.
    """
    single_i = int(round(single_awg))
    if parallel_count <= 1:
        return WireConfig(parallel_count=1, awg=float(single_i))
    if parallel_count == 2:
        if single_i in _SINGLE_TO_PARALLEL:
            n, strand = _SINGLE_TO_PARALLEL[single_i]
            return WireConfig(parallel_count=n, awg=float(strand))
        strand_i = single_i + PARALLEL_STRAND_DELTA
        if strand_i > 22:
            return WireConfig(parallel_count=1, awg=float(single_i))
        return WireConfig(parallel_count=2, awg=float(strand_i))
    return WireConfig(parallel_count=1, awg=float(single_i))


def get_single_from_parallel(parallel_awg: float, parallel_count: int = 2) -> float:
    """Inverso rigoroso: 2×22 → 1×19 (regra N-3)."""
    if parallel_count <= 1:
        return round(parallel_awg, 1)
    p_int = int(round(parallel_awg))
    key = (parallel_count, p_int)
    if key in _EQUIVALENCE_CANONICAL:
        return float(_EQUIVALENCE_CANONICAL[key])
    if parallel_count == 2:
        return float(max(14, p_int - PARALLEL_STRAND_DELTA))
    return round(parallel_awg - PARALLEL_STRAND_DELTA, 1)


def _parallel_respects_n_minus_3(cfg: WireConfig, target_single_awg: float) -> bool:
    """Valida que paralelo obedece 2×N ≡ 1×(N-3) — nunca 2×20 = 1×14."""
    if cfg.parallel_count <= 1:
        return True
    canonical = get_equivalent_wire(target_single_awg, cfg.parallel_count)
    eq = get_single_from_parallel(cfg.awg, cfg.parallel_count)
    if cfg.parallel_count == 2 and int(round(cfg.awg)) == 20 and eq <= 15:
        return False
    return (
        cfg.parallel_count == canonical.parallel_count
        and int(round(cfg.awg)) == int(canonical.awg)
        and abs(eq - target_single_awg) <= 0.6
    )


def parallel_from_single_awg(single_awg: float, parallel_count: int = 2) -> WireConfig:
    return get_equivalent_wire(single_awg, parallel_count)


def parse_wire_config(raw: str) -> Optional[WireConfig]:
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


def equivalent_single_awg(config: WireConfig) -> float:
    if config.parallel_count <= 1:
        return round(config.awg, 1)
    return get_single_from_parallel(config.awg, config.parallel_count)


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
    """Escolhe configuração de fio; paralelo sempre pela regra N-3 de bancada."""
    target_area = awg_to_mm2(target_awg)
    base = WireConfig(parallel_count=1, awg=round(target_awg, 1))
    stats = _catalog_parallel_stats(fio_samples)

    if stats:
        if prefer_parallel:
            parallel_stats = [(k, c) for k, c in stats.items() if k[0] > 1]
            if parallel_stats:
                best_key, _ = max(parallel_stats, key=lambda x: x[1])
                cand = WireConfig(parallel_count=best_key[0], awg=best_key[1])
                if _parallel_respects_n_minus_3(cand, target_awg):
                    return cand
        best_key, _ = stats.most_common(1)[0]
        best = WireConfig(parallel_count=best_key[0], awg=best_key[1])
        if best.parallel_count <= 1 and _area_close(best.total_area_mm2, target_area):
            return best
        if best.parallel_count > 1 and _parallel_respects_n_minus_3(best, target_awg):
            return best

    if prefer_parallel and target_awg >= 14:
        canonical = get_equivalent_wire(target_awg, 2)
        if canonical.parallel_count > 1:
            return canonical

    return base


def format_wire_suggestion(espiras: float, config: WireConfig) -> str:
    esp_i = int(espiras) if abs(espiras - int(espiras)) < 1e-6 else round(espiras, 1)
    if config.parallel_count <= 1:
        return f"Sugestão: {esp_i} espiras, {config.label()}"
    equiv = equivalent_single_awg(config)
    equiv_i = int(equiv) if abs(equiv - int(equiv)) < 1e-6 else equiv
    return (
        f"Sugestão: {esp_i} espiras, {config.label()} "
        f"(Equivalente a 1x {equiv_i} AWG)"
    )


THICK_WIRE_AWG_MAX = 19


def parallel_alternative_for_single(single_awg: float) -> Optional[WireConfig]:
    if single_awg <= 0 or single_awg > THICK_WIRE_AWG_MAX:
        return None
    return get_equivalent_wire(single_awg, 2)


def wire_display_options(
    espiras: float,
    single_awg: float,
) -> dict[str, str]:
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
