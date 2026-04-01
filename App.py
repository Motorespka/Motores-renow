import streamlit as st
import importlib

# ================= CONFIG =================

st.set_page_config(
    page_title="Moto-Renow",
    page_icon="⚙️",
    layout="wide"
)

# ================= CSS =================

def carregar_css():
    try:
        with open("assets/style.css") as f:
            st.markdown(
                f"<style>{f.read()}</style>",
                unsafe_allow_html=True
            )
    except:
        pass

carregar_css()

# ================= LOGIN =================

try:
    from auth.login import check_login
    from auth.logout import botao_logout
    check_login()
except:
    pass

# ================= CONTROLE DE PÁGINA =================

if "pagina" not in st.session_state:
    st.session_state.pagina = "cadastro"

# ================= SIDEBAR =================

with st.sidebar:

    st.title("⚙️ Moto-Renow")

    escolha = st.radio(
        "Sistema",
        ["cadastro", "consulta"]
    )

    st.divider()

    try:
        botao_logout()
    except:
        pass

# ================= ROUTER =================

if st.session_state.pagina == "editar":

    from page.editar import show
    show()

else:

    st.session_state.pagina = escolha

    page = importlib.import_module(
        f"page.{st.session_state.pagina}"
    )

    page.show()
