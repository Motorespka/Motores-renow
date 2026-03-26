import streamlit as st
import os
from db import salvar_motor
from ocr_motor import ler_placa_motor

# Funções utilitárias para conversão segura
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
    # =========================
    # 🔐 LOGIN
    # =========================
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

    # =========================
    # SESSION STATE
    # =========================
    campos_texto = ["marca","modelo","carcaca","ip","isolamento","refrigeracao","ligacao","desenho","unidade"]
    campos_num = ["peso","potencia","tensao","amperagem","polos","fp","rpm","fs"]

    for c in campos_texto:
        if c not in st.session_state:
            st.session_state[c] = ""
    for c in campos_num:
        if c not in st.session_state:
            st.session_state[c] = 0.0

    if "form_version" not in st.session_state:
        st.session_state.form_version = 0
    if "dados_ocr" not in st.session_state:
        st.session_state.dados_ocr = {}
    if "debug" not in st.session_state:
        st.session_state.debug = False
    if "last_uploaded" not in st.session_state:
        st.session_state.last_uploaded = None

    # =========================
    # UPLOAD E OCR AUTOMÁTICO
    # =========================
    st.subheader("📸 Captura de Dados via Placa")
    arquivo = st.file_uploader("Envie foto da placa do motor", type=["jpg","png","jpeg"], key="uploader_cadastro")
    if arquivo:
        st.image(arquivo, width=300)
        if st.session_state.last_uploaded != arquivo.name:
            st.session_state.last_uploaded = arquivo.name
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

                    # =========================
                    # MAPEAR OCR PARA FORMULÁRIO
                    # =========================
                    st.session_state.marca = resultado.get("Marca","")
                    st.session_state.modelo = resultado.get("Modelo","")
                    st.session_state.carcaca = resultado.get("Carcaça","")
                    st.session_state.peso = safe_float(resultado.get("Peso","0"))
                    st.session_state.potencia = safe_float(resultado.get("Potência","0"))
                    st.session_state.unidade = resultado.get("Unidade","cv")
                    tensao_raw = resultado.get("Tensão","0").split("/")[0]
                    st.session_state.tensao = safe_float(tensao_raw)
                    st.session_state.amperagem = safe_float(resultado.get("Corrente","0"))
                    st.session_state.polos = int(resultado.get("Polos",4))
                    st.session_state.fp = safe_float(resultado.get("Fator de potência","0.85"))
                    st.session_state.rpm = safe_int(resultado.get("Rotação","0"))
                    st.session_state.ip = resultado.get("IP","IP55")
                    st.session_state.isolamento = resultado.get("Isolamento","F")
                    st.session_state.fs = safe_float(resultado.get("Fator de Serviço","1.0"))
                    st.session_state.refrigeracao = resultado.get("Refrigeração","TFVE")
                    st.session_state.ligacao = resultado.get("Ligação","Δ / Y")
                    st.session_state.desenho = resultado.get("Desenho","")

                    if os.path.exists(caminho_temp):
                        os.remove(caminho_temp)

                except Exception as e:
                    st.error(f"Erro no OCR: {e}")

    # =========================
    # DEBUG OCR
    # =========================
    st.checkbox("🔍 Mostrar dados brutos do OCR", key="debug")
    if st.session_state.debug:
        st.json(st.session_state.dados_ocr)

    # =========================
    # FORMULÁRIO DE CADASTRO
    # =========================
    st.title("Cadastro de Motor")
    form_key = f"form_motor_v_{st.session_state.form_version}"
    with st.form(key=form_key):
        col1, col2 = st.columns(2)
        with col1:
            marca = st.text_input("Marca", key="marca")
            modelo = st.text_input("Modelo", key="modelo")
            carcaca = st.text_input("Carcaça", key="carcaca")
            peso = st.number_input("Peso (kg)", key="peso")
            potencia = st.number_input("Potência", key="potencia")
            unidade = st.selectbox("Unidade", ["cv","kW"], key="unidade")
            tensao = st.number_input("Tensão (V)", key="tensao")
            amperagem = st.number_input("Amperagem (A)", key="amperagem")
        with col2:
            polos = st.selectbox("Polos", [2,4,6,8], index=1, key="polos")
            fp = st.number_input("Fator de potência", 0.0, 1.0, 0.85, key="fp")
            rpm = st.number_input("RPM", key="rpm")
            ip = st.text_input("Grau de Proteção (IP)", key="ip")
            isolamento = st.text_input("Classe de Isolamento", key="isolamento")
            fs = st.number_input("Fator de Serviço", 0.0, value=1.0, key="fs")
            refrigeracao = st.text_input("Refrigeração", key="refrigeracao")
            ligacao = st.text_input("Ligação", key="ligacao")
        desenho = st.text_input("Caminho da imagem/desenho", key="desenho")

        submit = st.form_submit_button("Salvar Motor", use_container_width=True)

        if submit:
            if not st.session_state.marca or not st.session_state.modelo:
                st.warning("Marca e Modelo são obrigatórios!")
                st.stop()
            dados_para_salvar = (
                st.session_state.marca,
                st.session_state.modelo,
                st.session_state.carcaca,
                st.session_state.peso,
                st.session_state.potencia,
                st.session_state.unidade,
                st.session_state.tensao,
                st.session_state.amperagem,
                st.session_state.polos,
                st.session_state.fp,
                st.session_state.rpm,
                st.session_state.ip,
                st.session_state.isolamento,
                st.session_state.fs,
                st.session_state.refrigeracao,
                st.session_state.ligacao,
                st.session_state.desenho
            )
            try:
                salvar_motor(dados_para_salvar)
                st.success(f"Motor {st.session_state.modelo} salvo com sucesso!")
                st.balloons()
                # Reset
                for c in campos_texto:
                    st.session_state[c] = ""
                for c in campos_num:
                    st.session_state[c] = 0.0
                st.session_state.dados_ocr = {}
                st.session_state.form_version += 1
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")
