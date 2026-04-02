import streamlit as st
import importlib
from supabase import create_client, Client

# ================= 1. CONFIGURAÇÃO DA PÁGINA =================
st.set_page_config(
    page_title="Moto-Renow",
    page_icon="⚙️",
    layout="wide"
)

# ================= 2. INICIALIZAÇÃO SUPABASE =================
# Usando cache para não reconectar a cada clique
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception as e:
        st.error("Erro nas credenciais do Supabase. Verifique o arquivo secrets.toml.")
        return None

# Disponibiliza o cliente supabase para ser usado em qualquer lugar do app
supabase = init_connection()

# ================= 3. CSS CUSTOMIZADO =================
def carregar_css():
    try:
        with open("assets/style.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass

carregar_css()

# ================= 4. AUTENTICAÇÃO =================
try:
    from auth.login import check_login
    from auth.logout import botao_logout
    # Se o check_login barrar o usuário, o script para aqui (dependendo de como sua auth foi feita)
    check_login()
except Exception as e:
    # Se não houver sistema de login ou der erro, segue o fluxo
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

    # Se o usuário clicar no rádio, limpamos o estado de 'edit' para voltar ao fluxo normal
    if st.session_state.pagina != "edit":
        st.session_state.pagina = escolha

    st.divider()

    try:
        botao_logout()
    except:
        pass

# ================= 7. ROUTER (CARREGAMENTO DE PÁGINAS) =================
# Lógica para exibir a página correta
try:
    if st.session_state.pagina == "edit":
        # Importação direta para a página de edição (caso precise de parâmetros extras)
        from page.edit import show
        show(supabase) # Passando o cliente supabase como argumento
    else:
        # Importação dinâmica para cadastro ou consulta
        # O módulo deve ter uma função 'show(supabase)'
        nome_modulo = f"page.{st.session_state.pagina}"
        modulo = importlib.import_module(nome_modulo)
        importlib.reload(modulo) # Garante que o código novo seja carregado
        modulo.show(supabase) # Passando o cliente supabase como argumento

except ModuleNotFoundError as e:
    st.error(f"Erro: A página '{st.session_state.pagina}' não foi encontrada na pasta 'page/'.")
except Exception as e:
    st.error(f"Ocorreu um erro ao carregar a página: {e}")
