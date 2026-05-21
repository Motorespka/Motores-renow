#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sessão e operações de persistência SaaS."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from sqlalchemy.orm import Session

from config.settings import get_settings
from saas.models import (
    AccessLog,
    CalculationHistory,
    TenantUser,
    create_engine_from_url,
    init_db,
)


@lru_cache(maxsize=1)
def get_saas_engine():
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    engine = create_engine_from_url(settings.database_url)
    init_db(engine)
    return engine


def bootstrap_saas_database() -> None:
    get_saas_engine()


def get_or_create_user(
    *,
    username: str,
    email: str = "",
    plano: str = "free",
) -> TenantUser:
    engine = get_saas_engine()
    with Session(engine) as session:
        user = session.query(TenantUser).filter_by(username=username).one_or_none()
        if user is None:
            user = TenantUser(username=username, email=email, plano_assinatura=plano)
            session.add(user)
        elif email and not user.email:
            user.email = email
        session.commit()
        return session.query(TenantUser).filter_by(username=username).one()


def log_user_access(
    *,
    username: str,
    pagina: str = "demo_calculo",
    email: str = "",
    plano: str = "free",
) -> int:
    user = get_or_create_user(username=username, email=email, plano=plano)
    engine = get_saas_engine()
    with Session(engine) as session:
        row = AccessLog(id_usuario=user.id_usuario, pagina=pagina)
        session.add(row)
        session.flush()
        return int(row.id)


def log_calculation_history(
    *,
    username: str,
    modo: str,
    entrada: dict[str, Any],
    resultado: dict[str, Any],
    sucesso: bool = True,
    erro: str = "",
    email: str = "",
) -> int:
    user = get_or_create_user(username=username, email=email)
    engine = get_saas_engine()
    with Session(engine) as session:
        row = CalculationHistory(
            id_usuario=user.id_usuario,
            modo=modo,
            plano_no_momento=user.plano_assinatura,
            entrada_json=json.dumps(entrada, ensure_ascii=False, default=str),
            resultado_json=json.dumps(resultado, ensure_ascii=False, default=str),
            sucesso=sucesso,
            mensagem_erro=erro,
        )
        session.add(row)
        session.flush()
        return int(row.id)


def get_user_plan(username: str) -> str:
    engine = get_saas_engine()
    with Session(engine) as session:
        user = session.query(TenantUser).filter_by(username=username).one_or_none()
        return user.plano_assinatura if user else "free"


def update_user_plan(username: str, plano: str) -> None:
    engine = get_saas_engine()
    with Session(engine) as session:
        user = session.query(TenantUser).filter_by(username=username).one_or_none()
        if user:
            user.plano_assinatura = plano
