from __future__ import annotations

import streamlit as st

from core.navigation import Route
from services.supabase_data import fetch_motor_by_id_cached
from utils.motor_view import friendly, normalize_motor_record


def render(ctx) -> None:
    motor_id = ctx.session.selected_motor_id
    if motor_id is None:
        st.warning("Nenhum motor selecionado para detalhe.")
        if st.button("Voltar para consulta", use_container_width=True):
            ctx.session.set_route(Route.CONSULTA)
            st.rerun()
        return

    motor = fetch_motor_by_id_cached(ctx.supabase, motor_id)
    if motor is None:
        st.error(f"Motor {motor_id} não encontrado.")
        if st.button("Voltar para consulta", use_container_width=True):
            ctx.session.set_route(Route.CONSULTA)
            st.rerun()
        return

    m = normalize_motor_record(motor)
    st.title(f"🔧 Detalhe do Motor #{motor_id}")
    st.write(f"**Marca:** {friendly(m.get('marca'))}")
    st.write(f"**Modelo:** {friendly(m.get('modelo'))}")
    st.write(f"**Potência:** {friendly(m.get('potencia_hp_cv'))}")
    st.write(f"**RPM:** {friendly(m.get('rpm_nominal'))}")
    st.write(f"**Tensão:** {friendly(m.get('tensao_v'))}")
    st.write(f"**Corrente:** {friendly(m.get('corrente_nominal_a'))}")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Editar motor", use_container_width=True):
            ctx.session.set_route(Route.EDIT)
            st.rerun()
    with c2:
        if st.button("Voltar", use_container_width=True):
            ctx.session.set_route(Route.CONSULTA)
            st.rerun()
