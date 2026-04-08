import streamlit as st
from postgrest.exceptions import APIError
from supabase import create_client


@st.cache_resource
def init_connection():
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL/SUPABASE_KEY não encontrados em st.secrets")
    return create_client(url, key)


def _salvar_perfil_usuario(supabase, user_id: str, username: str, nome: str, email: str) -> None:
    payload = {
        "id": user_id,
        "username": username,
        "nome": nome,
        "email": email,
        "role": "user",
        "plan": "free",
        "ativo": True,
    }
    # upsert evita conflito caso exista trigger automático de criação de perfil
    supabase.table("usuarios_app").upsert(payload, on_conflict="id").execute()


def _carregar_perfil_usuario(supabase, user_id: str, email: str):
    try:
        perfil = supabase.table("usuarios_app").select("*").eq("id", user_id).limit(1).execute()
        if perfil.data:
            return perfil.data[0]
    except Exception:
        pass

    try:
        perfil = supabase.table("usuarios_app").select("*").eq("email", email).limit(1).execute()
        if perfil.data:
            return perfil.data[0]
    except Exception:
        pass

    return None


def render_login(session) -> bool:
    if session.is_authenticated:
        return True

    supabase = init_connection()
    st.title("🔐 Moto-Renow • Acesso Técnico")

    tab_login, tab_cadastro = st.tabs(["Entrar", "Criar Conta"])

    with tab_login:
        email = st.text_input("E-mail", key="login_email")
        senha = st.text_input("Senha", type="password", key="login_pass")

        if st.button("Acessar Sistema"):
            if not email or not senha:
                st.warning("Por favor, preencha todos os campos.")
            else:
                try:
                    auth_res = supabase.auth.sign_in_with_password({"email": email, "password": senha})
                    user = getattr(auth_res, "user", None)
                    if not user:
                        st.error("Falha no login. Verifique e-mail/senha ou confirmação de e-mail.")
                    else:
                        perfil = _carregar_perfil_usuario(supabase, user.id, email)
                        st.session_state["auth_user_id"] = user.id
                        st.session_state["auth_user_email"] = email
                        st.session_state["auth_user_profile"] = perfil
                        session.login()
                        st.success("Login realizado!")
                        st.rerun()
                except Exception as exc:
                    st.error(f"Erro no login: {exc}")

    with tab_cadastro:
        st.info("Crie seu acesso usando Supabase Auth.")
        nome = st.text_input("Nome", key="reg_nome")
        novo_usuario = st.text_input("Nome de usuário", key="reg_user")
        novo_email = st.text_input("E-mail", key="reg_email")
        nova_senha = st.text_input("Definir Senha", type="password", key="reg_pass")
        confirmar = st.text_input("Confirmar Senha", type="password", key="reg_conf")

        if st.button("Cadastrar"):
            if not nome or not novo_usuario or not novo_email or not nova_senha:
                st.error("Nome, usuário, e-mail e senha não podem estar vazios.")
            elif nova_senha != confirmar:
                st.error("As senhas não coincidem.")
            elif len(nova_senha) < 6:
                st.warning("A senha deve ter pelo menos 6 caracteres.")
            else:
                try:
                    auth_response = supabase.auth.sign_up(
                        {
                            "email": novo_email,
                            "password": nova_senha,
                            "options": {"data": {"username": novo_usuario, "nome": nome}},
                        }
                    )

                    user = getattr(auth_response, "user", None)
                    if not user or not getattr(user, "id", None):
                        st.warning(
                            "Conta criada no Auth, mas o retorno não trouxe user.id. "
                            "Verifique confirmação de e-mail/configuração do Auth antes de salvar perfil."
                        )
                    else:
                        _salvar_perfil_usuario(
                            supabase=supabase,
                            user_id=user.id,
                            username=novo_usuario,
                            nome=nome,
                            email=novo_email,
                        )
                        st.success("Conta criada com sucesso! Vá na aba 'Entrar'.")
                except APIError as api_exc:
                    st.error(f"Erro ao salvar no Supabase: {api_exc}")
                except Exception as exc:
                    st.error(f"Erro ao cadastrar no Supabase Auth: {exc}")

    return False
