import streamlit as st
from services.database import listar_motores

def show():
    st.header("Consulta de Motores")

    motores = listar_motores()

    if not motores:
        st.info("Nenhum motor cadastrado.")
        return

    # Defina os campos mais importantes (sempre visíveis) e os secundários (escondidos)
    campos_principais = ["marca", "modelo", "potencia", "tensao", "corrente", "rpm"]
    campos_secundarios = [
        "frequencia", "fp", "carcaca", "ip", "isolacao", "regime",
        "rolamento_dianteiro", "rolamento_traseiro", "peso",
        "diametro_eixo", "comprimento_pacote", "numero_ranhuras",
        "ligacao", "fabricacao", "original"
    ]

    for i, motor in enumerate(motores, start=1):
        with st.expander(f"Motor {i} - {motor.get('marca','')} {motor.get('modelo','')}"):
            # Mostra os campos principais sempre
            st.subheader("⚡ Informações Principais")
            for campo in campos_principais:
                st.write(f"**{campo.capitalize()}**: {motor.get(campo, '')}")

            # Mostra os campos secundários dentro de outro expander
            with st.expander("🔽 Mais informações"):
                for campo in campos_secundarios:
                    st.write(f"**{campo.capitalize()}**: {motor.get(campo, '')}")
