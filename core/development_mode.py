from __future__ import annotations

import os
import re
import uuid
from typing import Any

import streamlit as st

from core.feature_flags import FeatureFlags


DEV_MODE_KEY = "dev_mode"
DEV_MODE_ACTOR_KEY = "dev_mode_actor"
DEV_SANDBOX_ID_KEY = "dev_sandbox_id"
DEV_SANDBOX_DB_PATH_KEY = "dev_sandbox_db_path"
DEV_SANDBOX_ROOT = os.path.join("data", "dev_sandboxes")
DEV_LOCAL_STATE_PREFIXES = (
    "_comercial_local_",
    "_live_update_last_full_rerun_",
)
DEV_LOCAL_STATE_KEYS = (
    "_feature_flags_overrides",
    "_service_role_client",
    "_service_role_client_key",
)


def is_dev_mode() -> bool:
    return bool(st.session_state.get(DEV_MODE_KEY, False))


def _sanitize_token(value: str) -> str:
    raw = str(value or "").strip().lower()
    if not raw:
        return ""
    token = re.sub(r"[^a-z0-9_-]", "", raw)
    return token[:40]


def resolve_dev_sandbox_id() -> str:
    existing = _sanitize_token(st.session_state.get(DEV_SANDBOX_ID_KEY))
    if existing:
        return existing

    seed = _sanitize_token(st.session_state.get("_browser_cache_key"))
    if len(seed) < 8:
        seed = uuid.uuid4().hex[:24]
    st.session_state[DEV_SANDBOX_ID_KEY] = seed
    return seed


def resolve_dev_sandbox_db_path() -> str:
    sandbox_id = resolve_dev_sandbox_id()
    os.makedirs(DEV_SANDBOX_ROOT, exist_ok=True)
    path = os.path.abspath(os.path.join(DEV_SANDBOX_ROOT, f"{sandbox_id}.db"))
    st.session_state[DEV_SANDBOX_DB_PATH_KEY] = path
    return path


def cleanup_dev_sandbox_state(remove_db: bool = True) -> None:
    db_path = str(st.session_state.get(DEV_SANDBOX_DB_PATH_KEY) or "").strip()

    for key in list(st.session_state.keys()):
        if any(str(key).startswith(prefix) for prefix in DEV_LOCAL_STATE_PREFIXES):
            st.session_state.pop(key, None)

    for key in DEV_LOCAL_STATE_KEYS:
        st.session_state.pop(key, None)

    st.session_state.pop(DEV_SANDBOX_ID_KEY, None)
    st.session_state.pop(DEV_SANDBOX_DB_PATH_KEY, None)

    if remove_db and db_path:
        try:
            if os.path.isfile(db_path):
                os.remove(db_path)
        except Exception:
            pass


def set_dev_mode(enabled: bool, actor: str = "") -> None:
    is_enabled = bool(enabled)
    if is_enabled:
        if not is_dev_mode():
            cleanup_dev_sandbox_state(remove_db=True)
        st.session_state[DEV_MODE_KEY] = True
        st.session_state[DEV_MODE_ACTOR_KEY] = str(actor or "").strip()
        resolve_dev_sandbox_db_path()
        return

    cleanup_dev_sandbox_state(remove_db=True)
    st.session_state[DEV_MODE_KEY] = False
    st.session_state.pop(DEV_MODE_ACTOR_KEY, None)


def ensure_dev_mode_access(is_admin: bool) -> None:
    if is_admin:
        return
    if is_dev_mode():
        set_dev_mode(False, actor="system")


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

