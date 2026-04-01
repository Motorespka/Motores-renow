import streamlit as st
from services.database import salvar_motor

def show():

    st.title("⚙️ Cadastro de Motor")

    with st.form("cadastro_motor"):

        col1, col2 = st.columns(2)

        with col1:
            marca = st.text_input("Marca")
            modelo = st.text_input("Modelo")
            potencia = st.text_input("Potência")
            tensao = st.text_input("Tensão")
            corrente = st.text_input("Corrente")
            rpm = st.text_input("RPM")

        with col2:
            polos = st.text_input("Polos")
            isolacao = st.text_input("Isolação")
            ip = st.text_input("IP")
            rolamento_d = st.text_input("Rolamento dianteiro")
            rolamento_t = st.text_input("Rolamento traseiro")

        origem = st.selectbox(
            "Origem do cálculo",
            ["União","Rebobinador","Próprio"]
        )

        salvar = st.form_submit_button("💾 Salvar Motor")

    if salvar:

        motor = {
            "marca": marca,
            "modelo": modelo,
            "potencia": potencia,
            "tensao": tensao,
            "corrente": corrente,
            "rpm": rpm,
            "polos": polos,
            "isolacao": isolacao,
            "ip": ip,
            "rolamento_d": rolamento_d,
            "rolamento_t": rolamento_t,
            "origem_calculo": origem
        }

        salvar_motor(motor)

        st.success("Motor salvo!")
