import streamlit as st
import os
from db import salvar_motor
from ocr_motor import ler_placa_motor


def show():

    st.markdown("### 🔐 Área Restrita: Cadastro Técnico")

    # ===== LOGIN =====
    senha_digitada = st.text_input(
        "Insira a chave de acesso",
        type="password"
    )

    senha_correta = st.secrets["APP_PASSWORD"]

    if senha_digitada != senha_correta:
        if senha_digitada != "":
            st.warning("Senha incorreta")
        st.stop()

    st.success("Acesso liberado")

    # ===== UPLOAD =====
    st.subheader("📸 Captura de Dados via Placa")

    arquivo = st.file_uploader(
        "Envie foto da placa/cálculo do motor",
        type=["jpg", "png", "jpeg"]
    )

    if arquivo:
        st.image(arquivo, caption="Imagem Carregada", width=300)

        if st.button("Executar OCR"):
            with st.spinner("Extraindo dados..."):
                os.makedirs("temp", exist_ok=True)

                caminho_temp = os.path.join("temp", arquivo.name)

                with open(caminho_temp, "wb") as f:
                    f.write(arquivo.getbuffer())

                st.info("Texto extraído (simulação)")

    # ===== FORMULÁRIO =====
    st.title("Cadastro de Motor")

    with st.form("form_cadastro_motor"):

        col1, col2 = st.columns(2)

        with col1:
            marca = st.text_input("Marca")
            modelo = st.text_input("Modelo")
            carcaca = st.text_input("Carcaça")
            peso = st.number_input("Peso (kg)", 0.0)
            potencia = st.number_input("Potência", 0.0)
            unidade = st.selectbox("Unidade", ["cv", "kW"])
            tensao = st.number_input("Tensão (V)", 0.0)
            amperagem = st.number_input("Amperagem (A)", 0.0)

        with col2:
            polos = st.selectbox("Polos", [2, 4, 6, 8])
            fp = st.number_input("Fator de potência", 0.0, 1.0)
            rpm = st.number_input("RPM", 0)
            ip = st.text_input("Grau de Proteção (IP)")
            isolamento = st.text_input("Classe de Isolamento")
            fs = st.number_input("Fator de Serviço", 0.0)
            refrigeracao = st.text_input("Refrigeração")
            ligacao = st.text_input("Ligação")

        desenho = st.text_input("Caminho da imagem/desenho")

        submit = st.form_submit_button(
            "salvar Motor",
            use_container_width=True
        )

        if submit:

            if marca and modelo:

                dados = (
                    marca, modelo, carcaca, peso, potencia, unidade,
                    tensao, amperagem, polos, fp, rpm, ip,
                    isolamento, fs, refrigeracao, ligacao, desenho
                )

                Salvar_motor(dados)

                st.balloons()
                st.success(f"Motor {modelo} salvo!")

            else:
                st.warning("Marca e Modelo são obrigatórios.")

dados_ocr = ler_placa_motor(Database_motores)
st.sucess("Dados encontrados!")
st.write(dados_ocr)

