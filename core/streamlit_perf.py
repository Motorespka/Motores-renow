"""Helpers para reduzir rerun com `st.fragment` (Streamlit >= 1.33)."""

from __future__ import annotations

import streamlit as st

CTX_KEY = "mrw_page_frag_ctx"


def maybe_fragment(fn):
    dec = getattr(st, "fragment", None)
    return dec(fn) if callable(dec) else fn


def stash_page_ctx(ctx, **extra: object) -> None:
    st.session_state[CTX_KEY] = {"ctx": ctx, **extra}


def pop_page_ctx_pack() -> dict:
    return st.session_state.get(CTX_KEY) or {}
