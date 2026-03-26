import streamlit as st
import os
import numpy as np
from PIL import Image
from db import salvar_motor 
from ocr_motor import ler_placa_motor

def show():
    # 1. TÍTULO E LOGIN
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

    # 2. INICIALIZAÇÃO DO ESTADO
    if "dados_ocr" not in st.session_state:
        st.session_state.dados_ocr = {
            "Marca": "", "Tensão (V)": "0.0", "Potência (kW/HP)": "0.0", 
            "Rotação (RPM)": "0", "Frequência (Hz)": "", "Corrente (A)": "0.0"
        }

    # 3. UPLOAD E OCR (A LÓGICA DA PASTA TEMP ESTÁ AQUI)
    st.subheader("📸 Captura de Dados via Placa")

    arquivo = st.file_uploader(
        "Envie foto da placa/cálculo do motor",
        type=["jpg", "png", "jpeg"],
        key="uploader_cadastro"
    )

    if arquivo:
        st.image(arquivo, caption="Imagem Carregada", width=300)

        if st.button("Executar OCR", use_container_width=True):
            with st.spinner("🤖 IA Analisando imagem..."):
                try:
                    # Caminho absoluto para evitar erro de pasta
                    base_dir = os.path.dirname(os.path.abspath(__file__))
                    temp_dir = os.path.join(base_dir, "temp")
                    os.makedirs(temp_dir, exist_ok=True)
                    
                    nome_arquivo = arquivo.name.replace(" ", "_")
                    caminho_temp = os.path.join(temp_dir, nome_arquivo)

                    with open(caminho_temp, "wb") as f:
                        f.write(arquivo.getbuffer())

                    # Chama o motor de OCR
                    resultados = ler_placa_motor(caminho_temp)
                    
                    st.session_state.dados_ocr = resultados
                    st.success("Dados extraídos com sucesso! Verifique o formulário abaixo.")
                    
                    # Limpa o arquivo temporário
                    if os.path.exists(caminho_temp):
                        os.remove(caminho_temp)
                        
                except Exception as e:
                    st.error(f"Erro técnico no processamento da pasta temp: {e}")

    # 4. FORMULÁRIO DE CADASTRO
    st.title("Cadastro de Motor")
    d = st.session_state.dados_ocr

    with st.form("form_cadastro_motor"):
        col1, col2 = st.columns(2)

        with col1:
            marca = st.text_input("Marca", value=d.get("Marca", ""))
            modelo = st.text_input("Modelo")
            carcaca = st.text_input("Carcaça")
            peso = st.number_input("Peso (kg)", 0.0)
            
            try:
                pot_str = str(d.get("Potência (kW/HP)", "0.0")).replace(",", ".")
                pot_valor = float(pot_str)
            except:
                pot_valor = 0.0
            potencia = st.number_input("Potência", value=pot_valor)
            
            unidade = st.selectbox("Unidade", ["cv", "kW"])
            
            try:
                tensao_raw = str(d.get("Tensão (V)", "0.0")).split("/")[0].strip()
                tensao_ocr = float(tensao_raw.replace(",", "."))
            except:
                tensao_ocr = 0.0
            tensao = st.number_input("Tensão (V)", value=tensao_ocr)
            
            amperagem = st.number_input("Amperagem (A)", 0.0)

        with col2:
            polos = st.selectbox("Polos", [2, 4, 6, 8], index=1)
            fp = st.number_input("Fator de potência", 0.0, 1.0, 0.85)
            
            try:
                rpm_ocr = int(float(str(d.get("Rotação (RPM)", "0")).replace(",", ".")))
            except:
                rpm_ocr = 0
            rpm = st.number_input("RPM", value=rpm_ocr)
            
            ip = st.text_input("Grau de Proteção (IP)", value="IP55")
            isolamento = st.text_input("Classe de Isolamento", value="F")
            fs = st.number_input("Fator de Serviço", 0.0, value=1.0)
            refrigeracao = st.text_input("Refrigeração", value="TFVE")
            ligacao = st.text_input("Ligação", value="Δ / Y")

        desenho = st.text_input("Caminho da imagem/desenho")

        submit = st.form_submit_button("Salvar Motor", use_container_width=True)

        if submit:
            if marca and modelo:
                dados_para_salvar = (
                    marca, modelo, carcaca, peso, potencia, unidade,
                    tensao, amperagem, polos, fp, rpm, ip,
                    isolamento, fs, refrigeracao, ligacao, desenho
                )

                try:
                    salvar_motor(dados_para_salvar)
                    st.balloons()
                    st.success(f"Motor {modelo} salvo!")
                    st.session_state.dados_ocr = {
                        "Marca": "", "Tensão (V)": 0.0, "Potência (kW/HP)": 0.0, 
                        "Rotação (RPM)": 0, "Frequência (Hz)": "", "Corrente (A)": 0.0
                    }
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
            else:
                st.warning("Marca e Modelo são obrigatórios.")
