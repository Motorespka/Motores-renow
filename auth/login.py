import bcrypt
import streamlit as st
from supabase import create_client


@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


def render_login(session) -> bool:
    if session.is_authenticated:
        return True

    supabase = init_connection()
    st.title("🔐 Moto-Renow • Acesso Técnico")

    tab_login, tab_cadastro = st.tabs(["Entrar", "Criar Conta"])

    with tab_login:
        usuario = st.text_input("Usuário", key="login_user")
        senha = st.text_input("Senha", type="password", key="login_pass")

        if st.button("Acessar Sistema"):
            if not usuario or not senha:
                st.warning("Por favor, preencha todos os campos.")
            else:
                res = supabase.table("usuarios_app").select("*").eq("username", usuario).execute()
                if not res.data:
                    st.error("Usuário não encontrado.")
                else:
                    stored_hash = res.data[0]["password_hash"]
                    if not bcrypt.checkpw(senha.encode("utf-8"), stored_hash.encode("utf-8")):
                        st.error("Senha incorreta.")
                    else:
                        session.login()
                        st.success("Login realizado!")
                        st.rerun()

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
                hashed = bcrypt.hashpw(nova_senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                supabase.table("usuarios_app").insert({"username": novo_usuario, "password_hash": hashed}).execute()
                st.success("Conta criada! Vá na aba 'Entrar'.")

    return False
