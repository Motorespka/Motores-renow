import streamlit as st
import sys
from pathlib import Path
from supabase import create_client

@st.cache_resource
def init_connection():
    try:
        # Garanta que esses nomes existam no seu secrets.toml
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Erro nas credenciais: {e}")
        return None
# ===============================
# 1️⃣ CONFIGURAÇÃO INICIAL
# ===============================
st.set_page_config(
    page_title="Moto-Renow",
    page_icon="⚙️",
    layout="wide"
)

# ===============================
# 2️⃣ PATH DO PROJETO
# ===============================
raiz = Path(__file__).resolve().parent

if str(raiz) not in sys.path:
    sys.path.insert(0, str(raiz))

# ===============================
# 3️⃣ SESSION STATE
# ===============================
if "pagina" not in st.session_state:
    st.session_state.pagina = "cadastro"

if "logado" not in st.session_state:
    st.session_state.logado = False

# ===============================
# 4️⃣ SUPABASE
# ===============================
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception:
        st.error("Erro nas credenciais do Supabase.")
        return None

supabase = init_connection()

# ===============================
# 5️⃣ CSS GLOBAL
# ===============================
def carregar_css():
    try:
        css_path = raiz / "assets" / "style.css"
        if css_path.exists():
            st.markdown(
                f"<style>{css_path.read_text(encoding='utf-8')}</style>",
                unsafe_allow_html=True
            )
    except Exception:
        pass

carregar_css()

# ===============================
# 6️⃣ UI EXTRA (OPCIONAL)
# ===============================
try:
    from ui.theme import aplicar_tema
    from ui.animations import iniciar_animacoes
    aplicar_tema()
    iniciar_animacoes()
except Exception:
    pass

# ===============================
# 7️⃣ AUTH LOGIN (GATE)
# ===============================
try:
    from auth.login import check_login

    if not check_login():
        st.stop()

except Exception as e:
    st.error(f"Erro no sistema de autenticação: {e}")
    st.stop()

# ===============================
# 8️⃣ SIDEBAR
# ===============================
try:
    from streamlit_option_menu import option_menu
except ModuleNotFoundError:
    st.error("Instale: pip install streamlit-option-menu")
    st.stop()

with st.sidebar:

    idx = 0 if st.session_state.pagina == "cadastro" else 1

    escolha = option_menu(
        "Moto-Renow",
        ["cadastro", "consulta"],
        icons=["plus-circle", "search"],
        menu_icon="gear",
        default_index=idx,
        styles={
            "container": {"background-color": "#0d1117"},
            "icon": {"color": "#00f2ff"},
            "nav-link": {"color": "white"},
            "nav-link-selected": {
                "background-color": "#1f2937",
                "border-left": "4px solid #00f2ff",
            },
        },
    )

    st.session_state.pagina = escolha

    st.divider()

    # LOGOUT
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# ===============================
# 9️⃣ ROUTER DE PÁGINAS
# ===============================
try:

    if st.session_state.pagina == "cadastro":
        from page.cadastro import show
        show(supabase)

    elif st.session_state.pagina == "consulta":
        from page.consulta import show
        show(supabase)

except ModuleNotFoundError as e:
    st.error(f"Página não encontrada: {e}")

except Exception as e:
    st.error(f"Erro ao carregar página: {e}")
