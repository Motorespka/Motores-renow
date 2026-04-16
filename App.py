import os
import streamlit as st

st.set_page_config(page_title="Moto-Renow", layout="wide")

st.title("Moto-Renow")
st.caption("Modo seguro de deploy no Streamlit Cloud")

external_frontend_url = os.getenv("NEXT_APP_URL", "").strip()
api_docs_url = os.getenv("API_DOCS_URL", "").strip()

st.success("O app Streamlit abriu normalmente.")

if external_frontend_url:
    st.info("Frontend externo detectado.")
    st.iframe(external_frontend_url, height=900)
else:
    st.warning(
        "Next.js desativado neste deploy do Streamlit Cloud. "
        "O app não tentará iniciar npm/Node no boot."
    )

if api_docs_url:
    st.markdown(f"[Abrir docs da API]({api_docs_url})")

st.write("Próximo passo: separar deploys.")
st.write("- Streamlit: interface principal / fallback")
st.write("- FastAPI: deploy próprio")
st.write("- Next.js: deploy próprio")
