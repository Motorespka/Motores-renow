import streamlit as st
import sys
import os
from db import salvar_motor
# Certifique-se de que ler_placa_motor está importado corretamente
# from ocr_module import ler_placa_motor 

def show():
    st.markdown("### 🔐 Área Restrita: Cadastro Técnico")

    # Autenticação Simples
    senha_digitada = st.text_input("Insira a chave de acesso", type="password")
    # Use um valor padrão para evitar erro de None no os.getenv
    
senha_correta = st.secrets["APP_PASSWORD"]
if senha_digita == senha_correta:
    st.sucess("Acesso liberado")
else: 
     if senha_digita != "":   
    st.warning("senha incorreta")
st.stop()
    

    # --- Upload e OCR ---
    st.subheader("📸 Captura de Dados via Placa")
    arquivo = st.file_uploader("Envie foto da placa/cálculo do motor", type=["jpg", "png", "jpeg"])
    
    # Dicionário inicial para preencher os campos (vazio por padrão)
    dados_ocr = {}

    if arquivo:
        # Mostra a imagem carregada
        st.image(arquivo, caption="Imagem Carregada", width=300)
        
        # Processamento (Opcional: Adicione um botão para disparar o OCR e economizar API)
        if st.button("Executar OCR"):
            with st.spinner("Extraindo dados da imagem..."):
                # Salva temporariamente para processar (usando o nome original para evitar conflitos)
                caminho_temp = os.path.join("temp", arquivo.name)
                os.makedirs("temp", exist_ok=True)
                
                with open(caminho_temp, "wb") as f:
                    f.write(arquivo.getbuffer())
                
                # Chamada da sua função de OCR
                # resultado = ler_placa_motor(caminho_temp)
                # dados_ocr = resultado.get("campos_extraidos", {}) 
                st.info("Texto extraído com sucesso (Simulação).")

    # --- Formulário de Cadastro ---
    st.title("Cadastro de Motor")
    
    # O uso do 'key' no input permite pré-preencher com dados do OCR se disponíveis
    with st.form("form_cadastro_motor"):
        col1, col2 = st.columns(2)

        with col1:
            marca = st.text_input("Marca")
            modelo = st.text_input("Modelo")
            carcaca = st.text_input("Carcaça")
            peso = st.number_input("Peso (kg)", min_value=0.0, step=0.1)
            potencia = st.number_input("Potência", min_value=0.0, step=0.1)
            unidade = st.selectbox("Unidade", ["cv", "kW"])
            tensao = st.number_input("Tensão (V)", min_value=0.0, step=1.0)
            amperagem = st.number_input("Amperagem (A)", min_value=0.0, step=0.1)

        with col2:
            polos = st.selectbox("Polos", [2, 4, 6, 8])
            fp = st.number_input("Fator de potência", min_value=0.0, max_value=1.0, step=0.01)
            rpm = st.number_input("RPM", min_value=0, step=10)
            ip = st.text_input("Grau de Proteção (IP)")
            isolamento = st.text_input("Classe de Isolamento")
            fs = st.number_input("Fator de Serviço (FS)", min_value=0.0, step=0.01)
            refrigeracao = st.text_input("Refrigeração")
            ligacao = st.text_input("Ligação")

        desenho = st.text_input("Caminho da imagem/desenho")

        # Botão de submissão do formulário
        submit = st.form_submit_button("Salvar Motor", use_container_width=True)

        if submit:
            if marca and modelo:
                dados = (
                    marca, modelo, carcaca, peso, potencia, unidade,
                    tensao, amperagem, polos, fp, rpm, ip,
                    isolamento, fs, refrigeracao, ligacao, desenho
                )
                
                try:
                    inserir_motor(dados)
                    st.balloons()
                    st.success(f"Motor {modelo} registrado com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao salvar no banco: {e}")
            else:
                st.warning("Os campos 'Marca' e 'Modelo' são obrigatórios.")
