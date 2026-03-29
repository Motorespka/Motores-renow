import streamlit as st

# ===== V4 IMPORTS =====
from services.ocr_motor import ler_placa_motor
from services.fabrica_motor import analise_fabrica
from services.weg_engine import analise_weg
from services.aprendizado_motor import (
    salvar_motor,
    sugestao_inteligente
)
from services.diagnostico_ia import diagnostico_motor

# ===== V6 AUTO MODULES =====
from services.auto_modules import executar_modulos


st.title("⚙️ Moto-Renow — Sistema Inteligente")

modo = st.radio(
    "Modo de operação",
    [
        "🔧 Simplificado",
        "🏭 Engenharia Industrial",
        "🔵 Modo WEG",
        "⚡ Diagnóstico IA",
        "🧬 Auto Sistema (V6)"
    ],
)

imagem = st.camera_input("Fotografar placa do motor")

dados = {}
engenharia = {}
fabrica = {}

# =====================================================
# CORE DO SISTEMA (V4)
# =====================================================

if imagem:

    dados, engenharia, texto = ler_placa_motor(imagem)

    st.success("OCR concluído")

    with st.expander("Texto detectado"):
        st.write(texto)

    # ---------- APRENDIZADO V4 ----------
    sugestao = sugestao_inteligente(dados)

    if sugestao:
        st.info(
            f"Baseado em {sugestao['baseado_em']} motores\n"
            f"Espiras sugeridas: {sugestao['espiras_sugeridas']}"
        )

    # ---------- FÁBRICA V5 ----------
    fabrica = analise_fabrica(dados)

# =====================================================
# FORMULÁRIO
# =====================================================

marca = st.text_input("Marca", dados.get("marca",""))
rpm = st.text_input("RPM", dados.get("rpm",""))
tensao = st.text_input("Tensão", dados.get("tensao",""))
corrente = st.text_input("Corrente", dados.get("corrente",""))

# =====================================================
# MODO SIMPLES (V4)
# =====================================================

if modo == "🔧 Simplificado" and engenharia:

    st.subheader("Resumo Técnico")

    st.write("Tipo:", engenharia.get("tipo_motor"))
    st.write("Espiras:", engenharia.get("espiras_originais"))
    st.write("Fio:", engenharia.get("fio_original"))

# =====================================================
# ENGENHARIA INDUSTRIAL (V5)
# =====================================================

if modo == "🏭 Engenharia Industrial":

    st.subheader("Engenharia")

    st.write("Potência estimada:", fabrica.get("potencia_kw"), "kW")

    bitola = fabrica.get("bitola")

    if bitola:
        st.write("Área fio:", bitola["area"], "mm²")
        st.write("Diâmetro fio:", bitola["diametro"], "mm")

# =====================================================
# MODO WEG (V5)
# =====================================================

if modo == "🔵 Modo WEG":

    weg = analise_weg(dados, fabrica)

    st.subheader("Diagnóstico WEG")

    st.write("Polos estimados:", weg["polos_estimados"])
    st.write("Diagnóstico:", weg["diagnostico"])

# =====================================================
# DIAGNÓSTICO IA (V4)
# =====================================================

if modo == "⚡ Diagnóstico IA":

    avisos = diagnostico_motor(
        dados,
        engenharia,
        fabrica,
    )

    st.subheader("Diagnóstico Inteligente")

    for aviso in avisos:
        st.warning(aviso)

# =====================================================
# V6 — AUTO SISTEMA
# =====================================================

if modo == "🧬 Auto Sistema (V6)":

    st.subheader("Sistema Auto Modular")

    executar_modulos(dados, engenharia, fabrica)

# =====================================================
# SALVAR + APRENDER (V4)
# =====================================================

if st.button("Salvar Motor"):

    salvar_motor(dados, engenharia)

    st.success("Motor salvo — IA Aprendeu!")
