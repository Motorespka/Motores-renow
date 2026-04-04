import streamlit as st
import importlib
import sys
import os
from pathlib import Path
from supabase import create_client, Client

# ================= 0. CORREÇÃO DE PATH DEFINITIVA =================
raiz = Path(__file__).resolve().parent
if str(raiz) not in sys.path:
    sys.path.insert(0, str(raiz))

# Adicional para subpastas serem reconhecidas como pacotes
sys.path.append(os.path.join(os.path.dirname(__file__), 'page'))

st.set_page_config(page_title="Moto-Renow", page_icon="⚙️", layout="wide")

@st.cache_resource
def init_connection():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except Exception:
        st.error("Erro nas credenciais. Verifique o secrets.toml.")
        return None

supabase = init_connection()

# ... (Mantenha o CSS e Autenticação como estão) ...

if "pagina" not in st.session_state:
    st.session_state.pagina = "cadastro"

# Lógica de Roteamento (Melhorada para evitar ModuleNotFoundError)
try:
    nome_modulo = f"page.{st.session_state.pagina}"
    if st.session_state.pagina == "edit":
        nome_modulo = "page.edit"
        
    modulo = importlib.import_module(nome_modulo)
    importlib.reload(modulo)
    
    if hasattr(modulo, "show"):
        modulo.show(supabase)
except Exception as e:
    st.error(f"Erro ao carregar página: {e}")
