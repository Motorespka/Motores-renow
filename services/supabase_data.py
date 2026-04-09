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
    candidates = [
        ("vw_consulta_motores", "created_at"),
        ("vw_consulta_motores", "updated_at"),
        ("vw_consulta_motores", None),
        ("vw_motores_para_site", "CreatedAt"),
        ("vw_motores_para_site", "UpdatedAt"),
        ("vw_motores_para_site", None),
        ("motores", "created_at"),
        ("motores", "updated_at"),
        ("motores", None),
    ]

    for table_name, order_col in candidates:
        try:
            query = supabase.table(table_name).select("*")
            if order_col:
                query = query.order(order_col, desc=True)
            res = query.execute()
            data = res.data or []
            if data:
                return data
        except APIError:
            continue
        except Exception:
            continue

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
    lookups = [
        ("vw_consulta_motores", "id"),
        ("vw_motores_para_site", "Id"),
        ("motores", "id"),
        ("arquivos_motor", "id"),
    ]

    for table_name, id_col in lookups:
        try:
            res = (
                supabase
                .table(table_name)
                .select("*")
                .eq(id_col, motor_id)
                .limit(1)
                .execute()
            )
            if res.data:
                return res.data[0]
        except APIError:
            continue
        except Exception:
            continue

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
    lookups = [
        ("arquivos_motor", "id"),
        ("motores", "id"),
        ("vw_motores_para_site", "Id"),
    ]

    for table_name, id_col in lookups:
        try:
            res = (
                supabase
                .table(table_name)
                .select("*")
                .eq(id_col, motor_id)
                .limit(1)
                .execute()
            )
            if res.data:
                return res.data[0]
        except APIError:
            continue
        except Exception:
            continue

    return None


def clear_motores_cache() -> None:
    fetch_motores_cached.clear()
    fetch_motor_by_id_cached.clear()
    fetch_variaveis_by_motor_id_cached.clear()
    fetch_arquivo_by_id_cached.clear()
