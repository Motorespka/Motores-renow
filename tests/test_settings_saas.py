#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import os

import pytest

from config.settings import AppEnvironment, get_settings, reload_settings


def test_settings_development_default(monkeypatch):
    monkeypatch.delenv("APP_ENV", raising=False)
    monkeypatch.setenv("APP_ENV", "development")
    reload_settings()
    s = get_settings()
    assert s.app_env == AppEnvironment.DEVELOPMENT
    assert s.database_url.startswith("sqlite")
    safe = s.to_safe_dict()
    assert "gemini_keys_count" in safe
    assert safe["app_env"] == "development"


def test_settings_production_env(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg2://u:p@localhost/db")
    reload_settings()
    s = get_settings()
    assert s.app_env == AppEnvironment.PRODUCTION
    assert s.is_production
    assert "postgresql" in s.database_url


def test_saas_database_sqlite(tmp_path, monkeypatch):
    db_path = tmp_path / "test_saas.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    reload_settings()

    from saas.database import (
        bootstrap_saas_database,
        get_or_create_user,
        get_saas_engine,
        log_calculation_history,
        log_user_access,
    )

    get_saas_engine.cache_clear()
    bootstrap_saas_database()
    user = get_or_create_user(username="tester", email="t@test.com", plano="pro")
    assert user.plano_assinatura == "pro"
    log_user_access(username="tester", pagina="demo_calculo")
    hid = log_calculation_history(
        username="tester",
        modo="caixa_preta",
        entrada={"d": 80},
        resultado={"ok": True},
    )
    assert hid >= 1
