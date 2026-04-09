from __future__ import annotations

import streamlit as st

from core.access_control import is_admin_user
from core.navigation import Route
from services.supabase_data import fetch_motor_by_id_cached
from utils.motor_view import friendly, normalize_motor_record


def render(ctx) -> None:
    admin_user = is_admin_user()

    motor_id = ctx.session.selected_motor_id
    if motor_id is None:
        st.warning("Nenhum motor selecionado para detalhe.")
        if st.button("Voltar para consulta", use_container_width=True):
            ctx.session.set_route(Route.CONSULTA)
            st.rerun()
        return

    motor = fetch_motor_by_id_cached(ctx.supabase, motor_id)
    if motor is None:
        st.error(f"Motor {motor_id} nao encontrado.")
        if st.button("Voltar para consulta", use_container_width=True):
            ctx.session.set_route(Route.CONSULTA)
            st.rerun()
        return

    m = normalize_motor_record(motor)
    st.title(f"Detalhe do Motor #{motor_id}")
    st.write(f"**Marca:** {friendly(m.get('marca'))}")
    st.write(f"**Modelo:** {friendly(m.get('modelo'))}")
    st.write(f"**Potencia:** {friendly(m.get('potencia_hp_cv'))}")
    st.write(f"**RPM:** {friendly(m.get('rpm_nominal'))}")
    st.write(f"**Tensao:** {friendly(m.get('tensao_v'))}")
    st.write(f"**Corrente:** {friendly(m.get('corrente_nominal_a'))}")

    dados = m.get("dados_tecnicos_json", {}) if isinstance(m, dict) else {}
    oficina = dados.get("oficina", {}) if isinstance(dados, dict) else {}
    resultado = oficina.get("resultado_pos_servico", {}) if isinstance(oficina, dict) else {}
    historico = oficina.get("historico_tecnico", []) if isinstance(oficina, dict) else []
    st.write(f"**Status Oficina:** {friendly(resultado.get('status') if isinstance(resultado, dict) else '')}")
    st.write(f"**Historico Tecnico:** {len(historico) if isinstance(historico, list) else 0} registro(s)")

    if admin_user:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Editar motor", use_container_width=True):
                ctx.session.set_route(Route.EDIT)
                st.rerun()
        with c2:
            if st.button("Voltar", use_container_width=True):
                ctx.session.set_route(Route.CONSULTA)
                st.rerun()
    else:
        if st.button("Voltar", use_container_width=True):
            ctx.session.set_route(Route.CONSULTA)
            st.rerun()


def show(ctx):
    return render(ctx)
