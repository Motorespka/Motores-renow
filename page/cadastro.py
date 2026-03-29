import streamlit as st
from services.ocr_motor import ler_placa_motor

st.title("Cadastro de Motor")

# =====================
# CAMERA DIRETO CELULAR
# =====================
imagem = st.camera_input("📸 Fotografar placa do motor")

dados = {}

if imagem:

    with st.spinner("Lendo placa do motor..."):
        dados, texto = ler_placa_motor(imagem)

    st.success("Placa lida com sucesso")

    with st.expander("Texto reconhecido"):
        st.write(texto)


# =====================
# FORMULÁRIO AUTO
# =====================
marca = st.text_input("Marca", dados.get("marca", ""))
modelo = st.text_input("Modelo", dados.get("modelo", ""))
rpm = st.text_input("RPM", dados.get("rpm", ""))
tensao = st.text_input("Tensão", dados.get("tensao", ""))
corrente = st.text_input("Corrente", dados.get("corrente", ""))
isolacao = st.text_input("Isolação", dados.get("isolacao", ""))
regime = st.text_input("Regime", dados.get("regime", ""))
polos = st.text_input("Polos", dados.get("polos", ""))

if st.button("Salvar Motor"):
    st.success("Motor cadastrado!")
