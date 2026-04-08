"""
Consultas ao Supabase com cache para reduzir roundtrips e manter API unica.
"""

from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st
from postgrest.exceptions import APIError
from supabase import Client

MotorRow = Dict[str, Any]


@st.cache_data(
    ttl=45,
    show_spinner=False,
    hash_funcs={Client: lambda _c: "supabase-client"},
)
def fetch_motores_cached(supabase: Client) -> List[MotorRow]:
    """
    Busca motores de forma tolerante a diferenças de schema no Supabase.

    Estratégia:
    1) tenta ordenar por id desc
    2) fallback para created_at desc
    3) fallback sem ordenação
    """
    try:
        res = supabase.table("motores").select("*").order("id", desc=True).execute()
        return res.data or []
    except APIError:
        pass
    except Exception:
        return []

    try:
        res = supabase.table("motores").select("*").order("created_at", desc=True).execute()
        return res.data or []
    except APIError:
        pass
    except Exception:
        return []

    try:
        res = supabase.table("motores").select("*").execute()
        return res.data or []
    except Exception:
        return []


@st.cache_data(
    ttl=45,
    show_spinner=False,
    hash_funcs={Client: lambda _c: "supabase-client"},
)
def fetch_motor_by_id_cached(supabase: Client, motor_id: int) -> MotorRow | None:
    """
    Busca por id com fallback para id_motor em schemas legados.
    """
    try:
        res = supabase.table("motores").select("*").eq("id", motor_id).limit(1).execute()
        if res.data:
            return res.data[0]
    except APIError:
        pass
    except Exception:
        return None

    try:
        res = supabase.table("motores").select("*").eq("id_motor", motor_id).limit(1).execute()
        if res.data:
            return res.data[0]
    except Exception:
        return None

    return None


def clear_motores_cache() -> None:
    fetch_motores_cached.clear()
    fetch_motor_by_id_cached.clear()
