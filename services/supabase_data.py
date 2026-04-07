"""
Consultas ao Supabase com cache para reduzir roundtrips e manter API unica.
"""

from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st
from supabase import Client

MotorRow = Dict[str, Any]

from utils.configuracoes_motor import obter_configuracoes_ligacao


@st.cache_data(
    ttl=45,
    show_spinner=False,
    hash_funcs={Client: lambda _c: "supabase-client"},
)
def fetch_motores_cached(supabase: Client) -> List[MotorRow]:
    res = supabase.table("motores").select("*").order("id", desc=True).execute()
    return res.data or []


@st.cache_data(
    ttl=45,
    show_spinner=False,
    hash_funcs={Client: lambda _c: "supabase-client"},
)
def fetch_motor_by_id_cached(supabase: Client, motor_id: int) -> MotorRow | None:
    res = supabase.table("motores").select("*").eq("id", motor_id).limit(1).execute()
    if not res.data:
        return None
    return res.data[0]


def clear_motores_cache() -> None:
    fetch_motores_cached.clear()
    fetch_motor_by_id_cached.clear()
