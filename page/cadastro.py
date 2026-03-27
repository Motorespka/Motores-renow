import streamlit as st
from services.ocr_motor import ler_placa_motor


def show():

    st.header("📋 Cadastro de Motor")

    # ---------------- OCR ----------------

    st.subheader("📸 Ler placa do motor (OCR)")

    imagem = st.file_uploader(
        "Envie foto da placa do motor",
        type=["jpg", "jpeg", "png"]
    )

    dados_ocr = {}

    if imagem:
        with st.spinner("Lendo placa..."):
            dados_ocr = ler_placa_motor(imagem)

        st.success("Placa lida com sucesso!")

    # ---------------- FORMULÁRIO ----------------

    st.subheader("🧾 Dados do Motor")

    col1, col2 = st.columns(2)

    with col1:

        marca = st.text_input(
            "Marca",
            value=dados_ocr.get("Marca", "")
        )

        modelo = st.text_input(
            "Modelo",
            value=dados_ocr.get("Modelo", "")
        )

        potencia = st.text_input(
            "Potência",
            value=dados_ocr.get("Potência", "")
        )

        tensao = st.text_input(
            "Tensão",
            value=dados_ocr.get("Tensão", "")
        )

        corrente = st.text_input(
            "Corrente (A)",
            value=dados_ocr.get("Corrente", "")
        )

    with col2:

        rpm = st.text_input(
            "RPM",
            value=dados_ocr.get("RPM", "")
        )

        frequencia = st.text_input(
            "Frequência (Hz)",
            value=dados_ocr.get("Frequência", "")
        )

        rendimento = st.text_input(
            "Rendimento (%)",
            value=dados_ocr.get("Rendimento", "")
        )

        fp = st.text_input(
            "Fator de Potência",
            value=dados_ocr.get("FP", "")
        )

        carcaca = st.text_input(
            "Carcaça",
            value=dados_ocr.get("Carcaça", "")
        )

    # ---------------- DADOS DE REBOBINAGEM ----------------

    st.subheader("🔧 Dados de Rebobinagem")

    col3, col4 = st.columns(2)

    with col3:

        ranhuras = st.number_input("Número de Ranhuras", 0)
        polos = st.number_input("Número de Polos", 0)
        passo = st.text_input("Passo da Bobina")

    with col4:

        fio = st.text_input("Bitola do Fio")
        espiras = st.number_input("Espiras por Bobina", 0)
        ligacao = st.selectbox(
            "Ligação",
            ["Estrela", "Triângulo", "Série", "Paralelo"]
        )

    observacoes = st.text_area("Observações")

    # ---------------- SALVAR ----------------

    if st.button("💾 Salvar Motor"):

        dados_motor = {
            "Marca": marca,
            "Modelo": modelo,
            "Potência": potencia,
            "Tensão": tensao,
            "Corrente": corrente,
            "RPM": rpm,
            "Frequência": frequencia,
            "Rendimento": rendimento,
            "FP": fp,
            "Carcaça": carcaca,
            "Ranhuras": ranhuras,
            "Polos": polos,
            "Passo": passo,
            "Fio": fio,
            "Espiras": espiras,
            "Ligação": ligacao,
            "Observações": observacoes
        }

        # depois vamos conectar com banco
        st.success("Motor cadastrado (simulação)")
        st.json(dados_motor)
