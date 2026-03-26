import streamlit as st
import os
import numpy as np
from PIL import Image
from db import salvar_motor 
from ocr_motor import ler_placa_motor


def show():
    # =========================
    # 🔐 1. LOGIN
    # =========================
    st.markdown("### 🔐 Área Restrita: Cadastro Técnico")

    senha_digitada = st.text_input(
        "Insira a chave de acesso",
        type="password",
        key="login_senha"
    )

    try:
        senha_correta = st.secrets["APP_PASSWORD"]
    except Exception:
        st.error("Erro: APP_PASSWORD não configurada nos Secrets.")
        st.stop()

    if senha_digitada != senha_correta:
        if senha_digitada != "":
            st.warning("Senha incorreta")
        st.stop()

    st.success("Acesso liberado")

    # =========================
    # 📦 2. SESSION STATE
    # =========================
    if "dados_ocr" not in st.session_state:
        st.session_state.dados_ocr = {}

    if "form_version" not in st.session_state:
        st.session_state.form_version = 0

    if "debug" not in st.session_state:
        st.session_state.debug = False

    # =========================
    # 🔍 3. FUNÇÕES AUXILIARES
    # =========================

    def buscar_inteligente(campo):
        """
        Busca valores no OCR mesmo com nomes diferentes
        """
        mapa = {
            "marca": ["marca"],
            "potencia": ["potência", "kw", "cv", "hp"],
            "tensao": ["tensão", "v"],
            "corrente": ["corrente", "a"],
            "rotacao": ["rpm", "rotação"],
        }

        for k, v in st.session_state.dados_ocr.items():
            for termo in mapa.get(campo, []):
                if termo in k.lower():
                    return str(v)
        return ""

    def to_float(valor):
        try:
            return float(str(valor).replace(",", "."))
        except:
            return 0.0

    def to_int(valor):
        try:
            return int(float(str(valor).replace(",", ".")))
        except:
            return 0

    # =========================
    # 📸 4. OCR
    # =========================
    st.subheader("📸 Captura de Dados via Placa")

    arquivo = st.file_uploader(
        "Envie foto da placa do motor",
        type=["jpg", "png", "jpeg"],
        key="uploader_cadastro"
    )

    if arquivo:
        st.image(arquivo, caption="Imagem Carregada", width=300)

        if st.button("Executar OCR", use_container_width=True):
            with st.spinner("🤖 IA analisando imagem..."):
                try:
                    base_dir = os.path.dirname(os.path.abspath(__file__))
                    temp_dir = os.path.join(base_dir, "temp")
                    os.makedirs(temp_dir, exist_ok=True)

                    caminho_temp = os.path.join(temp_dir, arquivo.name)

                    with open(caminho_temp, "wb") as f:
                        f.write(arquivo.getbuffer())

                    resultado = ler_placa_motor(caminho_temp)

                    st.session_state.dados_ocr = resultado
                    st.session_state.form_version += 1

                    os.remove(caminho_temp)

                    st.success("OCR concluído!")
                    st.rerun()

                except Exception as e:
                    st.error(f"Erro no OCR: {e}")

    # =========================
    # 🧠 DEBUG OCR
    # =========================
    st.checkbox("🔍 Mostrar dados brutos do OCR", key="debug")

    if st.session_state.debug:
        st.write("Dados OCR:")
        st.json(st.session_state.dados_ocr)

    # =========================
    # 📝 5. FORMULÁRIO
    # =========================
    st.title("Cadastro de Motor")

    with st.form(key=f"form_motor_v_{st.session_state.form_version}"):

        col1, col2 = st.columns(2)

        with col1:
            marca = st.text_input("Marca", value=buscar_inteligente("marca"))
            modelo = st.text_input("Modelo")
            carcaca = st.text_input("Carcaça")
            peso = st.number_input("Peso (kg)", 0.0)

            potencia = st.number_input(
                "Potência",
                value=to_float(buscar_inteligente("potencia"))
            )

            unidade = st.selectbox("Unidade", ["cv", "kW"])

            tensao = st.number_input(
                "Tensão (V)",
                value=to_float(buscar_inteligente("tensao"))
            )

            amperagem = st.number_input(
                "Amperagem (A)",
                value=to_float(buscar_inteligente("corrente"))
            )

        with col2:
            polos = st.selectbox("Polos", [2, 4, 6, 8], index=1)

            fp = st.number_input(
                "Fator de potência",
                min_value=0.0,
                max_value=1.0,
                value=0.85
            )

            rpm = st.number_input(
                "RPM",
                value=to_int(buscar_inteligente("rotacao"))
            )

            ip = st.text_input("Grau de Proteção (IP)", value="IP55")
            isolamento = st.text_input("Classe de Isolamento", value="F")
            fs = st.number_input("Fator de Serviço", 0.0, value=1.0)
            refrigeracao = st.text_input("Refrigeração", value="TFVE")
            ligacao = st.text_input("Ligação", value="Δ / Y")

        desenho = st.text_input("Caminho da imagem/desenho")

        submit = st.form_submit_button("Salvar Motor", use_container_width=True)

        # =========================
        # 💾 6. SALVAR
        # =========================
        if submit:
            if not marca or not modelo:
                st.warning("Marca e Modelo são obrigatórios!")
                st.stop()

            dados_para_salvar = (
                marca, modelo, carcaca, peso, potencia, unidade,
                tensao, amperagem, polos, fp, rpm, ip,
                isolamento, fs, refrigeracao, ligacao, desenho
            )

            try:
                salvar_motor(dados_para_salvar)

                st.success(f"Motor {modelo} salvo com sucesso!")
                st.balloons()

                # Reset inteligente
                st.session_state.dados_ocr = {}
                st.session_state.form_version += 1

                st.rerun()

            except Exception as e:
                st.error(f"Erro ao salvar: {e}")
