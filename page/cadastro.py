import streamlit as st
from PIL import Image
import numpy as np
import cv2
from services.ocr_motor import ler_placa_motor
from services.database import salvar_motor

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
    if "original" not in st.session_state:
        st.session_state["original"] = "Sim"

    # =============================
    # CAPTURA DE IMAGEM
    # =============================
    st.subheader("📸 Tire a foto da placa do motor")
    imagem_input = st.camera_input("Clique para tirar a foto do motor")

    if imagem_input:
        st.image(imagem_input, caption="Imagem capturada", width=300)

        if st.button("🔎 Ler placa"):
            with st.spinner("Lendo placa..."):
                # Converte para PIL e depois para numpy array
                imagem = Image.open(imagem_input)
                imagem_cv = np.array(imagem)
                imagem_cv = cv2.cvtColor(imagem_cv, cv2.COLOR_RGB2BGR)

                dados_ocr = ler_placa_motor(imagem_cv)

            # Mostra para verificação
            st.write("📝 Dados OCR:", dados_ocr)

            # Preenche os campos automaticamente
            for chave, valor in dados_ocr.items():
                if chave in st.session_state:
                    st.session_state[chave] = valor

            st.success("✅ Dados preenchidos automaticamente!")

    # =============================
    # FORMULÁRIO / EDIÇÃO MANUAL
    # =============================
    st.subheader("⚙️ Dados do Motor (Edição Manual)")
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
    # VERIFICAÇÃO MANUAL / ORIGINALIDADE
    # =============================
    st.subheader("🔧 Verificação Manual / Cálculo Não Original")
    st.session_state["original"] = st.radio(
        "Motor Original?",
        ["Sim", "Não"],
        index=0 if st.session_state["original"] == "Sim" else 1
    )

    # =============================
    # SALVAR MOTOR
    # =============================
    st.subheader("💾 Salvar Motor no Banco de Dados")
    if st.button("Salvar Motor", use_container_width=True):
        motor = {campo: st.session_state[campo] for campo in campos}
        motor["original"] = st.session_state["original"]
        salvar_motor(motor)
        st.success("Motor salvo com sucesso!")
        st.json(motor)
