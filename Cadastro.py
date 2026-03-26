import streamlit as st
import os
from db import salvar_motor
from ocr_motor import ler_placa_motor

def safe_float(valor):
    try:
        return float(str(valor).replace(",", "."))
    except:
        return 0.0

def safe_int(valor):
    try:
        return int(float(str(valor).replace(",", ".")))
    except:
        return 0

def show():
    st.markdown("### 🔐 Área Restrita: Cadastro Técnico")

    senha_digitada = st.text_input("Insira a chave de acesso", type="password", key="login_senha")
    try:
        senha_correta = st.secrets["APP_PASSWORD"]
    except:
        st.error("Erro: APP_PASSWORD não configurada nos Secrets.")
        st.stop()

    if senha_digitada != senha_correta:
        if senha_digitada != "":
            st.warning("Senha incorreta")
        st.stop()
    st.success("Acesso liberado")

    campos = ["marca","modelo","carcaca","peso","potencia","tensao","amperagem","rpm"]
    for c in campos:
        if c not in st.session_state:
            st.session_state[c] = "" if c in ["marca","modelo","carcaca"] else 0.0

    if "form_version" not in st.session_state:
        st.session_state.form_version = 0
    if "dados_ocr" not in st.session_state:
        st.session_state.dados_ocr = {}
    if "debug" not in st.session_state:
        st.session_state.debug = False

    st.subheader("📸 Captura de Dados via Placa")
    arquivo = st.file_uploader("Envie foto da placa do motor", type=["jpg","png","jpeg"], key="uploader_cadastro")
    if arquivo:
        st.image(arquivo, width=300)
        if st.button("Executar OCR", use_container_width=True):
            with st.spinner("🤖 Analisando imagem..."):
                try:
                    base_dir = os.path.dirname(os.path.abspath(__file__))
                    temp_dir = os.path.join(base_dir,"temp")
                    os.makedirs(temp_dir, exist_ok=True)
                    caminho_temp = os.path.join(temp_dir, arquivo.name)
                    with open(caminho_temp,"wb") as f:
                        f.write(arquivo.getbuffer())
                    resultado = ler_placa_motor(caminho_temp)
                    st.session_state.dados_ocr = resultado

                    # Preencher campos de forma segura
                    st.session_state.marca = resultado.get("Marca","")
                    st.session_state.potencia = safe_float(resultado.get("Potência","0"))
                    st.session_state.tensao = safe_float(resultado.get("Tensão","0").split("/")[0])
                    st.session_state.amperagem = safe_float(resultado.get("Corrente","0"))
                    st.session_state.rpm = safe_int(resultado.get("Rotação","0"))

                    st.success("OCR aplicado e campos preenchidos!")
                    if os.path.exists(caminho_temp):
                        os.remove(caminho_temp)
                    st.session_state.form_version += 1
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro no OCR: {e}")

    st.checkbox("🔍 Mostrar dados brutos do OCR", key="debug")
    if st.session_state.debug:
        st.json(st.session_state.dados_ocr)

    st.title("Cadastro de Motor")
    with st.form(key=f"form_motor_v_{st.session_state.form_version}"):
        col1, col2 = st.columns(2)
        with col1:
            marca = st.text_input("Marca", key="marca")
            modelo = st.text_input("Modelo", key="modelo")
            carcaca = st.text_input("Carcaça", key="carcaca")
            peso = st.number_input("Peso (kg)", key="peso")
            potencia = st.number_input("Potência", key="potencia")
            unidade = st.selectbox("Unidade", ["cv","kW"])
            tensao = st.number_input("Tensão (V)", key="tensao")
            amperagem = st.number_input("Amperagem (A)", key="amperagem")
        with col2:
            polos = st.selectbox("Polos", [2,4,6,8], index=1)
            fp = st.number_input("Fator de potência", 0.0, 1.0, 0.85)
            rpm = st.number_input("RPM", key="rpm")
            ip = st.text_input("Grau de Proteção (IP)", value="IP55")
            isolamento = st.text_input("Classe de Isolamento", value="F")
            fs = st.number_input("Fator de Serviço", 0.0, value=1.0)
            refrigeracao = st.text_input("Refrigeração", value="TFVE")
            ligacao = st.text_input("Ligação", value="Δ / Y")
        desenho = st.text_input("Caminho da imagem/desenho")
        submit = st.form_submit_button("Salvar Motor", use_container_width=True)

        if submit:
            if not marca or not modelo:
                st.warning("Marca e Modelo são obrigatórios!")
                st.stop()
            dados_para_salvar = (marca,modelo,carcaca,peso,potencia,unidade,tensao,amperagem,
                                 polos,fp,rpm,ip,isolamento,fs,refrigeracao,ligacao,desenho)
            try:
                salvar_motor(dados_para_salvar)
                st.success(f"Motor {modelo} salvo com sucesso!")
                st.balloons()
                for c in campos:
                    st.session_state[c] = "" if c in ["marca","modelo","carcaca"] else 0.0
                st.session_state.dados_ocr = {}
                st.session_state.form_version += 1
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")
