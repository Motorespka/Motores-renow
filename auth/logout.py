import streamlit as st
from supabase import create_client
import bcrypt
from auth.session import criar_sessao, sessao_valida, limpar_sessao

# 1. Conexão com Supabase (Puxando dos Secrets do Streamlit/GitHub)
@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_connection()

def check_login():
    # Verifica se já existe uma sessão ativa
    if sessao_valida():
        # Se estiver logado, mostra seu botão de logout na sidebar
        if st.sidebar.button("🚪 Sair"):
            limpar_sessao()
            st.rerun()
        return True

    # Se NÃO estiver logado, exibe a interface de acesso
    st.title("🔐 Moto-Renow • Acesso Técnico")
    
    # Abas para separar Login de Cadastro (Onde você criará seu Admin)
    tab_login, tab_cadastro = st.tabs(["Entrar", "Criar Conta Admin"])

    with tab_login:
        usuario = st.text_input("Usuário", key="login_user")
        senha = st.text_input("Senha", type="password", key="login_pass")
        
        if st.button("Acessar"):
            # Busca o usuário na tabela 'perfis_usuarios' que criamos no SQL
            res = supabase.table("perfis_usuarios").select("*").eq("username", usuario).execute()
            
            if res.data:
                stored_hash = res.data[0]["password_hash"]
                # Compara a senha digitada com o hash do banco
                if bcrypt.checkpw(senha.encode('utf-8'), stored_hash.encode('utf-8')):
                    criar_sessao() # Sua função de session.py
                    st.success("Acesso liberado!")
                    st.rerun()
                else:
                    st.error("Senha incorreta.")
            else:
                st.error("Usuário não encontrado.")

    with tab_cadastro:
        st.info("Use esta aba para criar seu acesso de administrador.")
        novo_user = st.text_input("Definir Usuário", key="reg_user")
        nova_pass = st.text_input("Definir Senha", type="password", key="reg_pass")
        confirmar = st.text_input("Confirmar Senha", type="password", key="reg_conf")

        if st.button("Confirmar Cadastro"):
            if not novo_user or not nova_pass:
                st.warning("Preencha todos os campos.")
            elif nova_pass != confirmar:
                st.error("As senhas não coincidem.")
            else:
                # Gerando o hash seguro
                hashed = bcrypt.hashpw(nova_pass.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                try:
                    supabase.table("perfis_usuarios").insert({
                        "username": novo_user,
                        "password_hash": hashed
                    }).execute()
                    st.success("Conta criada com sucesso! Agora entre na aba 'Entrar'.")
                except:
                    st.error("Erro: Este nome de usuário já está em uso.")

    # Bloqueia o restante do app enquanto não logar
    st.stop()
