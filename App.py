import streamlit as st
from auth.login import check_login

st.set_page_config(
    page_title="Moto-Renow",
    layout="wide"
)

check_login()

st.title("Moto-Renow")

menu = st.sidebar.selectbox(
    "Menu",
    ["Cadastro", "Consulta", "Calculadora"]
)

if menu == "Cadastro":
    from pages.cadastro import show
    show()

elif menu == "Consulta":
    from pages.consulta import show
    show()

elif menu == "Calculadora":
    from pages.calculadora import show
    show()
