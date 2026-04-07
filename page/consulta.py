from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st

from components.motor_card import render_motor_card
from core.navigation import Route
from services.supabase_data import fetch_motores_cached
from utils.motor_view import ALIASES, is_empty, normalize_motor_record, pick_value


def _to_text(value: Any) -> str:
    if is_empty(value):
        return ""
    return str(value).strip()


def _search_blob(motor: Dict[str, Any]) -> str:
    keys = ALIASES["marca"] + ALIASES["modelo"] + ALIASES["potencia"] + ALIASES["rpm"]
    return " ".join(_to_text(motor.get(k)) for k in keys).lower()


def _unique_values(rows: List[Dict[str, Any]], aliases: List[str]) -> List[str]:
    values = set()
    for row in rows:
        val = _to_text(pick_value(row, aliases))
        if val:
            values.add(val)
    return sorted(values)


def render(ctx) -> None:
    st.title("🔎 Central de Motores")

    motores_raw = fetch_motores_cached(ctx.supabase)
    if not motores_raw:
        st.info("Nenhum motor cadastrado no sistema.")
        return

    motores = [normalize_motor_record(m) for m in motores_raw]
    busca = st.text_input("Pesquisar", placeholder="Marca, modelo, potência...").strip().lower()
    filtrados = [m for m in motores if busca in _search_blob(m)] if busca else motores

    st.sidebar.markdown("### Filtros da consulta")
    marcas = _unique_values(motores, ALIASES["marca"])
    marca = st.sidebar.selectbox("Marca", ["Todas"] + marcas, key="consulta_filtro_marca")
    if marca != "Todas":
        filtrados = [m for m in filtrados if _to_text(pick_value(m, ALIASES["marca"])) == marca]

    if not filtrados:
        st.warning("Nenhum motor encontrado.")
        return

    for motor in filtrados:
        action = render_motor_card(motor)
        if action == "detail":
            ctx.session.selected_motor_id = motor["id"]
            ctx.session.set_route(Route.DETALHE)
            st.rerun()
        if action == "edit":
            ctx.session.selected_motor_id = motor["id"]
            ctx.session.set_route(Route.EDIT)
            st.rerun()
