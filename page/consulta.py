import streamlit as st
from services.database import listar_motores

def show():
    st.header("Consulta")

    motores = listar_motores()

    for m in motores:
        st.write(m)
