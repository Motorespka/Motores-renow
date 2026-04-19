"""Feedback consistente no topo da area principal (apos o header)."""

from __future__ import annotations

from typing import Any, Dict, Optional

import streamlit as st

MRW_BANNER_KEY = "mrw_ui_banner"


def mrw_set_banner(kind: str, message: str) -> None:
    """Define mensagem para o proximo render (sobrescreve a anterior). kind: success|error|warning|info."""
    st.session_state[MRW_BANNER_KEY] = {"kind": str(kind or "info").lower(), "message": str(message or "").strip()}


def mrw_clear_banner() -> None:
    st.session_state.pop(MRW_BANNER_KEY, None)


def mrw_feedback_success(message: str) -> None:
    mrw_set_banner("success", message)
    toast = getattr(st, "toast", None)
    if callable(toast):
        try:
            toast(message, icon="✅")
        except TypeError:
            toast(message)


def mrw_feedback_error(message: str) -> None:
    mrw_set_banner("error", message)
    toast = getattr(st, "toast", None)
    if callable(toast):
        try:
            toast(message, icon="⛔")
        except TypeError:
            toast(message)


def mrw_peek_banner() -> Optional[Dict[str, Any]]:
    raw = st.session_state.get(MRW_BANNER_KEY)
    return raw if isinstance(raw, dict) else None


def mrw_render_banner_zone() -> None:
    """Chamar no App.py logo apos render_route_header. Consome a mensagem (uma vez por interaccao)."""
    data = st.session_state.pop(MRW_BANNER_KEY, None)
    if not isinstance(data, dict):
        return
    msg = str(data.get("message") or "").strip()
    if not msg:
        return
    kind = str(data.get("kind") or "info").lower()
    if kind == "success":
        st.success(msg)
    elif kind == "error":
        st.error(msg)
    elif kind == "warning":
        st.warning(msg)
    else:
        st.info(msg)
