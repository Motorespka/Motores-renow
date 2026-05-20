#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.search_lib import passo_canonical  # noqa: E402
from app.topologia_bobinagem import correction_factor, norm_tipo_bobinagem, tipo_exact_match  # noqa: E402


def test_norm_topologia():
    assert norm_tipo_bobinagem("3 e 3") == "TRES_E_TRES"
    assert norm_tipo_bobinagem("Imbricado") == "IMBRICADO"
    assert norm_tipo_bobinagem("Concêntrico") == "CONCENTRICO"


def test_passo_vs_topologia():
    assert passo_canonical("10-12") == "10-12"
    assert not tipo_exact_match("IMBRICADO", "TRES_E_TRES")


def test_correction_factor():
    assert correction_factor("IMBRICADO", "TRES_E_TRES") < 1.0
    assert correction_factor("IMBRICADO", "IMBRICADO") == 1.0
