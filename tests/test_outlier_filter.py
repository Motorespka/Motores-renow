#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine.outlier_filter import (  # noqa: E402
    filter_outliers_bussola_zscore_band,
    filter_outliers_median_band,
    robust_historical_median,
    should_exclude_cadastro_pollution_80_90,
)


def test_bussola_zscore_band_removes_contamination():
    vals = [42.0, 44.0, 41.0, 8.0, 43.0]
    cleaned = filter_outliers_bussola_zscore_band(vals)
    assert 8.0 not in cleaned
    assert len(cleaned) >= 4


def test_outlier_filter_removes_2_pole_contamination():
    vals = [42.0, 44.0, 41.0, 8.0, 43.0]
    cleaned = filter_outliers_median_band(vals)
    assert 8.0 not in cleaned
    assert len(cleaned) >= 4


def test_robust_median_ignores_low_outlier():
    med, n_total, n_clean = robust_historical_median([42, 44, 41, 8, 43])
    assert n_total == 5
    assert n_clean == 4
    assert med is not None
    assert 40 <= med <= 45


def test_pollution_excludes_80_90_below_20_espiras():
    assert should_exclude_cadastro_pollution_80_90("80A", 8.0)
    assert should_exclude_cadastro_pollution_80_90("90", 19.0)
    assert not should_exclude_cadastro_pollution_80_90("80B", 22.0)
    assert not should_exclude_cadastro_pollution_80_90("132", 8.0)
