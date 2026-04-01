import streamlit as st
from services.database import listar_motores, excluir_motor

def show():

    st.title("🔎 Consulta de Motores")

    busca = st.text_input("Pesquisar")

    motores = listar_motores()

    if busca:
        motores = [
            m for m in motores
            if busca.lower() in str(m).lower()
        ]

    if not motores:
        st.info("Nenhum motor encontrado.")
        return

    for motor in motores:

        nome = f"{motor.get('marca','')} {motor.get('modelo','')}"

        with st.expander(nome):

            st.write("Potência:", motor.get("potencia",""))
            st.write("Tensão:", motor.get("tensao",""))
            st.write("RPM:", motor.get("rpm",""))
            st.write("Origem:", motor.get("origem_calculo",""))

            col1, col2 = st.columns(2)

            if col1.button("✏️ Editar", key=f"edit{motor['id']}"):
                st.session_state.motor_editando = motor
                st.session_state.pagina = "editar"
                st.rerun()

            if col2.button("🗑️ Excluir", key=f"del{motor['id']}"):
                excluir_motor(motor["id"])
                st.rerun()
