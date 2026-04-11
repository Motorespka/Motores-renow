import streamlit as st

def menu():

    st.sidebar.markdown("# ⚙️ Moto-Renow")
    st.sidebar.caption("Sistema Profissional de Rebobinagem")

    return st.sidebar.radio(
        "Navegação",
        ["Cadastro","Consulta","Cálculos","Rebobinador"]
    )
