import streamlit as st
import importlib

from auth.login import login
from components.ui import carregar_css
from components.animation import transicao
from components.navbar import menu

st.set_page_config(
    page_title="Moto-Renow",
    page_icon="⚙️",
    layout="wide"
)

carregar_css()

login()

if not st.session_state.get("logado"):
    st.stop()

pagina = menu()

transicao()

mapa = {
    "Cadastro":"pages.cadastro",
    "Consulta":"pages.consulta",
    "Cálculos":"pages.calculos",
    "Rebobinador":"pages.rebobinador"
}

modulo = importlib.import_module(mapa[pagina])
modulo.main()
