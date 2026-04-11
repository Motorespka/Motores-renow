from __future__ import annotations

from typing import Any

import streamlit as st

from core.feature_flags import FeatureFlags


DEV_MODE_KEY = "dev_mode"
DEV_MODE_ACTOR_KEY = "dev_mode_actor"


def is_dev_mode() -> bool:
    return bool(st.session_state.get(DEV_MODE_KEY, False))


def set_dev_mode(enabled: bool, actor: str = "") -> None:
    st.session_state[DEV_MODE_KEY] = bool(enabled)
    st.session_state[DEV_MODE_ACTOR_KEY] = str(actor or "").strip()


def ensure_dev_mode_access(is_admin: bool) -> None:
    if is_admin:
        return
    if is_dev_mode():
        st.session_state[DEV_MODE_KEY] = False
        st.session_state.pop(DEV_MODE_ACTOR_KEY, None)


def resolve_client_ip() -> str:
    try:
        headers = dict(getattr(st.context, "headers", {}) or {})
    except Exception:
        headers = {}
    if not isinstance(headers, dict):
        return ""

    for key in ["x-forwarded-for", "cf-connecting-ip", "x-real-ip", "remote-addr"]:
        value = headers.get(key) or headers.get(key.title())
        if not value:
            continue
        text = str(value).split(",")[0].strip()
        if text:
            return text
    return ""


def render_dev_banner_if_needed(flags: FeatureFlags) -> None:
    if not flags.enable_dev_banner:
        return
    if not is_dev_mode():
        return

    actor = str(st.session_state.get(DEV_MODE_ACTOR_KEY) or "").strip()
    actor_line = f"<span>Responsavel: {actor}</span>" if actor else "<span>Responsavel: sessao atual</span>"
    st.markdown(
        f"""
        <div class="dev-mode-banner">
            <strong>MODO DEVELOPMENT</strong>
            <span>AMBIENTE DE TESTE</span>
            {actor_line}
        </div>
        """,
        unsafe_allow_html=True,
    )


def use_isolated_mode_for_module(client: Any) -> bool:
    if is_dev_mode():
        return True
    return bool(getattr(client, "is_local_runtime", False))

