#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Design system — tokens para frontend Next."""

from __future__ import annotations

from fastapi import APIRouter

from app.design.digital_twin_tokens import get_digital_twin_tokens

router = APIRouter(prefix="/design", tags=["design"])


@router.get("/digital-twin-tokens")
def digital_twin_tokens() -> dict:
    """Tokens PMTH Digital Twin (cores, tipografia, limites físicos de exibição)."""
    return get_digital_twin_tokens()
