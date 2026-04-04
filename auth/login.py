import streamlit as st
from supabase import create_client
import bcrypt
from auth.session import criar_sessao, sessao_valida

# Inicializa o cliente Supabase usando st.secrets
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

def check_login():
    if sessao_valida():
        return True

    st.title("🔐 Moto-Renow • Acesso Técnico")
    
    # Criamos abas para organizar a interface
    tab_login, tab_cadastro = st.tabs(["Entrar", "Criar Conta"])

    with tab_login:
        usuario = st.text_input("Usuário", key="login_user")
        senha = st.text_input("Senha", type="password", key="login_pass")
        
        if st.button("Acessar Sistema"):
            # Busca o usuário no banco
            res = supabase.table("perfis_usuarios").select("*").eq("username", usuario).execute()
            
            if res.data:
                stored_hash = res.data[0]["password_hash"]
                # Verifica se a senha bate com o hash seguro
                if bcrypt.checkpw(senha.encode('utf-8'), stored_hash.encode('utf-8')):
                    criar_sessao()
                    st.success("Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error("Senha incorreta.")
            else:
                st.error("Usuário não encontrado.")

    with tab_cadastro:
        st.info("Crie seu acesso para salvar cálculos de motores.")
        novo_usuario = st.text_input("Definir Usuário", key="reg_user")
        nova_senha = st.text_input("Definir Senha", type="password", key="reg_pass")
        confirmar = st.text_input("Confirmar Senha", type="password", key="reg_conf")

        if st.button("Cadastrar"):
            if nova_senha != confirmar:
                st.error("As senhas não coincidem.")
            elif len(nova_senha) < 6:
                st.warning("A senha deve ter pelo menos 6 caracteres.")
            else:
                # Gera o hash para nunca salvar a senha limpa
                hashed = bcrypt.hashpw(nova_senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                try:
                    supabase.table("perfis_usuarios").insert({
                        "username": novo_usuario,
                        "password_hash": hashed
                    }).execute()
                    st.success("Conta criada! Vá na aba 'Entrar'.")
                except Exception:
                    st.error("Nome de usuário já está em uso.")

    st.stop()
