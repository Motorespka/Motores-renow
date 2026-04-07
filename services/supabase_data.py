"""
Supabase data helpers used by consulta/cadastro pages.
"""

from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st
from supabase import Client

try:
    # Backward-compatible re-export used by legacy pages.
    from utils.configuracoes_motor import obter_configuracoes_ligacao
except Exception:
    def obter_configuracoes_ligacao(_motor_data: Dict[str, Any]) -> str:
        return "Configuracoes de ligacao indisponiveis."

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
