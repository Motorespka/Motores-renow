import streamlit as st
import importlib
import sys
from pathlib import Path
from supabase import create_client

# ================= 0. CORREÇÃO DE PATH =================
raiz = Path(__file__).resolve().parent
if str(raiz) not in sys.path:
    sys.path.insert(0, str(raiz))

# ================= 1. CONFIGURAÇÃO DA PÁGINA =================
# st.set_page_config DEVE ser o primeiro comando Streamlit
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

# ================= 3. CSS CUSTOMIZADO =================
def carregar_css():
    try:
        css_path = raiz / "assets" / "style.css"
        if css_path.exists():
            with open(css_path) as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception:
        pass

carregar_css()

# ================= 4. AUTENTICAÇÃO (BLOQUEIO) =================
try:
    from auth.login import check_login
    
    # Se check_login() for False, ele mostra a tela de login e para o script aqui.
    if not check_login():
        st.stop()
        
except Exception as e:
    st.error(f"Erro ao carregar sistema de autenticação: {e}")
    st.stop()

# ================= TUDO ABAIXO SÓ APARECE SE ESTIVER LOGADO =================

# ================= 5. CONTROLE DE ESTADO (ROTEAMENTO) =================
if "pagina" not in st.session_state:
    st.session_state.pagina = "cadastro"

# ================= 6. SIDEBAR (MENU NAV) =================
with st.sidebar:
    st.title("⚙️ Moto-Renow")
    
    escolha = st.radio(
        "Navegação",
        ["cadastro", "consulta"],
        index=0 if st.session_state.pagina == "cadastro" else 1,
        key="menu_principal"
    )

    # Atualiza a página apenas se não estiver em modo de edição
    if st.session_state.get("pagina") != "edit":
        st.session_state.pagina = escolha

    st.divider()
    # O botão de logout já está dentro do check_login() na sidebar, 
    # mas se você preferir o seu arquivo logout.py, ele seria chamado aqui.

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
