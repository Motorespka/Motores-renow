import streamlit as st
import io

from ocr.ocr_motor import ler_placa_motor
from services.database import salvar_motor


def show():

    st.title("Cadastro de Motor")

    # =============================
    # CAMPOS DO MOTOR
    # =============================
    campos = [
        "marca", "modelo", "potencia", "tensao", "corrente",
        "rpm", "frequencia", "fp", "carcaca", "ip",
        "isolacao", "regime", "rolamento_dianteiro",
        "rolamento_traseiro", "peso", "diametro_eixo",
        "comprimento_pacote", "numero_ranhuras",
        "ligacao", "fabricacao",
    ]

    for campo in campos:
        if campo not in st.session_state:
            st.session_state[campo] = ""

    if "original" not in st.session_state:
        st.session_state["original"] = "Sim"

    # =============================
    # FOTO DA PLACA (EASYOCR)
    # =============================
    st.subheader("📸 Foto da placa do motor")

    imagem = st.file_uploader(
        "Enviar foto ou screenshot da placa",
        type=["jpg", "jpeg", "png", "webp"]
    )

    if imagem and st.button("🔎 Ler placa (OCR)", type="primary"):

        with st.spinner("Lendo placa do motor..."):

            dados = ler_placa_motor(
                io.BytesIO(imagem.getvalue())
            )

            texto = dados.get("texto_detectado", "")

            # salva texto bruto
            st.session_state["texto_ocr"] = texto

            # autopreenche simples
            texto_upper = texto.upper()

            if "WEG" in texto_upper:
                st.session_state["marca"] = "WEG"
            elif "SIEMENS" in texto_upper:
                st.session_state["marca"] = "SIEMENS"
            elif "ABB" in texto_upper:
                st.session_state["marca"] = "ABB"

            st.success("OCR concluído ✅")

    # MOSTRAR TEXTO DETECTADO
    if "texto_ocr" in st.session_state:
        st.text_area(
            "Texto encontrado na placa",
            st.session_state["texto_ocr"],
            height=150
        )

    # =============================
    # FORMULÁRIO
    # =============================
    st.subheader("⚙️ Dados do Motor")

    col1, col2 = st.columns(2)

    with col1:
        st.session_state["marca"] = st.text_input("Marca", value=st.session_state["marca"])
        st.session_state["modelo"] = st.text_input("Modelo", value=st.session_state["modelo"])
        st.session_state["potencia"] = st.text_input("Potência", value=st.session_state["potencia"])
        st.session_state["tensao"] = st.text_input("Tensão", value=st.session_state["tensao"])
        st.session_state["corrente"] = st.text_input("Corrente", value=st.session_state["corrente"])
        st.session_state["rpm"] = st.text_input("RPM", value=st.session_state["rpm"])
        st.session_state["frequencia"] = st.text_input("Frequência", value=st.session_state["frequencia"])
        st.session_state["fp"] = st.text_input("Fator de Potência", value=st.session_state["fp"])
        st.session_state["carcaca"] = st.text_input("Carcaça", value=st.session_state["carcaca"])
        st.session_state["ip"] = st.text_input("Grau IP", value=st.session_state["ip"])

    with col2:
        st.session_state["isolacao"] = st.text_input("Classe de Isolação", value=st.session_state["isolacao"])
        st.session_state["regime"] = st.text_input("Regime", value=st.session_state["regime"])
        st.session_state["rolamento_dianteiro"] = st.text_input("Rolamento Dianteiro", value=st.session_state["rolamento_dianteiro"])
        st.session_state["rolamento_traseiro"] = st.text_input("Rolamento Traseiro", value=st.session_state["rolamento_traseiro"])
        st.session_state["peso"] = st.text_input("Peso", value=st.session_state["peso"])
        st.session_state["diametro_eixo"] = st.text_input("Diâmetro do Eixo", value=st.session_state["diametro_eixo"])
        st.session_state["comprimento_pacote"] = st.text_input("Comprimento do Pacote", value=st.session_state["comprimento_pacote"])
        st.session_state["numero_ranhuras"] = st.text_input("Número de Ranhuras", value=st.session_state["numero_ranhuras"])
        st.session_state["ligacao"] = st.text_input("Ligação", value=st.session_state["ligacao"])
        st.session_state["fabricacao"] = st.text_input("Ano de Fabricação", value=st.session_state["fabricacao"])

    # =============================
    # ORIGINALIDADE
    # =============================
    st.subheader("🔧 Verificação Manual")

    st.session_state["original"] = st.radio(
        "Motor Original?",
        ["Sim", "Não"],
        index=0 if st.session_state["original"] == "Sim" else 1,
    )

    # =============================
    # SALVAR
    # =============================
    st.subheader("💾 Salvar Motor")

    if st.button("Salvar Motor", use_container_width=True):

        motor = {campo: st.session_state[campo] for campo in campos}
        motor["original"] = st.session_state["original"]

        salvar_motor(motor)

        st.success("Motor salvo com sucesso!")
        st.json(motor)
