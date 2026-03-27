import streamlit as st
from services.ocr_motor import ler_placa_motor
from services.database import salvar_motor

def show():

    st.header("Cadastro de Motor")

    imagem = st.file_uploader("Foto da placa")

    dados = {}

    if imagem:
        if st.button("Escanear placa"):
            dados = ler_placa_motor(imagem)

    marca = st.text_input("Marca", dados.get("Marca",""))
    tensao = st.text_input("Tensão", dados.get("Tensão",""))
    potencia = st.text_input("Potência", dados.get("Potência",""))

    if st.button("Salvar"):
        salvar_motor(marca, tensao, potencia)
        st.success("Motor salvo!")
