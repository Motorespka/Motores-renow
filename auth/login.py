import streamlit as st
try:
    from postgrest.exceptions import APIError
except Exception:
    class APIError(Exception):
        pass


def _is_local_runtime(client) -> bool:
    return bool(getattr(client, "is_local_runtime", False))


def _get_authenticated_user(client):
    try:
        auth_user_res = client.auth.get_user()
        user = getattr(auth_user_res, "user", None)
        if user and getattr(user, "id", None):
            return user
    except Exception:
        pass
    return None


def _normalized_email(value: str) -> str:
    return (value or "").strip().lower()


def _set_authenticated_state(session, user, email: str, perfil: dict | None) -> None:
    st.session_state["auth_user_id"] = getattr(user, "id", "")
    st.session_state["auth_user_email"] = _normalized_email(email)
    st.session_state["auth_user_profile"] = perfil or {}
    st.session_state["auth_force_logged_out"] = False
    session.login()


def _build_profile(perfil, user, fallback_email: str):
    out = dict(perfil or {}) if isinstance(perfil, dict) else {}
    out.setdefault("email", fallback_email)
    metadata = getattr(user, "user_metadata", None) or {}
    if isinstance(metadata, dict):
        if "is_admin" in metadata and "is_admin" not in out:
            out["is_admin"] = metadata.get("is_admin")
        if "role" in metadata and "role" not in out:
            out["role"] = metadata.get("role")
        if "perfil" in metadata and "perfil" not in out:
            out["perfil"] = metadata.get("perfil")
    return out


def _carregar_perfil_usuario(client, user_id: str, email: str):
    perfil = None
    try:
        res = client.table("usuarios_app").select("*").eq("id", user_id).limit(1).execute()
        if res.data:
            perfil = res.data[0]
    except Exception:
        perfil = None

    if not perfil:
        try:
            res = client.table("usuarios_app").select("*").eq("email", email).limit(1).execute()
            if res.data:
                perfil = res.data[0]
        except Exception:
            perfil = None

    if not perfil and email:
        try:
            res = client.table("usuarios_app").select("*").ilike("email", email).limit(1).execute()
            if res.data:
                perfil = res.data[0]
        except Exception:
            perfil = None

    if not isinstance(perfil, dict):
        perfil = {}

    # Compatibilidade opcional com tabela dedicada de administradores.
    admin_match = False
    for col, value in [
        ("id", user_id),
        ("user_id", user_id),
        ("usuario_id", user_id),
        ("auth_user_id", user_id),
        ("email", email),
        ("user_email", email),
    ]:
        if not value:
            continue
        try:
            res = client.table("admin").select("*").eq(col, value).limit(1).execute()
            if res.data:
                admin_match = True
                break
        except Exception:
            continue

    if not admin_match and email:
        for col in ["email", "user_email"]:
            try:
                res = client.table("admin").select("*").ilike(col, email).limit(1).execute()
                if res.data:
                    admin_match = True
                    break
            except Exception:
                continue

    if admin_match:
        perfil["is_admin"] = True
        if "role" not in perfil:
            perfil["role"] = "admin"

    return perfil or None


def try_restore_auth_session(session, client) -> bool:
    if st.session_state.get("auth_force_logged_out"):
        return False

    if session.is_authenticated or _is_local_runtime(client):
        return bool(session.is_authenticated)

    user = _get_authenticated_user(client)
    if not user:
        return False

    email = _normalized_email(getattr(user, "email", None) or st.session_state.get("auth_user_email") or "")
    perfil = _carregar_perfil_usuario(client, user.id, email)
    perfil = _build_profile(perfil, user, email)
    _set_authenticated_state(session, user, email, perfil)
    return True


def sync_authenticated_profile(session, client) -> None:
    if not session.is_authenticated or _is_local_runtime(client):
        return

    user = _get_authenticated_user(client)
    if not user:
        return

    email = _normalized_email(getattr(user, "email", None) or st.session_state.get("auth_user_email") or "")
    perfil = _carregar_perfil_usuario(client, user.id, email)
    perfil = _build_profile(perfil, user, email)
    st.session_state["auth_user_profile"] = perfil
    st.session_state["auth_user_email"] = email
    st.session_state["auth_user_id"] = getattr(user, "id", st.session_state.get("auth_user_id"))


