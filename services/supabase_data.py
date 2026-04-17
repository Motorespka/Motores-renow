"""
Consultas ao Supabase com cache para reduzir roundtrips e manter API única.
Fonte de listagem (env): SUPABASE_CONSULTA_TABLE (default vw_motores_para_site),
fallback SUPABASE_PRIMARY_TABLE (default motores), depois vw_consulta_motores.
"""

from __future__ import annotations

import os
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


def _read_secret_or_env(*names: str) -> str:
    for name in names:
        try:
            value = st.secrets.get(name)
            if value:
                return str(value).strip()
        except Exception:
            pass
        value = os.environ.get(name)
        if value:
            return str(value).strip()
    return ""


def _resolve_fetch_limit() -> int:
    raw = _read_secret_or_env("MOTORES_FETCH_LIMIT", "SUPABASE_MOTORES_FETCH_LIMIT")
    try:
        value = int(str(raw or "").strip())
    except Exception:
        value = 3000
    return max(200, min(value, 20000))


def _id_column_for_table(table: str) -> str:
    return "Id" if table.strip().lower() == "vw_motores_para_site" else "id"


def _resolve_consulta_table_chain() -> List[str]:
    """
    Ordem de tentativa: SUPABASE_CONSULTA_TABLE (default vw_motores_para_site),
    depois SUPABASE_PRIMARY_TABLE (default motores), depois demais fontes.
    MOTORES_SOURCE_TABLE / SUPABASE_MOTORES_SOURCE_TABLE mantém compat quando
    SUPABASE_CONSULTA_TABLE não está definido.
    """
    consulta = _read_secret_or_env("SUPABASE_CONSULTA_TABLE", "MOTORES_CONSULTA_TABLE").strip().lower()
    primary = (
        _read_secret_or_env(
            "SUPABASE_PRIMARY_TABLE",
            "MOTORES_PRIMARY_TABLE",
            "SUPABASE_MOTORES_PRIMARY_TABLE",
        ).strip().lower()
        or "motores"
    )
    legacy = _read_secret_or_env("MOTORES_SOURCE_TABLE", "SUPABASE_MOTORES_SOURCE_TABLE").strip().lower()
    known = {"motores", "vw_consulta_motores", "vw_motores_para_site", "arquivos_motor"}

    seen: set[str] = set()
    ordered: List[str] = []

    def add(name: str) -> None:
        n = name.strip().lower()
        if not n or n in seen:
            return
        seen.add(n)
        ordered.append(n)

    if consulta:
        add(consulta)
    elif legacy and legacy in known:
        add(legacy)
    else:
        add("vw_motores_para_site")

    add(primary)
    for t in ("motores", "vw_motores_para_site", "vw_consulta_motores"):
        add(t)
    return ordered


def _resolve_source_candidates() -> List[str]:
    return _resolve_consulta_table_chain()


def _single_motor_table_lookups() -> List[tuple[str, str]]:
    """(tabela, coluna_id) para busca por UUID/id."""
    lookups: List[tuple[str, str]] = []
    for table in _resolve_consulta_table_chain():
        lookups.append((table, _id_column_for_table(table)))
    if not any(t == "arquivos_motor" for t, _ in lookups):
        lookups.append(("arquivos_motor", "id"))
    return lookups


def _sorted_rows(rows: List[MotorRow]) -> List[MotorRow]:
    if not rows:
        return rows
    for key in ("updated_at", "created_at", "UpdatedAt", "CreatedAt"):
        if any(key in row for row in rows):
            return sorted(rows, key=lambda row: str(row.get(key) or ""), reverse=True)
    return rows


@st.cache_data(
    ttl=45,
    show_spinner=False,
    hash_funcs=HASH_FUNCS,
)
def fetch_motores_cached(supabase: Client) -> List[MotorRow]:
    """
    Busca os registros de motores com fallback entre fontes conhecidas.
    Estratégia otimizada para reduzir roundtrips por rerun.
    """
    fetch_limit = _resolve_fetch_limit()
    for table_name in _resolve_source_candidates():
        try:
            res = supabase.table(table_name).select("*").limit(fetch_limit).execute()
            data = res.data or []
            if data:
                return _sorted_rows(data)
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
    Busca um registro pelo id (UUID), priorizando a mesma cadeia da listagem
    (vw_motores_para_site → motores → …).
    """
    for table_name, id_col in _single_motor_table_lookups():
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
