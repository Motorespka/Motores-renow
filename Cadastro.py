import streamlit as st
from ocr_motor import ler_placa_motor
from PIL import Image


def show():

    st.header("Cadastro de Motor")

    # =============================
    # SESSION STATE PADRÃO
    # =============================
    campos = [
        "Marca",
        "Modelo",
        "Carcaça",
        "Potência",
        "Tensão",
        "Corrente",
        "Rotação",
        "Frequência",
        "Polos",
        "IP",
        "Isolamento"
    ]

    for campo in campos:
        if campo not in st.session_state:
            st.session_state[campo] = ""

    # =============================
    # UPLOAD DA IMAGEM
    # =============================
    imagem = st.file_uploader(
        "📷 Tire foto da placa do motor",
        type=["jpg", "jpeg", "png"]
    )

    # =============================
    # BOTÃO OCR
    # =============================
    if imagem:

        img = Image.open(imagem)
        st.image(img, caption="Imagem enviada", use_container_width=True)

        if st.button("🔎 Escanear placa automaticamente"):

            with st.spinner("Lendo placa do motor..."):

                dados = ler_placa_motor(img)

                # JOGA RESULTADO NO FORMULÁRIO
                for chave, valor in dados.items():
                    if chave in st.session_state:
                        st.session_state[chave] = valor

            st.success("✅ Dados preenchidos automaticamente!")

    st.divider()

    # =============================
    # FORMULÁRIO
    # =============================
    with st.form("cadastro_motor"):

        marca = st.text_input("Marca", key="Marca")
        modelo = st.text_input("Modelo", key="Modelo")
        carcaca = st.text_input("Carcaça", key="Carcaça")
        potencia = st.text_input("Potência", key="Potência")
        tensao = st.text_input("Tensão", key="Tensão")
        corrente = st.text_input("Corrente", key="Corrente")
        rotacao = st.text_input("Rotação", key="Rotação")
        frequencia = st.text_input("Frequência", key="Frequência")
        polos = st.text_input("Polos", key="Polos")
        ip = st.text_input("IP", key="IP")
        isolamento = st.text_input("Isolamento", key="Isolamento")

        salvar = st.form_submit_button("💾 Salvar Motor")

    # =============================
    # SALVAR
    # =============================
    if salvar:

        motor = {campo: st.session_state[campo] for campo in campos}

        st.success("Motor salvo!")
        st.json(motor)
