import streamlit as st
from services.ocr_motor import ler_placa_motor


def iniciar_campos():

    campos = [
        "marca","modelo","carcaca","serie","ano",
        "potencia","unidade","tensao","corrente",
        "frequencia","fp","fs","polos","rpm",
        "ip","isolamento","refrigeracao",
        "ligacao","peso","rendimento"
    ]

    for c in campos:
        if c not in st.session_state:
            st.session_state[c] = ""


def preencher_ocr(dados):

    mapa = {
        "Marca":"marca",
        "Modelo":"modelo",
        "Carcaça":"carcaca",
        "Potência":"potencia",
        "Unidade":"unidade",
        "Tensão":"tensao",
        "Corrente":"corrente",
        "Frequência":"frequencia",
        "Fator de potência":"fp",
        "Fator de Serviço":"fs",
        "Polos":"polos",
        "Rotação":"rpm",
        "IP":"ip",
        "Isolamento":"isolamento",
        "Refrigeração":"refrigeracao",
        "Ligação":"ligacao",
        "Peso":"peso",
        "Rendimento":"rendimento",
        "Ano":"ano",
        "Série":"serie"
    }

    for k,v in mapa.items():
        if k in dados:
            st.session_state[v] = dados[k]


def show():

    iniciar_campos()

    st.header("📸 Leitura automática da placa")

    imagem = st.file_uploader(
        "Enviar foto da placa do motor",
        type=["jpg","jpeg","png"]
    )

    if imagem:

        st.image(imagem, width=300)

        with st.spinner("Lendo placa..."):
            dados = ler_placa_motor(imagem)

        preencher_ocr(dados)

        st.success("Dados detectados!")

        with st.expander("🔎 Dados OCR"):
            st.json(dados)

    # ============================
    # FORMULÁRIO COMPLETO
    # ============================

    st.header("Cadastro do Motor")

    col1, col2 = st.columns(2)

    with col1:

        st.text_input("Marca", key="marca")
        st.text_input("Modelo", key="modelo")
        st.text_input("Carcaça", key="carcaca")
        st.text_input("Nº Série", key="serie")
        st.text_input("Ano", key="ano")

        st.text_input("Potência", key="potencia")
        st.selectbox("Unidade", ["cv","kW","hp"], key="unidade")

        st.text_input("Tensão", key="tensao")
        st.text_input("Corrente", key="corrente")
        st.text_input("Frequência", key="frequencia")

    with col2:

        st.text_input("Fator de Potência", key="fp")
        st.text_input("Fator de Serviço", key="fs")
        st.text_input("Polos", key="polos")
        st.text_input("RPM", key="rpm")

        st.text_input("IP", key="ip")
        st.text_input("Isolamento", key="isolamento")
        st.text_input("Refrigeração", key="refrigeracao")
        st.text_input("Ligação", key="ligacao")

        st.text_input("Peso", key="peso")
        st.text_input("Rendimento", key="rendimento")

    if st.button("💾 Salvar Motor", use_container_width=True):

        dados_salvos = dict(st.session_state)

        st.success("Motor cadastrado!")
        st.json(dados_salvos)
