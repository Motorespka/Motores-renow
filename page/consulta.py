import streamlit as st
from services.database import listar_motores

def show():
    st.header("Consulta de Motores")

    motores = listar_motores()

    if not motores:
        st.info("Nenhum motor cadastrado.")
        return

    for idx, m in enumerate(motores, start=1):
        st.subheader(f"Motor {idx}")
        st.write({
            "Marca": m.get("marca", ""),
            "Modelo": m.get("modelo", ""),
            "Potência": m.get("potencia", ""),
            "Tensão": m.get("tensao", ""),
            "Corrente": m.get("corrente", ""),
            "RPM": m.get("rpm", ""),
            "Frequência": m.get("frequencia", ""),
            "Fator de Potência": m.get("fp", ""),
            "Carcaça": m.get("carcaca", ""),
            "Grau IP": m.get("ip", ""),
            "Classe de Isolação": m.get("isolacao", ""),
            "Regime": m.get("regime", ""),
            "Rolamento Dianteiro": m.get("rolamento_dianteiro", ""),
            "Rolamento Traseiro": m.get("rolamento_traseiro", ""),
            "Peso": m.get("peso", ""),
            "Diâmetro do Eixo": m.get("diametro_eixo", ""),
            "Comprimento do Pacote": m.get("comprimento_pacote", ""),
            "Número de Ranhuras": m.get("numero_ranhuras", ""),
            "Ligação": m.get("ligacao", ""),
            "Ano de Fabricação": m.get("fabricacao", ""),
            "Original": m.get("original", "")
        })
