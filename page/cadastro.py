import streamlit as st
from services.ocr_motor import ler_placa_motor

st.title("Cadastro de Motor")

# =============================
# Inicializa campos
# =============================

campos = [
    "marca","modelo","potencia","tensao","corrente",
    "rpm","frequencia","fp","carcaca","ip",
    "isolacao","regime","rolamento_dianteiro",
    "rolamento_traseiro","peso","diametro_eixo",
    "comprimento_pacote","numero_ranhuras",
    "ligacao","fabricacao"
]

for campo in campos:
    if campo not in st.session_state:
        st.session_state[campo] = ""

# =============================
# OCR
# =============================

st.subheader("Escanear placa")

imagem = st.file_uploader(
    "Envie foto da placa do motor",
    type=["png","jpg","jpeg"]
)

if imagem:
    if st.button("Ler placa"):
        dados = ler_placa_motor(imagem)

        # 🔥 PREENCHE AUTOMATICAMENTE
        for chave, valor in dados.items():
            if chave in st.session_state:
                st.session_state[chave] = valor

        st.success("Dados preenchidos automaticamente!")

# =============================
# FORMULÁRIO
# =============================

st.subheader("Dados do Motor")

st.session_state.marca = st.text_input(
    "Marca", value=st.session_state.marca)

st.session_state.modelo = st.text_input(
    "Modelo", value=st.session_state.modelo)

st.session_state.potencia = st.text_input(
    "Potência", value=st.session_state.potencia)

st.session_state.tensao = st.text_input(
    "Tensão", value=st.session_state.tensao)

st.session_state.corrente = st.text_input(
    "Corrente", value=st.session_state.corrente)

st.session_state.rpm = st.text_input(
    "RPM", value=st.session_state.rpm)

st.session_state.frequencia = st.text_input(
    "Frequência", value=st.session_state.frequencia)

st.session_state.fp = st.text_input(
    "Fator de Potência", value=st.session_state.fp)

st.session_state.carcaca = st.text_input(
    "Carcaça", value=st.session_state.carcaca)

st.session_state.ip = st.text_input(
    "Grau IP", value=st.session_state.ip)

st.session_state.isolacao = st.text_input(
    "Classe de Isolação", value=st.session_state.isolacao)

st.session_state.regime = st.text_input(
    "Regime", value=st.session_state.regime)

st.session_state.rolamento_dianteiro = st.text_input(
    "Rolamento Dianteiro", value=st.session_state.rolamento_dianteiro)

st.session_state.rolamento_traseiro = st.text_input(
    "Rolamento Traseiro", value=st.session_state.rolamento_traseiro)

st.session_state.peso = st.text_input(
    "Peso", value=st.session_state.peso)

st.session_state.diametro_eixo = st.text_input(
    "Diâmetro do Eixo", value=st.session_state.diametro_eixo)

st.session_state.comprimento_pacote = st.text_input(
    "Comprimento do Pacote", value=st.session_state.comprimento_pacote)

st.session_state.numero_ranhuras = st.text_input(
    "Número de Ranhuras", value=st.session_state.numero_ranhuras)

st.session_state.ligacao = st.text_input(
    "Ligação", value=st.session_state.ligacao)

st.session_state.fabricacao = st.text_input(
    "Ano de Fabricação", value=st.session_state.fabricacao)

# =============================
# SALVAR
# =============================

if st.button("Salvar Motor"):
    motor = {campo: st.session_state[campo] for campo in campos}

    st.success("Motor salvo!")
    st.json(motor)
