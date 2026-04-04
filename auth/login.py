import streamlit as st
from supabase import create_client
import bcrypt
from auth.session import criar_sessao, sessao_valida, limpar_sessao

# Inicializa o cliente Supabase usando st.secrets
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

def check_login():
    # 1. Se a sessão for válida (via session_state ou Token na URL)
    if sessao_valida():
        # Exibe botão de sair na barra lateral
        if st.sidebar.button("🚪 Sair do Sistema"):
            limpar_sessao()
            st.rerun()
        return True

    # 2. Se não estiver logado, exibe a interface de Login/Cadastro
    st.title("🔐 Moto-Renow • Acesso Técnico")
    
    tab_login, tab_cadastro = st.tabs(["Entrar", "Criar Conta"])

    with tab_login:
        usuario = st.text_input("Usuário", key="login_user")
        senha = st.text_input("Senha", type="password", key="login_pass")
        
        if st.button("Acessar Sistema"):
            if not usuario or not senha:
                st.warning("Por favor, preencha todos os campos.")
            else:
                # BUSCA NA TABELA CORRETA: usuarios_app
                res = supabase.table("usuarios_app").select("*").eq("username", usuario).execute()
                
                if res.data:
                    stored_hash = res.data[0]["password_hash"]
                    # Verifica se a senha bate com o hash seguro
                    if bcrypt.checkpw(senha.encode('utf-8'), stored_hash.encode('utf-8')):
                        criar_sessao() 
                        st.success("Login realizado!")
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
            if not novo_usuario or not nova_senha:
                st.error("O usuário e a senha não podem estar vazios.")
            elif nova_senha != confirmar:
                st.error("As senhas não coincidem.")
            elif len(nova_senha) < 6:
                st.warning("A senha deve ter pelo menos 6 caracteres.")
            else:
                # Gera o hash para nunca salvar a senha limpa
                hashed = bcrypt.hashpw(nova_senha.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                try:
                    # INSERE NA TABELA CORRETA: usuarios_app
                    supabase.table("usuarios_app").insert({
                        "username": novo_usuario,
                        "password_hash": hashed
                    }).execute()
                    st.success("Conta criada! Vá na aba 'Entrar'.")
                except Exception as e:
                    # Mostra o erro real caso a conexão falhe ou o RLS bloqueie
                    st.error(f"Erro ao cadastrar: {e}")

    # Interrompe o restante do app enquanto o usuário não estiver logado
    st.stop()
