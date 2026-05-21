#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gate de acesso ao Gêmeo Digital / demo cálculo.
Combina Supabase (existente) + streamlit-authenticator (SaaS local/Docker).
"""

from __future__ import annotations

from typing import Any, Optional

import streamlit as st

from config.settings import get_settings
from core.logging_config import get_logger


def _session_username() -> str:
    for key in ("username", "user_email", "user_id"):
        v = st.session_state.get(key)
        if v:
            return str(v)
    return ""


def _session_email() -> str:
    return str(st.session_state.get("user_email") or st.session_state.get("email") or "")


def is_supabase_authenticated() -> bool:
    return bool(
        st.session_state.get("authenticated")
        or st.session_state.get("user_id")
        or st.session_state.get("access_token")
    )


def _run_streamlit_authenticator() -> bool:
    settings = get_settings()
    if not settings.saas_streamlit_auth_enabled:
        return False
    cred_path = settings.auth_credentials_path
    if not cred_path.is_file():
        st.error(
            f"Auth SaaS ativo, mas arquivo de credenciais ausente: `{cred_path}`. "
            "Copie `config/auth_credentials.yaml.example` e configure senhas com bcrypt."
        )
        return False
    try:
        import yaml
        import streamlit_authenticator as stauth
    except ImportError:
        st.error("Instale: `pip install streamlit-authenticator PyYAML`")
        return False

    with cred_path.open(encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    authenticator = stauth.Authenticate(
        config.get("credentials", {}),
        config.get("cookie", {}).get("name", "mrw_saas_auth"),
        settings.auth_cookie_key,
        config.get("cookie", {}).get("expiry_days", 7),
    )
    try:
        authenticator.login(location="main", key="saas_gemelo_login")
    except TypeError:
        authenticator.login("main", key="saas_gemelo_login")

    auth_status = st.session_state.get("authentication_status")
    if auth_status is True:
        name = st.session_state.get("name") or ""
        username = st.session_state.get("username") or ""
        st.session_state["username"] = username
        st.session_state["authenticated"] = True
        if name:
            st.caption(f"Sessão: {name} ({username})")
        return True
    if auth_status is False:
        st.error("Usuário ou senha inválidos.")
    elif auth_status is None:
        st.info("Faça login para acessar o Gêmeo Digital.")
    return False


def require_gemelo_digital_access(
    feature_name: str = "Gêmeo Digital",
    client: Any | None = None,
) -> bool:
    """
    Retorna True se o usuário pode usar a página de cálculo.
    Em produção com SAAS_STREAMLIT_AUTH_ENABLED=true exige login explícito.
    Caso contrário, delega ao require_admin_access existente (Supabase/planos).
    """
    settings = get_settings()
    log = get_logger()

    if settings.saas_streamlit_auth_enabled:
        if _run_streamlit_authenticator():
            from saas.database import log_user_access

            uname = str(st.session_state.get("username") or "anon")
            try:
                log_user_access(username=uname, pagina="demo_calculo", email=_session_email())
            except Exception as exc:
                log.warning("Falha ao registrar acesso SaaS: {}", exc)
            return True
        st.stop()
        return False

    if is_supabase_authenticated():
        from core.access_control import require_paid_access
        from saas.database import log_user_access

        if not require_paid_access(feature_name, client=client):
            return False
        uname = _session_username() or "supabase_user"
        try:
            log_user_access(
                username=uname,
                pagina="demo_calculo",
                email=_session_email(),
                plano=str(st.session_state.get("user_plan") or "pro"),
            )
        except Exception:
            pass
        return True

    try:
        from core.access_control import require_paid_access

        return bool(require_paid_access(feature_name, client=client))
    except Exception as exc:
        log.error("Gate de acesso falhou: {}", exc)
        st.error("Não foi possível validar seu acesso. Tente novamente ou contate o suporte.")
        st.stop()
        return False


def current_actor() -> dict[str, str]:
    return {
        "username": str(st.session_state.get("username") or _session_username() or "anon"),
        "email": _session_email(),
        "plan": str(st.session_state.get("user_plan") or get_settings().app_env.value),
    }
