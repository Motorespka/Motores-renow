import streamlit as st

from core.navigation import Route
from services.supabase_data import clear_motores_cache, fetch_motor_by_id_cached


def _update_motor_supabase(supabase, id_motor, payload: dict) -> None:
    supabase.table("motores").update(payload).eq("id", id_motor).execute()


def render(ctx):
    st.title("✏️ Editar Motor")

    id_motor = ctx.session.selected_motor_id
    if id_motor is None:
        st.warning("Nenhum motor selecionado para edição.")
        if st.button("🔙 Voltar para Consulta", use_container_width=True):
            ctx.session.set_route(Route.CONSULTA)
            st.rerun()
        return

    motor = fetch_motor_by_id_cached(ctx.supabase, id_motor)
    if motor is None:
        st.error("Motor não encontrado.")
        if st.button("🔙 Voltar para Consulta", use_container_width=True):
            ctx.session.set_route(Route.CONSULTA)
            st.rerun()
        return

    with st.form("edit_motor_form"):
        marca = st.text_input("Marca", value=motor.get("marca") or "")
        modelo = st.text_input("Modelo", value=motor.get("modelo") or "")
        potencia = st.text_input("Potência", value=motor.get("potencia") or "")
        tensao = st.text_input("Tensão", value=motor.get("tensao") or "")
        corrente = st.text_input("Corrente", value=motor.get("corrente") or "")
        rpm = st.text_input("RPM", value=motor.get("rpm") or "")

        c1, c2 = st.columns(2)
        with c1:
            salvar = st.form_submit_button("💾 SALVAR", use_container_width=True)
        with c2:
            voltar = st.form_submit_button("🔙 VOLTAR", use_container_width=True)

    if voltar:
        ctx.session.set_route(Route.DETALHE)
        st.rerun()

    if salvar:
        payload = {
            "marca": marca,
            "modelo": modelo,
            "potencia": potencia,
            "tensao": tensao,
            "corrente": corrente,
            "rpm": rpm,
        }
        _update_motor_supabase(ctx.supabase, id_motor, payload)
        clear_motores_cache()
        st.success("Alterações salvas com sucesso.")
        ctx.session.set_route(Route.DETALHE)
        st.rerun()
