import streamlit as st
import importlib
import sys
from pathlib import Path
from supabase import create_client

# ================= 0. CORREÇÃO DE PATH =================
raiz = Path(__file__).resolve().parent
if str(raiz) not in sys.path:
    sys.path.insert(0, str(raiz))

# NOVO: Import para o menu lateral pro com correção do erro de exceção
try:
    from streamlit_option_menu import option_menu
except ModuleNotFoundError: # <-- CORRIGIDO AQUI (era ImportNotFoundError)
    st.error("Erro: A biblioteca 'streamlit-option-menu' não está instalada. Execute: pip install streamlit-option-menu")
    st.stop()

# ================= 1. CONFIGURAÇÃO DA PÁGINA =================
st.set_page_config(
    page_title="Moto-Renow",
    page_icon="⚙️",
    layout="wide"
)

# ================= 2. INICIALIZAÇÃO SUPABASE =================
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error("Erro nas credenciais do Supabase. Verifique o arquivo secrets.toml.")
        return None

supabase = init_connection()

# ================= 3. CSS CUSTOMIZADO (FUNDO ESCURO TECH) =================
def carregar_css():
    # Injetando fundo escuro profundo e ajustes de interface
    st.markdown("""
        <style>
        /* Fundo principal */
        .stApp {
            background-color: #0d1117 !important;
            color: #ffffff !important;
        }
        
        /* Ajuste do Sidebar */
        section[data-testid="stSidebar"] {
            background-color: #0d1117 !important;
            border-right: 1px solid #30363d;
        }

        /* Estilo para inputs e containers */
        .stTextInput > div > div > input {
            background-color: #161b22 !important;
            color: white !important;
        }
        
        header {visibility: hidden;}
        footer {visibility: hidden;}
        </style>
    """, unsafe_allow_html=True)
    
    try:
        css_path = raiz / "assets" / "style.css"
        if css_path.exists():
            with open(css_path) as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception:
        pass

carregar_css()

# ================= UI TECH =================
try:
    from ui.theme import aplicar_tema
    from ui.animations import iniciar_animacoes
    aplicar_tema()
    iniciar_animacoes()
except Exception as e:
    print("UI não carregada:", e)

# ================= 4. AUTENTICAÇÃO (BLOQUEIO) =================
try:
    from auth.login import check_login
    if not check_login():
        st.stop()
except Exception as e:
    st.error(f"Erro ao carregar sistema de autenticação: {e}")
    st.stop()

# ================= 6. SIDEBAR PRO (MENU NAV) =================
with st.sidebar:
    # Definindo o índice baseado no estado atual para o menu não resetar
    idx_padrao = 0 if st.session_state.get("pagina") == "cadastro" else 1
    
    escolha = option_menu(
        "Moto-Renow", 
        ["cadastro", "consulta"],
        icons=['plus-circle', 'search'],
        menu_icon="gear", 
        default_index=idx_padrao,
        styles={
            "container": {"padding": "5!important", "background-color": "#0d1117"},
            "icon": {"color": "#00f2ff", "font-size": "18px"}, 
            "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#161b22", "color": "white"},
            "nav-link-selected": {"background-color": "#1f2937", "border-left": "4px solid #00f2ff"},
        }
    )

    # Atualiza o estado da página
    if st.session_state.get("pagina") != "edit":
        st.session_state.pagina = escolha

    st.divider()

# ================= 7. ROUTER (CARREGAMENTO DE PÁGINAS) =================
try:
    if st.session_state.pagina == "edit":
        from page.edit import show
        show(supabase)
    else:
        nome_modulo = f"page.{st.session_state.pagina}"
        modulo = importlib.import_module(nome_modulo)
        importlib.reload(modulo) 
        
        if hasattr(modulo, "show"):
            modulo.show(supabase)
        else:
            st.error(f"O módulo '{nome_modulo}' não possui a função 'show(supabase)'.")

except ModuleNotFoundError as e:
    st.error(f"Erro: A página '{st.session_state.pagina}' não foi encontrada.")
except Exception as e:
    st.error(f"Ocorreu um erro ao carregar a página: {e}")
