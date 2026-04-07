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
    st.title("⚡ Cadastro de O.S.")

    foto = st.file_uploader("Imagem da plaqueta", type=["jpg", "png", "jpeg"])
    extraidos = {}
    if foto and st.button("Extrair dados com IA", use_container_width=True):
        with st.spinner("Analisando imagem..."):
            extraidos = _processar_plaqueta(foto)
            st.success("Dados extraídos.")

    with st.form("os_form"):
        cliente = st.text_input("Cliente")
        marca = st.text_input("Marca", value=extraidos.get("marca", ""))
        potencia = st.text_input("Potência", value=extraidos.get("cv", ""))
        rpm = st.text_input("RPM", value=extraidos.get("rpm", ""))
        tensao = st.text_input("Tensão", value=extraidos.get("v", ""))
        corrente = st.text_input("Corrente", value=extraidos.get("a", ""))
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
