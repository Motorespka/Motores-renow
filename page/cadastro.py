import json

import google.generativeai as genai
import streamlit as st
from PIL import Image


def _processar_plaqueta(foto_arquivo):
    img = Image.open(foto_arquivo).transpose(Image.FLIP_LEFT_RIGHT)
    prompt = (
        "Você é um engenheiro de motores. Retorne APENAS JSON com: "
        '"marca", "cv", "rpm", "v", "a", "carcaca", "cos_phi", "isol".'
    )

    keys = st.secrets["GEMINI_API_KEY"]
    for key in keys:
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel("gemini-2.5-flash")
            response = model.generate_content([prompt, img])
            limpo = response.text.replace("```json", "").replace("```", "").strip()
            return json.loads(limpo)
        except Exception as exc:
            if any(flag in str(exc).lower() for flag in ["quota", "limit", "429"]):
                continue
            raise
    raise RuntimeError("Todas as keys do Gemini atingiram limite de uso.")


def render(ctx):
    st.title("⚡ Cadastro")

    # -----------------------------
    # CADASTRO DE MOTORES (com IA)
    # -----------------------------
    st.subheader("Cadastro de Motores")

    if "cadastro_motor_extraidos" not in st.session_state:
        st.session_state["cadastro_motor_extraidos"] = {}

    foto_motor = st.file_uploader(
        "Imagem da plaqueta do motor",
        type=["jpg", "png", "jpeg"],
        key="cadastro_motor_foto",
    )

    if foto_motor and st.button("Extrair dados do motor com IA", use_container_width=True, key="cadastro_motor_ia"):
        with st.spinner("Analisando imagem do motor..."):
            st.session_state["cadastro_motor_extraidos"] = _processar_plaqueta(foto_motor)
            st.success("Dados do motor extraídos.")

    extraidos_motor = st.session_state.get("cadastro_motor_extraidos", {})

    with st.form("motor_form"):
        marca_motor = st.text_input("Marca", value=extraidos_motor.get("marca", ""), key="motor_marca")
        potencia_motor = st.text_input("Potência", value=extraidos_motor.get("cv", ""), key="motor_potencia")
        rpm_motor = st.text_input("RPM", value=extraidos_motor.get("rpm", ""), key="motor_rpm")
        tensao_motor = st.text_input("Tensão", value=extraidos_motor.get("v", ""), key="motor_tensao")
        corrente_motor = st.text_input("Corrente", value=extraidos_motor.get("a", ""), key="motor_corrente")
        salvar_motor = st.form_submit_button("Salvar motor", use_container_width=True)

    if salvar_motor:
        if not marca_motor:
            st.warning("Preencha ao menos a Marca do motor.")
        else:
            payload_motor = {
                "marca": marca_motor,
                "potencia": potencia_motor,
                "rpm": rpm_motor,
                "tensao": tensao_motor,
                "corrente": corrente_motor,
            }
            ctx.supabase.table("motores").insert(payload_motor).execute()
            st.success("Motor salvo com sucesso.")
            st.session_state["cadastro_motor_extraidos"] = {}

    st.divider()

    # -----------------------------
    # CADASTRO DE O.S. (sem IA)
    # -----------------------------
    st.subheader("Cadastro de O.S.")

    with st.form("os_form"):
        cliente = st.text_input("Cliente")
        marca = st.text_input("Marca")
        potencia = st.text_input("Potência")
        rpm = st.text_input("RPM")
        tensao = st.text_input("Tensão")
        corrente = st.text_input("Corrente")
        diagnostico = st.text_area("Diagnóstico de entrada")
        salvar = st.form_submit_button("Salvar ordem", use_container_width=True)

    if salvar:
        if not cliente or not marca:
            st.warning("Preencha Cliente e Marca.")
            return
        payload = {
            "cliente": cliente,
            "marca": marca,
            "potencia": potencia,
            "rpm": rpm,
            "tensao": tensao,
            "corrente": corrente,
            "diagnostico": diagnostico,
            "status": "Em Análise",
        }
        ctx.supabase.table("ordens_servico").insert(payload).execute()
        st.success("Ordem salva com sucesso.")
