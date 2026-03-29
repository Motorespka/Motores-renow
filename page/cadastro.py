import streamlit as st

from services.ocr_motor import ler_placa_motor
from services.fabrica_motor import analise_fabrica
from services.weg_engine import analise_weg
from services.aprendizado_motor import salvar_motor, sugestao_inteligente
from services.diagnostico_ia import diagnostico_motor

st.title("⚙️ Moto-Renow — Sistema Inteligente")

modo = st.radio(
    "Modo",
    [
        "🔧 Simplificado",
        "🏭 Engenharia Industrial",
        "🔵 Modo WEG",
        "⚡ Diagnóstico IA",
    ],
)

imagem = st.camera_input("Fotografar placa ou ficha")

dados = {}
engenharia = {}

if imagem:

    dados, engenharia, texto = ler_placa_motor(imagem)

    st.success("OCR concluído")

    with st.expander("Texto lido"):
        st.write(texto)

    sugestao = sugestao_inteligente(dados)

    if sugestao:
        st.info(
            f"🧠 Baseado em {sugestao['baseado_em']} motores semelhantes\n"
            f"Espiras sugeridas: {sugestao['espiras_sugeridas']}"
        )

# ======================
# FORMULÁRIO
# ======================
marca = st.text_input("Marca", dados.get("marca",""))
rpm = st.text_input("RPM", dados.get("rpm",""))
tensao = st.text_input("Tensão", dados.get("tensao",""))
corrente = st.text_input("Corrente", dados.get("corrente",""))

# ======================
# SIMPLES
# ======================
if modo == "🔧 Simplificado" and engenharia:

    st.subheader("Resumo Técnico")
    st.write("Tipo:", engenharia.get("tipo_motor"))
    st.write("Espiras:", engenharia.get("espiras_originais"))
    st.write("Fio:", engenharia.get("fio_original"))

# ======================
# ENGENHARIA
# ======================
if modo == "🏭 Engenharia Industrial":

    fabrica = analise_fabrica(dados)

    st.subheader("Engenharia")

    st.write("Potência estimada:", fabrica.get("potencia_kw"), "kW")

    bitola = fabrica.get("bitola")

    if bitola:
        st.write("Área fio:", bitola["area"], "mm²")
        st.write("Diâmetro fio:", bitola["diametro"], "mm")

# ======================
# WEG
# ======================
if modo == "🔵 Modo WEG":

    fabrica = analise_fabrica(dados)
    weg = analise_weg(dados, fabrica)

    st.subheader("Diagnóstico WEG")

    st.write("Polos estimados:", weg["polos_estimados"])
    st.write("Diagnóstico:", weg["diagnostico"])

# ======================
# DIAGNÓSTICO IA
# ======================
if modo == "⚡ Diagnóstico IA":

    fabrica = analise_fabrica(dados)

    avisos = diagnostico_motor(
        dados,
        engenharia,
        fabrica,
    )

    st.subheader("⚡ Diagnóstico Inteligente")

    for aviso in avisos:
        st.write(aviso)

# ======================
# SALVAR + APRENDER
# ======================
if st.button("Salvar Motor"):

    salvar_motor(dados, engenharia)

    st.success("Motor salvo — IA Aprendeu!")
