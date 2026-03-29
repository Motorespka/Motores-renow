import streamlit as st
from services.ocr_motor import ler_placa_motor

st.title("⚙️ Cadastro de Motor")

imagem = st.camera_input("📸 Fotografar placa ou ficha do motor")

dados = {}
engenharia = {}

if imagem:

    with st.spinner("Lendo motor..."):
        dados, engenharia, texto = ler_placa_motor(imagem)

    st.success("Leitura concluída")

    with st.expander("Texto reconhecido"):
        st.write(texto)


# ==========================
# FORMULÁRIO
# ==========================
st.subheader("Dados do Motor")

marca = st.text_input("Marca", dados.get("marca", ""))
modelo = st.text_input("Modelo", dados.get("modelo", ""))
rpm = st.text_input("RPM", dados.get("rpm", ""))
tensao = st.text_input("Tensão", dados.get("tensao", ""))
corrente = st.text_input("Corrente", dados.get("corrente", ""))
isolacao = st.text_input("Isolação", dados.get("isolacao", ""))
regime = st.text_input("Regime", dados.get("regime", ""))
polos = st.text_input("Polos", dados.get("polos", ""))


# ==========================
# PAINEL ENGENHEIRO
# ==========================
if engenharia:

    st.subheader("🧠 Análise Técnica")

    st.write("Tipo de Motor:", engenharia.get("tipo_motor", ""))
    st.write("Passos:", engenharia.get("passos", ""))
    st.write("Espiras Originais:", engenharia.get("espiras_originais", ""))
    st.write("Média Espiras:", engenharia.get("media_espiras", ""))
    st.write("Espiras +10%:", engenharia.get("espiras_mais_10", ""))
    st.write("Espiras -10%:", engenharia.get("espiras_menos_10", ""))
    st.write("Fio Original:", engenharia.get("fio_original", ""))


if st.button("Salvar Motor"):
    st.success("Motor cadastrado com sucesso!")
