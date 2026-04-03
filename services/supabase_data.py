"""
Consultas ao Supabase com cache (st.cache_data) para reduzir idas ao servidor.
"""

from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st
from supabase import Client

MotorRow = Dict[str, Any]


@st.cache_data(
    ttl=45,
    show_spinner=False,
    hash_funcs={Client: lambda _c: "supabase-client"},
)
def fetch_motores_cached(supabase: Client) -> List[MotorRow]:
    res = supabase.table("motores").select("*").order("id", desc=True).execute()
    return res.data or []


def clear_motores_cache() -> None:
    try:
        fetch_motores_cached.clear()
    except Exception:
        pass
