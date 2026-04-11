from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st
from supabase import Client

MotorRow = Dict[str, Any]


@st.cache_data(
    show_spinner=False,
    ttl=5,  # reduz chance de ficar “stale” sem perder performance
    hash_funcs={Client: lambda _client: "supabase-client"},
)
def consultar_motores(supabase: Client) -> List[MotorRow]:
    """
    Consulta os motores no Supabase e retorna os dados.
    Cacheado para evitar reconsulta toda vez que o usuário interage na tela.
    """
    res = supabase.table("motores").select("*").order("id", desc=True).execute()
    return res.data or []


def excluir_motor(supabase: Client, id_motor: Any) -> bool:
    """
    Remove um motor pelo id (não cacheado).
    """
    supabase.table("motores").delete().eq("id", id_motor).execute()
    return True
