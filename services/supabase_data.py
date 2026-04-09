"""
Consultas ao Supabase com cache para reduzir roundtrips e manter API única.
Adaptado para a nova estrutura:
- public.arquivos_motor
- public.variaveis_motor
- public.vw_consulta_motores
"""

from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st
try:
    from postgrest.exceptions import APIError
except Exception:
    class APIError(Exception):
        pass

try:
    from supabase import Client
except Exception:
    class Client:  # type: ignore[no-redef]
        pass

try:
    from services.database import LocalRuntimeClient
except Exception:
    LocalRuntimeClient = None  # type: ignore[assignment]

MotorRow = Dict[str, Any]
VariavelRow = Dict[str, Any]

HASH_FUNCS = {Client: lambda _c: "supabase-client"}
if LocalRuntimeClient is not None:
    HASH_FUNCS[LocalRuntimeClient] = lambda _c: "local-runtime-client"


@st.cache_data(
    ttl=45,
    show_spinner=False,
    hash_funcs=HASH_FUNCS,
)
def fetch_motores_cached(supabase: Client) -> List[MotorRow]:
    """
    Busca os registros da view vw_consulta_motores.

    Estratégia:
    1) tenta ordenar por created_at desc
    2) fallback para updated_at desc
    3) fallback sem ordenação
    """
    try:
        res = (
            supabase
            .table("vw_consulta_motores")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        return res.data or []
    except APIError:
        pass
    except Exception:
        return []

    try:
        res = (
            supabase
            .table("vw_consulta_motores")
            .select("*")
            .order("updated_at", desc=True)
            .execute()
        )
        return res.data or []
    except APIError:
        pass
    except Exception:
        return []

    try:
        res = supabase.table("vw_consulta_motores").select("*").execute()
        return res.data or []
    except Exception:
        return []


@st.cache_data(
    ttl=45,
    show_spinner=False,
    hash_funcs=HASH_FUNCS,
)
def fetch_motor_by_id_cached(supabase: Client, motor_id: str) -> MotorRow | None:
    """
    Busca um registro específico na view vw_consulta_motores pelo id (UUID).
    """
    try:
        res = (
            supabase
            .table("vw_consulta_motores")
            .select("*")
            .eq("id", motor_id)
            .limit(1)
            .execute()
        )
        if res.data:
            return res.data[0]
    except APIError:
        pass
    except Exception:
        return None

    try:
        res = (
            supabase
            .table("arquivos_motor")
            .select("*")
            .eq("id", motor_id)
            .limit(1)
            .execute()
        )
        if res.data:
            return res.data[0]
    except Exception:
        return None

    return None


@st.cache_data(
    ttl=45,
    show_spinner=False,
    hash_funcs=HASH_FUNCS,
)
def fetch_variaveis_by_motor_id_cached(supabase: Client, motor_id: str) -> List[VariavelRow]:
    """
    Busca todas as variáveis extraídas de um arquivo/motor em variaveis_motor.
    """
    try:
        res = (
            supabase
            .table("variaveis_motor")
            .select("*")
            .eq("arquivo_id", motor_id)
            .order("bloco_id", desc=False)
            .execute()
        )
        return res.data or []
    except APIError:
        pass
    except Exception:
        return []

    try:
        res = (
            supabase
            .table("variaveis_motor")
            .select("*")
            .eq("arquivo_id", motor_id)
            .execute()
        )
        return res.data or []
    except Exception:
        return []


@st.cache_data(
    ttl=45,
    show_spinner=False,
    hash_funcs=HASH_FUNCS,
)
def fetch_arquivo_by_id_cached(supabase: Client, motor_id: str) -> MotorRow | None:
    """
    Busca os metadados crus do arquivo na tabela arquivos_motor.
    """
    try:
        res = (
            supabase
            .table("arquivos_motor")
            .select("*")
            .eq("id", motor_id)
            .limit(1)
            .execute()
        )
        if res.data:
            return res.data[0]
    except APIError:
        pass
    except Exception:
        return None

    return None


def clear_motores_cache() -> None:
    fetch_motores_cached.clear()
    fetch_motor_by_id_cached.clear()
    fetch_variaveis_by_motor_id_cached.clear()
    fetch_arquivo_by_id_cached.clear()
