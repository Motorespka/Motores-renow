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

    # ===== INICIALIZAÇÃO DO ESTADO (Para o formulário receber o OCR) =====
    if "dados_ocr" not in st.session_state:
        st.session_state.dados_ocr = {}

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

                # INTEGRAÇÃO REAL: Chama o seu arquivo ocr_motor.py
                resultado = ler_placa_motor(caminho_temp)
                st.session_state.dados_ocr = resultado
                st.success("Dados extraídos com sucesso!")

    # ===== FORMULÁRIO =====
    st.title("Cadastro de Motor")

    # Pegamos os dados extraídos pelo OCR (se houver) para preencher os campos
    d = st.session_state.dados_ocr

    with st.form("form_cadastro_motor"):

        col1, col2 = st.columns(2)

        with col1:
            marca = st.text_input("Marca", value=d.get("Marca", ""))
            modelo = st.text_input("Modelo")
            carcaca = st.text_input("Carcaça")
            peso = st.number_input("Peso (kg)", 0.0)
            
            # Tratamento de número para a potência
            try:
                pot_val = float(str(d.get("Potência (kW/HP)", "0.0")).replace(",", "."))
            except:
                pot_val = 0.0
            potencia = st.number_input("Potência", value=pot_val)
            
            unidade = st.selectbox("Unidade", ["cv", "kW"])
            
            # Tratamento para Tensão
            try:
                tensao_val = float(str(d.get("Tensão (V)", "0.0")).split("/")[0].strip())
            except:
                tensao_val = 0.0
            tensao = st.number_input("Tensão (V)", value=tensao_val)
            
            amperagem = st.number_input("Amperagem (A)", 0.0)

        with col2:
            polos = st.selectbox("Polos", [2, 4, 6, 8])
            fp = st.number_input("Fator de potência", 0.0, 1.0)
            
            # Tratamento para RPM
            try:
                rpm_val = int(d.get("Rotação (RPM)", 0))
            except:
                rpm_val = 0
            rpm = st.number_input("RPM", value=rpm_val)
            
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

                # CORREÇÃO: salvar_motor (minúsculo) para bater com seu import e db.py
                salvar_motor(dados)

                st.balloons()
                st.success(f"Motor {modelo} salvo!")
                # Limpa os dados do OCR após salvar
                st.session_state.dados_ocr = {}

            else:
                st.warning("Marca e Modelo são obrigatórios.")

refaça sem diminuir o codigo so aumenta se necessario
