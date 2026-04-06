from __future__ import annotations

from typing import Any, Dict, List
import streamlit as st
from supabase import Client

MotorRow = Dict[str, Any]

NOME_TABELA_MOTORES = "motores"

CAMPOS_RESUMO_CARD = """
id, marca, modelo, potencia_hp_cv,
potencia_kw, rpm_nominal, fases,
tensao_v, polos
"""


@st.cache_data(
    ttl=3600,
    show_spinner=False,
    hash_funcs={Client: lambda _: "supabase"},
)
def get_motores_resumidos(supabase: Client) -> List[MotorRow]:
    res = (
        supabase.table(NOME_TABELA_MOTORES)
        .select(CAMPOS_RESUMO_CARD)
        .order("id", desc=True)
        .execute()
    )

    return res.data or []


@st.cache_data(
    ttl=3600,
    show_spinner=False,
    hash_funcs={Client: lambda _: "supabase"},
)
def get_detalhes_motor(supabase: Client, motor_id: int) -> MotorRow | None:
    res = (
        supabase.table(NOME_TABELA_MOTORES)
        .select("*")
        .eq("id", motor_id)
        .execute()
    )

    return res.data[0] if res.data else None


def clear_motores_cache():
    get_motores_resumidos.clear()
