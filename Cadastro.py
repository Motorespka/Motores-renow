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
        st.session_state.dados_ocr = {}
    
    if "form_version" not in st.session_state:
        st.session_state.form_version = 0

    # 3. UPLOAD E OCR
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
                    base_dir = os.path.dirname(os.path.abspath(__file__))
                    temp_dir = os.path.join(base_dir, "temp")
                    os.makedirs(temp_dir, exist_ok=True)
                    
                    nome_arquivo = arquivo.name.replace(" ", "_")
                    caminho_temp = os.path.join(temp_dir, nome_arquivo)

                    with open(caminho_temp, "wb") as f:
                        f.write(arquivo.getbuffer())

                    # Chama o motor de OCR
                    resultados = ler_placa_motor(caminho_temp)
                    
                    # Atualiza os dados e incrementa a versão para forçar o formulário a atualizar
                    st.session_state.dados_ocr = resultados
                    st.session_state.form_version += 1
                    
                    if os.path.exists(caminho_temp):
                        os.remove(caminho_temp)
                    
                    st.rerun() 
                        
                except Exception as e:
                    st.error(f"Erro técnico no processamento da pasta temp: {e}")

    # 4. FORMULÁRIO DE CADASTRO
    st.title("Cadastro de Motor")
    d = st.session_state.dados_ocr

    # Função auxiliar para buscar dados ignorando maiúsculas/minúsculas
    def buscar(termo):
        for k, v in d.items():
            if termo.lower() in k.lower():
                return str(v)
        return ""

    # O formulário "renasce" a cada nova leitura de OCR devido à key dinâmica
    with st.form(key=f"form_motor_v_{st.session_state.form_version}"):
        col1, col2 = st.columns(2)

        with col1:
            marca = st.text_input("Marca", value=buscar("Marca"))
            modelo = st.text_input("Modelo")
            carcaca = st.text_input("Carcaça")
            peso = st.number_input("Peso (kg)", 0.0)
            
            # Tratamento de Potência
            try:
                pot_raw = buscar("Potência").replace(",", ".")
                pot_valor = float(pot_raw) if pot_raw else 0.0
            except:
                pot_valor = 0.0
            potencia = st.number_input("Potência", value=pot_valor)
            
            unidade = st.selectbox("Unidade", ["cv", "kW"])
            
            # Tratamento de Tensão
            try:
                tensao_raw = buscar("Tensão").split("/")[0].strip().replace(",", ".")
                tensao_ocr = float(tensao_raw) if tensao_raw else 0.0
            except:
                tensao_ocr = 0.0
            tensao = st.number_input("Tensão (V)", value=tensao_ocr)
            
            # Tratamento de Amperagem/Corrente
            try:
                amp_raw = buscar("Corrente").replace(",", ".")
                amp_valor = float(amp_raw) if amp_raw else 0.0
            except:
                amp_valor = 0.0
            amperagem = st.number_input("Amperagem (A)", value=amp_valor)

        with col2:
            polos = st.selectbox("Polos", [2, 4, 6, 8], index=1)
            fp = st.number_input("Fator de potência", 0.0, 1.0, 0.85)
            
            # Tratamento de RPM
            try:
                rpm_raw = buscar("Rotação").replace(",", ".")
                rpm_ocr = int(float(rpm_raw)) if rpm_raw else 0
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
                    # Limpa os dados para o próximo cadastro
                    st.session_state.dados_ocr = {}
                    st.session_state.form_version += 1
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
            else:
                st.warning("Marca e Modelo são obrigatórios!")
