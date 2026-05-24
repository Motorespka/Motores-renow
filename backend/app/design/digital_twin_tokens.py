#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tokens do Gêmeo Digital — fonte única para API e frontend."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_TOKENS_FILE = _REPO_ROOT / "design-system" / "digital-twin-tokens.json"


@lru_cache(maxsize=1)
def get_digital_twin_tokens() -> dict:
    if not _TOKENS_FILE.is_file():
        return {}
    return json.loads(_TOKENS_FILE.read_text(encoding="utf-8"))
