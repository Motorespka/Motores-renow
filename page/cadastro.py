import streamlit as st

from services.gemini_motor import (
    ler_placa_gemini,
    calcular_motor_gemini,
    obter_chave_gemini,
)
from services.database import salvar_motor


def _mime_de_upload(name: str) -> str:
    n = (name or "").lower()
    if n.endswith(".png"):
        return "image/png"
    if n.endswith(".webp"):
        return "image/webp"
    return "image/jpeg"


def show():
    st.title("Cadastro de Motor")

    if not obter_chave_gemini():
        st.warning(
            "Configure **GEMINI_API_KEY** (variável de ambiente ou "
            "`.streamlit/secrets.toml`) para leitura da placa e cálculos com Gemini."
        )

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
    if "resultado_calculo_gemini" not in st.session_state:
        st.session_state["resultado_calculo_gemini"] = None

    # =============================
    # FOTO DA PLACA (CÂMERA OU UPLOAD) + GEMINI
    # =============================
    st.subheader("📸 Foto da placa do motor (Gemini)")
    col_cam, col_up = st.columns(2)
    with col_cam:
        imagem_camera = st.camera_input("Tirar foto da placa", key="cam_placa")
    with col_up:
        arquivo = st.file_uploader(
            "Ou enviar imagem da placa",
            type=["jpg", "jpeg", "png", "webp"],
            key="up_placa",
        )

    imagem_para_ia = None
    mime_ia = "image/jpeg"
    if arquivo is not None:
        imagem_para_ia = arquivo.getvalue()
        mime_ia = _mime_de_upload(arquivo.name)
    elif imagem_camera is not None:
        imagem_para_ia = imagem_camera.getvalue()
        mime_ia = _mime_de_upload(getattr(imagem_camera, "name", "") or "foto.jpg")

    if imagem_para_ia and st.button("🔎 Ler placa com Gemini", type="primary"):
        if not obter_chave_gemini():
            st.error("Configure GEMINI_API_KEY para usar a leitura por IA.")
        else:
            with st.spinner("Analisando placa com Gemini..."):
                try:
                    dados = ler_placa_gemini(imagem_para_ia, mime_type=mime_ia)
                    for chave, valor in dados.items():
                        if chave in st.session_state:
                            st.session_state[chave] = valor
                    st.session_state["resultado_calculo_gemini"] = None
                    st.success("Dados da placa extraídos. Revise e ajuste se necessário.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Falha na leitura com Gemini: {e}")

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
    # CÁLCULOS COM GEMINI (COM BASE NOS CAMPOS)
    # =============================
    st.subheader("📐 Cálculos e observações (Gemini)")
    motor_snapshot = {c: st.session_state[c] for c in campos}
    if st.button("Calcular / interpretar com Gemini"):
        if not obter_chave_gemini():
            st.error("Configure GEMINI_API_KEY para usar os cálculos com IA.")
        else:
            with st.spinner("Gerando análise..."):
                try:
                    st.session_state["resultado_calculo_gemini"] = calcular_motor_gemini(motor_snapshot)
                except Exception as e:
                    st.error(f"Falha nos cálculos com Gemini: {e}")

    res = st.session_state.get("resultado_calculo_gemini")
    if isinstance(res, dict) and res:
        st.json(res)

    # =============================
    # VERIFICAÇÃO MANUAL / ORIGINALIDADE
    # =============================
    st.subheader("🔧 Verificação Manual / Cálculo Não Original")
    st.session_state["original"] = st.radio(
        "Motor Original?",
        ["Sim", "Não"],
        index=0 if st.session_state["original"] == "Sim" else 1,
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
