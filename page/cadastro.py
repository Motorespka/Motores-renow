import streamlit as st

from services.ocr_motor import ler_placa_motor
from services.fabrica_motor import analise_fabrica
from services.weg_engine import analise_weg

st.title("⚙️ Moto-Renow — Cadastro Inteligente")

modo = st.radio(
    "Modo de análise",
    ["🔧 Simplificado", "🏭 Engenharia Industrial", "🔵 Modo WEG"]
)

imagem = st.camera_input("Fotografar placa ou ficha")

dados = {}
engenharia = {}

if imagem:

    dados, engenharia, texto = ler_placa_motor(imagem)

    st.success("OCR concluído")

    with st.expander("Texto lido"):
        st.write(texto)


# ===================
# FORMULÁRIO
# ===================
marca = st.text_input("Marca", dados.get("marca",""))
rpm = st.text_input("RPM", dados.get("rpm",""))
tensao = st.text_input("Tensão", dados.get("tensao",""))
corrente = st.text_input("Corrente", dados.get("corrente",""))

# ===================
# SIMPLIFICADO
# ===================
if modo == "🔧 Simplificado" and engenharia:

    st.subheader("Resumo Técnico")

    st.write("Tipo:", engenharia.get("tipo_motor"))
    st.write("Espiras:", engenharia.get("espiras_originais"))
    st.write("Fio:", engenharia.get("fio_original"))


# ===================
# ENGENHARIA
# ===================
if modo == "🏭 Engenharia Industrial":

    fabrica = analise_fabrica(dados)

    st.subheader("Engenharia")

    st.write("Potência estimada:", fabrica.get("potencia_kw"), "kW")

    bitola = fabrica.get("bitola")

    if bitola:
        st.write("Área fio:", bitola["area"], "mm²")
        st.write("Diâmetro fio:", bitola["diametro"], "mm")


# ===================
# MODO WEG
# ===================
if modo == "🔵 Modo WEG":

    fabrica = analise_fabrica(dados)
    weg = analise_weg(dados, fabrica)

    st.subheader("Diagnóstico WEG")

    st.write("Polos estimados:", weg["polos_estimados"])
    st.write("Diagnóstico:", weg["diagnostico"])


if st.button("Salvar Motor"):
    st.success("Motor salvo!")