def _render_local_login(session) -> bool:
    if session.is_authenticated:
        return True

    st.title("Moto-Renow - Acesso Tecnico (Local)")
    st.caption("Ambiente de teste sem dependencia de Supabase Auth.")

    email = st.text_input("E-mail tecnico", key="local_login_email")
    nome = st.text_input("Nome tecnico", key="local_login_nome")

    if st.button("Entrar em modo local", use_container_width=True):
        email_norm = (email or "dev@local").strip().lower()
        nome_norm = (nome or "Tecnico DEV").strip()
        st.session_state["auth_user_id"] = f"local-{email_norm}"
        st.session_state["auth_user_email"] = email_norm
        st.session_state["auth_user_profile"] = {
            "nome": nome_norm,
            "email": email_norm,
            "local_mode": True,
        }
        session.login()
        st.session_state["auth_force_logged_out"] = False
        st.success("Login local realizado.")
        st.rerun()

    return False


def render_login(session, client) -> bool:
    if session.is_authenticated:
        return True

    if _is_local_runtime(client):
        return _render_local_login(session)

    if try_restore_auth_session(session, client):
        return True

    st.title("Moto-Renow - Acesso Tecnico")
    if st.session_state.get("auth_force_logged_out"):
        st.info("Sessao encerrada com sucesso. Faca login novamente.")

    tab_login, tab_cadastro = st.tabs(["Entrar", "Criar Conta"])

    with tab_login:
        email = st.text_input("E-mail", key="login_email")
        senha = st.text_input("Senha", type="password", key="login_pass")

        if st.button("Acessar Sistema"):
            email_norm = (email or "").strip().lower()
            if not email_norm or not senha:
                st.warning("Por favor, preencha todos os campos.")
            elif "@" not in email_norm:
                st.warning("Informe um e-mail valido para login.")
            else:
                try:
                    client.auth.sign_in_with_password({"email": email_norm, "password": senha})
                    user = _get_authenticated_user(client)
                    if not user or not getattr(user, "id", None):
                        st.error("Login sem usuario valido retornado pelo Supabase Auth.")
                        return False

                    perfil = _carregar_perfil_usuario(client, user.id, email_norm)
                    perfil = _build_profile(perfil, user, email_norm)
                    _set_authenticated_state(session, user, email_norm, perfil)
                    st.success("Login realizado!")
                    st.rerun()
                except APIError as api_exc:
                    msg = str(api_exc)
                    if "Invalid login credentials" in msg:
                        st.error("Credenciais invalidas. Verifique e-mail/senha no Supabase Auth.")
                    else:
                        st.error(f"Erro Supabase (login): {api_exc}")
                except Exception as exc:
                    st.error(f"Erro no login: {exc}")

    with tab_cadastro:
        st.info("Crie seu acesso usando Supabase Auth.")
        nome = st.text_input("Nome", key="reg_nome")
        novo_usuario = st.text_input("Nome de usuario", key="reg_user")
        novo_email = st.text_input("E-mail", key="reg_email")
        nova_senha = st.text_input("Definir Senha", type="password", key="reg_pass")
        confirmar = st.text_input("Confirmar Senha", type="password", key="reg_conf")

        if st.button("Cadastrar"):
            email_reg_norm = (novo_email or "").strip().lower()
            username_norm = (novo_usuario or "").strip()
            nome_norm = (nome or "").strip()

            if not nome_norm or not username_norm or not email_reg_norm or not nova_senha:
                st.error("Nome, usuario, e-mail e senha nao podem estar vazios.")
            elif "@" not in email_reg_norm:
                st.error("Informe um e-mail valido para cadastro.")
            elif nova_senha != confirmar:
                st.error("As senhas nao coincidem.")
            elif len(nova_senha) < 6:
                st.warning("A senha deve ter pelo menos 6 caracteres.")
            else:
                try:
                    auth_response = client.auth.sign_up(
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
                except APIError as api_exc:
                    st.error(f"Erro ao cadastrar no Supabase Auth: {api_exc}")
                except Exception as exc:
                    st.error(f"Erro ao cadastrar no Supabase Auth: {exc}")

    return False
