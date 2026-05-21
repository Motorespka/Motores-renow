#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Observabilidade — loguru com rastreio de cálculos e erros críticos."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from config.settings import Settings

_CONFIGURED = False


def setup_logging(settings: Optional["Settings"] = None) -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    from config.settings import get_settings

    cfg = settings or get_settings()
    try:
        from loguru import logger
    except ImportError:
        import logging

        logging.basicConfig(level=getattr(logging, cfg.log_level, logging.INFO))
        _CONFIGURED = True
        return

    logger.remove()
    fmt = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan> | "
        "<level>{message}</level>"
    )
    logger.add(sys.stderr, level=cfg.log_level, format=fmt, enqueue=True)

    cfg.log_dir.mkdir(parents=True, exist_ok=True)
    logger.add(
        cfg.log_dir / "app_{time:YYYY-MM-DD}.log",
        level=cfg.log_level,
        rotation="20 MB",
        retention="14 days",
        encoding="utf-8",
        enqueue=True,
    )
    logger.add(
        cfg.log_dir / "errors_{time:YYYY-MM-DD}.log",
        level="ERROR",
        rotation="10 MB",
        retention="30 days",
        encoding="utf-8",
        enqueue=True,
    )
    if cfg.log_json_sink:
        logger.add(
            cfg.log_dir / "audit_{time:YYYY-MM-DD}.jsonl",
            level="INFO",
            serialize=True,
            rotation="25 MB",
            retention="30 days",
            filter=lambda record: record["extra"].get("audit") is True,
            enqueue=True,
        )

    _CONFIGURED = True
    logger.info("Logging iniciado", extra={"audit": True, "env": cfg.app_env.value})


def get_logger():
    try:
        from loguru import logger

        return logger
    except ImportError:
        import logging

        return logging.getLogger("moto_renow")


def log_calculation_event(
    *,
    user_id: str,
    username: str,
    modo: str,
    entrada: dict[str, Any],
    resultado_resumo: dict[str, Any],
    sucesso: bool = True,
    erro: str = "",
) -> None:
    log = get_logger()
    payload = {
        "audit": True,
        "event": "calculation",
        "user_id": user_id,
        "username": username,
        "modo": modo,
        "sucesso": sucesso,
        "erro": erro,
        "entrada": entrada,
        "resultado": resultado_resumo,
    }
    if sucesso:
        log.info("Cálculo gêmeo digital | user={} modo={}", username, modo, extra=payload)
    else:
        log.error(
            "Falha cálculo gêmeo digital | user={} modo={} err={}",
            username,
            modo,
            erro,
            extra=payload,
        )
