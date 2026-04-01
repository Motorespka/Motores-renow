import streamlit as st
from services.database import listar_motores, excluir_motor


def show():

    st.title("🔎 Consulta de Motores")

    motores = listar_motores()

    # ================= BUSCA =================
    busca = st.text_input("Pesquisar motor")

    if busca:
        motores = [
            m for m in motores
            if busca.lower() in str(m).lower()
        ]

    if not motores:
        st.info("Nenhum motor encontrado")
        return

    # ================= LISTAGEM =================

    for motor in motores:

        titulo = f"{motor.get('marca','')} | {motor.get('modelo','')} | {motor.get('potencia','')}"

        with st.expander(titulo):

            # -------- INFORMAÇÕES BÁSICAS --------
            st.subheader("⚡ Dados principais")

            st.write("Marca:", motor.get("marca"))
            st.write("Modelo:", motor.get("modelo"))
            st.write("Potência:", motor.get("potencia"))
            st.write("Tensão:", motor.get("tensao"))
            st.write("Corrente:", motor.get("corrente"))
            st.write("RPM:", motor.get("rpm"))

            # -------- INFORMAÇÕES COMPLETAS --------
            st.subheader("📋 Ficha completa")

            for chave, valor in motor.items():
                if chave != "id":
                    st.write(f"**{chave}**:", valor)

            # -------- AÇÕES --------
            col1, col2 = st.columns(2)

            with col1:
                if st.button("🧮 Abrir cálculo", key=f"calc{motor['id']}"):
                    st.info("Calculadora será integrada aqui")

            with col2:
                if st.button("🗑 Excluir", key=f"del{motor['id']}"):
                    excluir_motor(motor["id"])
                    st.success("Motor excluído")
                    st.rerun()
