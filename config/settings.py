#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuração centralizada — credenciais via .env / variáveis de ambiente (nunca no Git).
Suporta DESENVOLVIMENTO, STAGING e PRODUÇÃO.
"""

from __future__ import annotations

import json
import os
from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

_REPO_ROOT = Path(__file__).resolve().parents[1]


class AppEnvironment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv(_REPO_ROOT / ".env", override=False)
        env_name = (os.environ.get("APP_ENV") or "development").strip().lower()
        load_dotenv(_REPO_ROOT / f".env.{env_name}", override=False)
    except ImportError:
        pass


def _streamlit_secret(name: str) -> str:
    try:
        import streamlit as st

        raw = getattr(getattr(st, "secrets", None), "get", lambda _k, _d=None: None)(name)
        if raw is not None and str(raw).strip():
            return str(raw).strip()
    except Exception:
        pass
    return ""


class Settings:
    """Carrega configuração sem expor segredos no código-fonte."""

    def __init__(self) -> None:
        _load_dotenv()
        raw_env = (
            os.environ.get("APP_ENV")
            or os.environ.get("ENVIRONMENT")
            or "development"
        ).strip().lower()
        if raw_env in ("prod", "production"):
            self.app_env = AppEnvironment.PRODUCTION
        elif raw_env in ("stage", "staging"):
            self.app_env = AppEnvironment.STAGING
        else:
            self.app_env = AppEnvironment.DEVELOPMENT

        self.app_name = os.environ.get("APP_NAME", "gemeo-digital-moto-renow")
        self.debug = self._bool("DEBUG", default=self.app_env == AppEnvironment.DEVELOPMENT)

        # Banco SaaS (PostgreSQL em produção; SQLite local em dev)
        self.database_url = self._secret(
            "DATABASE_URL",
            default=f"sqlite:///{(_REPO_ROOT / 'data' / 'saas.db').as_posix()}",
        )

        # Supabase (auth existente do app)
        self.supabase_url = self._secret("SUPABASE_URL")
        self.supabase_anon_key = self._secret("SUPABASE_ANON_KEY", "SUPABASE_KEY")
        self.supabase_service_role_key = self._secret("SUPABASE_SERVICE_ROLE_KEY")

        # Gemini — nunca hardcoded
        self.gemini_model_primary = self._secret(
            "GEMINI_MODEL_DEFAULT",
            "GEMINI_MODEL",
            default="gemini-2.5-flash",
        )
        self.gemini_model_fallback = self._secret(
            "GEMINI_MODEL_FALLBACK",
            default="gemini-2.5-flash-lite",
        )
        self.gemini_max_calls_per_key = int(os.environ.get("GEMINI_MAX_CALLS_PER_KEY_PER_RUN", "0") or "0")
        self.gemini_status_path = Path(
            self._secret(
                "GEMINI_STATUS_PATH",
                default=str(_REPO_ROOT / "logs" / "gemini_keys_status.json"),
            )
        )

        # Auth SaaS (streamlit-authenticator) — camada adicional ao Supabase
        self.saas_streamlit_auth_enabled = self._bool(
            "SAAS_STREAMLIT_AUTH_ENABLED",
            default=False,
        )
        self.auth_credentials_path = Path(
            self._secret(
                "AUTH_CREDENTIALS_PATH",
                default=str(_REPO_ROOT / "config" / "auth_credentials.yaml"),
            )
        )
        self.auth_cookie_key = self._secret("AUTH_COOKIE_KEY", default="mrw_saas_cookie_key_change_me")

        # Logs
        self.log_level = self._secret("LOG_LEVEL", default="INFO").upper()
        self.log_dir = Path(self._secret("LOG_DIR", default=str(_REPO_ROOT / "logs")))
        self.log_json_sink = self._bool("LOG_JSON", default=self.is_production)
        self.log_audit_calculations = self._bool("LOG_AUDIT_CALCULATIONS", default=True)

        # Paths de dados
        self.data_dir = Path(self._secret("DATA_DIR", default=str(_REPO_ROOT / "data")))
        self.oficial_search_db = Path(
            self._secret(
                "OFICIAL_SEARCH_DB",
                default=str(_REPO_ROOT / "data" / "oficial_search.sqlite"),
            )
        )

    def _bool(self, name: str, *, default: bool = False) -> bool:
        v = self._secret(name, default="")
        if not v:
            return default
        return v.lower() in {"1", "true", "yes", "on"}

    def _secret(self, name: str, *aliases: str, default: str = "") -> str:
        for key in (name, *aliases):
            v = (os.environ.get(key) or "").strip()
            if v:
                return v
            sv = _streamlit_secret(key)
            if sv:
                return sv
        return default

    @property
    def is_production(self) -> bool:
        return self.app_env == AppEnvironment.PRODUCTION

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    def gemini_api_keys(self) -> list[str]:
        """Coleta chaves GEMINI_* do ambiente (sem valores no código)."""
        try:
            from services.gemini_key_manager import GeminiKeyManager

            pairs = GeminiKeyManager(enabled=False).load_keys_from_env_and_secrets()
            keys = [k for _a, k in pairs if k]
            if keys:
                return keys
        except Exception:
            pass
        single = self._secret("GEMINI_API_KEY")
        return [single] if single else []

    def to_safe_dict(self) -> dict[str, Any]:
        return {
            "app_env": self.app_env.value,
            "app_name": self.app_name,
            "debug": self.debug,
            "database_url": "***" if "@" in self.database_url else self.database_url,
            "gemini_keys_count": len(self.gemini_api_keys()),
            "gemini_model_primary": self.gemini_model_primary,
            "saas_streamlit_auth_enabled": self.saas_streamlit_auth_enabled,
            "log_level": self.log_level,
        }


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def reload_settings() -> Settings:
    get_settings.cache_clear()
    try:
        from saas.database import get_saas_engine

        get_saas_engine.cache_clear()
    except Exception:
        pass
    return get_settings()
