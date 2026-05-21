#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Auditoria unificada — loguru + banco SaaS."""

from __future__ import annotations

from typing import Any

from config.settings import get_settings
from core.logging_config import log_calculation_event
from saas.auth_guard import current_actor
from saas.database import log_calculation_history


def record_calculation(
    *,
    modo: str,
    entrada: dict[str, Any],
    resultado_resumo: dict[str, Any],
    sucesso: bool = True,
    erro: str = "",
) -> None:
    settings = get_settings()
    actor = current_actor()
    if settings.log_audit_calculations:
        log_calculation_event(
            user_id=actor["username"],
            username=actor["username"],
            modo=modo,
            entrada=entrada,
            resultado_resumo=resultado_resumo,
            sucesso=sucesso,
            erro=erro,
        )
    try:
        log_calculation_history(
            username=actor["username"],
            email=actor["email"],
            modo=modo,
            entrada=entrada,
            resultado=resultado_resumo,
            sucesso=sucesso,
            erro=erro,
        )
    except Exception:
        pass
