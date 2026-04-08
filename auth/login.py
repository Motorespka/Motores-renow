import streamlit as st
from postgrest.exceptions import APIError


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


def render_login(session, supabase) -> bool:
    if session.is_authenticated:
        return True

    st.title("🔐 Moto-Renow • Acesso Técnico")

    tab_login, tab_cadastro = st.tabs(["Entrar", "Criar Conta"])

    with tab_login:
        email = st.text_input("E-mail", key="login_email")
        senha = st.text_input("Senha", type="password", key="login_pass")

        if st.button("Acessar Sistema"):
            email_norm = (email or "").strip().lower()
            if not email_norm or not senha:
                st.warning("Por favor, preencha todos os campos.")
            elif "@" not in email_norm:
                st.warning("Informe um e-mail válido para login.")
            else:
                try:
                    supabase.auth.sign_in_with_password({"email": email_norm, "password": senha})
                    auth_user_res = supabase.auth.get_user()
                    user = getattr(auth_user_res, "user", None)
                    if not user or not getattr(user, "id", None):
                        st.error("Login sem usuário válido retornado pelo Supabase Auth.")
                        return False

                    perfil = _carregar_perfil_usuario(supabase, user.id, email_norm)
                    st.session_state["auth_user_id"] = user.id
                    st.session_state["auth_user_email"] = email_norm
                    st.session_state["auth_user_profile"] = perfil
                    session.login()
                    st.success("Login realizado!")
                    st.rerun()
                except APIError as api_exc:
                    msg = str(api_exc)
                    if "Invalid login credentials" in msg:
                        st.error(
                            "Credenciais inválidas. Verifique e-mail/senha e confirme seu e-mail de cadastro no Supabase Auth."
                        )
                        st.info(
                            "Se você acabou de criar conta, confirme o e-mail antes de tentar login. "
                            "Sem confirmação, o Supabase pode retornar 'Invalid login credentials'."
                        )
                    else:
                        st.error(f"Erro Supabase (login): {api_exc}")
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
            email_reg_norm = (novo_email or "").strip().lower()
            username_norm = (novo_usuario or "").strip()
            nome_norm = (nome or "").strip()

            if not nome_norm or not username_norm or not email_reg_norm or not nova_senha:
                st.error("Nome, usuário, e-mail e senha não podem estar vazios.")
            elif "@" not in email_reg_norm:
                st.error("Informe um e-mail válido para cadastro.")
            elif nova_senha != confirmar:
                st.error("As senhas não coincidem.")
            elif len(nova_senha) < 6:
                st.warning("A senha deve ter pelo menos 6 caracteres.")
            else:
                try:
                    auth_response = supabase.auth.sign_up(
                        {
                            "email": email_reg_norm,
                            "password": nova_senha,
                            "options": {"data": {"username": username_norm, "nome": nome_norm}},
                        }
                    )
                    user = getattr(auth_response, "user", None)
                    if not user:
                        st.warning("Conta criada no Auth. Verifique seu e-mail para confirmar o acesso.")
                    else:
                        st.success("Conta criada no Auth com sucesso!")
                        st.info(
                            "Se a confirmação de e-mail estiver habilitada no projeto, "
                            "confirme o e-mail antes de tentar login."
                        )
                except APIError as api_exc:
                    st.error(f"Erro ao cadastrar no Supabase Auth: {api_exc}")
                except Exception as exc:
                    st.error(f"Erro ao cadastrar no Supabase Auth: {exc}")

    return False
