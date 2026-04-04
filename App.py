import streamlit as st
import importlib
import sys
import os
from pathlib import Path
from supabase import create_client, Client

# ================= 0. CORREÇÃO DE PATH (ACRESCENTADO) =================
# Este bloco garante que o Python encontre as pastas 'core' e 'services'
# mesmo quando os módulos são carregados de dentro da pasta 'page'
raiz = Path(__file__).resolve().parent
if str(raiz) not in sys.path:
    sys.path.insert(0, str(raiz))

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
        # Busca das secrets do Streamlit
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error("Erro nas credenciais do Supabase. Verifique o arquivo secrets.toml.")
        return None

# Disponibiliza o cliente supabase
supabase = init_connection()

# ================= 3. CSS CUSTOMIZADO =================
def carregar_css():
    try:
        # Caminho relativo à raiz para garantir funcionamento
        css_path = raiz / "assets" / "style.css"
        if css_path.exists():
            with open(css_path) as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except Exception:
        pass

carregar_css()

# ================= 4. AUTENTICAÇÃO =================
try:
    from auth.login import check_login
    from auth.logout import botao_logout
    check_login()
except Exception as e:
    # Se não houver sistema de login, o app segue normalmente
    pass

# ================= 5. CONTROLE DE ESTADO (ROTEAMENTO) =================
if "pagina" not in st.session_state:
    st.session_state.pagina = "cadastro"

# ================= 6. SIDEBAR (MENU NAV) =================
with st.sidebar:
    st.title("⚙️ Moto-Renow")
    
    # O radio define a navegação principal
    escolha = st.radio(
        "Navegação",
        ["cadastro", "consulta"],
        index=0 if st.session_state.pagina == "cadastro" else 1,
        key="menu_principal"
    )

    # Se o usuário mudar no rádio, atualizamos a página (exceto se estiver em modo edit)
    if st.session_state.get("pagina") != "edit":
        st.session_state.pagina = escolha

    st.divider()

    try:
        botao_logout()
    except:
        pass

# ================= 7. ROUTER (CARREGAMENTO DE PÁGINAS) =================
try:
    if st.session_state.pagina == "edit":
        # Importação para a página de edição
        from page.edit import show
        show(supabase)
    else:
        # Importação dinâmica para cadastro ou consulta
        # nome_modulo assume que seus arquivos estão em: page/cadastro.py ou page/consulta.py
        nome_modulo = f"page.{st.session_state.pagina}"
        
        # Carregamento e recarregamento para refletir alterações em tempo real
        modulo = importlib.import_module(nome_modulo)
        importlib.reload(modulo) 
        
        # Executa a função principal da página passando o supabase
        if hasattr(modulo, "show"):
            modulo.show(supabase)
        else:
            st.error(f"O módulo '{nome_modulo}' não possui a função 'show(supabase)'.")

except ModuleNotFoundError as e:
    st.error(f"Erro: A página '{st.session_state.pagina}' não foi encontrada. Verifique se o arquivo existe em 'page/{st.session_state.pagina}.py'")
    st.info(f"Detalhe do erro: {e}")
except Exception as e:
    st.error(f"Ocorreu um erro ao carregar a página: {e}")
