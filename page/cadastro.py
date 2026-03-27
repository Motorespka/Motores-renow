import streamlit as st
from services.ocr_motor import ler_placa_motor

def show():
st.title("Cadastro de Motor")

# =============================
# CAMPOS DO MOTOR
# =============================

campos = [
    "marca","modelo","potencia","tensao","corrente",
    "rpm","frequencia","fp","carcaca","ip",
    "isolacao","regime","rolamento_dianteiro",
    "rolamento_traseiro","peso","diametro_eixo",
    "comprimento_pacote","numero_ranhuras",
    "ligacao","fabricacao"
]

# Inicializa session_state
for campo in campos:
    if campo not in st.session_state:
        st.session_state[campo] = ""

# =============================
# OCR
# =============================

st.subheader("📸 Escanear placa")

imagem = st.file_uploader(
    "Envie foto da placa do motor",
    type=["png","jpg","jpeg"]
)

if imagem:
    st.image(imagem, width=300)

    if st.button("🔎 Ler placa"):

        with st.spinner("Lendo placa..."):
            dados = ler_placa_motor(imagem)

        # Preenchimento automático
        for chave, valor in dados.items():
            if chave in st.session_state:
                st.session_state[chave] = valor

        st.success("✅ Dados preenchidos automaticamente!")

        # força atualização visual
        st.rerun()

# =============================
# FORMULÁRIO
# =============================

st.subheader("⚙️ Dados do Motor")

col1, col2 = st.columns(2)

with col1:
    st.text_input("Marca", key="marca")
    st.text_input("Modelo", key="modelo")
    st.text_input("Potência", key="potencia")
    st.text_input("Tensão", key="tensao")
    st.text_input("Corrente", key="corrente")
    st.text_input("RPM", key="rpm")
    st.text_input("Frequência", key="frequencia")
    st.text_input("Fator de Potência", key="fp")
    st.text_input("Carcaça", key="carcaca")
    st.text_input("Grau IP", key="ip")

with col2:
    st.text_input("Classe de Isolação", key="isolacao")
    st.text_input("Regime", key="regime")
    st.text_input("Rolamento Dianteiro", key="rolamento_dianteiro")
    st.text_input("Rolamento Traseiro", key="rolamento_traseiro")
    st.text_input("Peso", key="peso")
    st.text_input("Diâmetro do Eixo", key="diametro_eixo")
    st.text_input("Comprimento do Pacote", key="comprimento_pacote")
    st.text_input("Número de Ranhuras", key="numero_ranhuras")
    st.text_input("Ligação", key="ligacao")
    st.text_input("Ano de Fabricação", key="fabricacao")

# =============================
# SALVAR
# =============================

if st.button("💾 Salvar Motor", use_container_width=True):

    motor = {campo: st.session_state[campo] for campo in campos}

    st.success("Motor salvo com sucesso!")
    st.json(motor)
