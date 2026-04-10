import json
from datetime import datetime, timedelta, timezone

import streamlit as st

try:
    import extra_streamlit_components as stx
except Exception:
    stx = None

try:
    from postgrest.exceptions import APIError
except Exception:
    class APIError(Exception):
        pass


AUTH_COOKIE_NAME = "moto_renow_supabase_auth"
AUTH_COOKIE_DAYS = 30


def _get_cookie_manager():
    if stx is None:
        return None
    if "_cookie_manager_auth" not in st.session_state:
        st.session_state["_cookie_manager_auth"] = stx.CookieManager()
    return st.session_state["_cookie_manager_auth"]


def _read_auth_cookie() -> dict:
    manager = _get_cookie_manager()
    if manager is None:
        return {}

    try:
        raw = manager.get(AUTH_COOKIE_NAME)
        if not raw:
            return {}
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write_auth_cookie(data: dict) -> bool:
    manager = _get_cookie_manager()
    if manager is None:
        return False

    try:
        expires_at = datetime.now(timezone.utc) + timedelta(days=AUTH_COOKIE_DAYS)
        manager.set(
            AUTH_COOKIE_NAME,
            json.dumps(data, ensure_ascii=False, separators=(",", ":")),
            expires_at=expires_at,
            key=f"set_{AUTH_COOKIE_NAME}",
        )
        return True
    except Exception:
        return False


def _clear_auth_cookie() -> None:
    manager = _get_cookie_manager()
    if manager is None:
        return
    try:
        manager.delete(AUTH_COOKIE_NAME, key=f"del_{AUTH_COOKIE_NAME}")
    except Exception:
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


def _partial_url(url: str) -> str:
    txt = (url or "").strip()
    if not txt:
        return ""
    if "://" in txt:
        head, tail = txt.split("://", 1)
        return f"{head}://{tail[:18]}..."
    return f"{txt[:24]}..."


def _query_debug_payload(table: str, method: str, field: str, value: str) -> dict:
    return {
        "table": table,
        "method": method,
        "field": field,
        "value": value,
        "status": "pending",
        "row_count": 0,
        "data": None,
        "error": None,
    }


def _set_authenticated_state(session, user, email: str, perfil: dict | None) -> None:
    st.session_state["auth_user_id"] = getattr(user, "id", "")
    st.session_state["auth_user_email"] = _normalized_email(email)
    st.session_state["auth_user_profile"] = perfil or {}
    st.session_state["auth_force_logged_out"] = False
    st.session_state["_post_login_route_applied"] = False
    st.session_state.pop("route", None)
    st.session_state.pop("logado", None)
    st.session_state.pop("expira_em", None)

    try:
        st.query_params.pop("auth", None)
    except Exception:
        try:
            q = st.experimental_get_query_params()
            q.pop("auth", None)
            st.experimental_set_query_params(**q)
        except Exception:
            pass

    st.session_state.pop("_access_cache_key", None)
    st.session_state.pop("_access_cache_value", None)
    st.session_state.pop("_admin_cache_key", None)
    st.session_state.pop("_admin_cache_value", None)

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


def _carregar_perfil_usuario(client, user_id: str, email: str, user_metadata: dict | None = None):
    perfil = None
    email_norm = _normalized_email(email)

    supabase_url = ""
    try:
        supabase_url = str(st.secrets.get("SUPABASE_URL") or "")
    except Exception:
        supabase_url = ""

    if not supabase_url:
        try:
            import os
            supabase_url = str(os.environ.get("SUPABASE_URL") or "")
        except Exception:
            supabase_url = ""

    debug = {
        "table": "usuarios_app",
        "supabase_url_partial": _partial_url(supabase_url),
        "is_local_runtime": _is_local_runtime(client),
        "user_id": user_id,
        "email": email_norm,
        "source": "none",
        "by_id": _query_debug_payload("usuarios_app", "eq", "id", user_id),
        "by_email": _query_debug_payload("usuarios_app", "eq", "email", email_norm),
        "by_email_ilike": _query_debug_payload("usuarios_app", "ilike", "email", email_norm),
    }

    try:
        res = client.table("usuarios_app").select("*").eq("id", user_id).limit(1).execute()
        rows = getattr(res, "data", None) or []
        debug["by_id"]["status"] = "success"
        debug["by_id"]["row_count"] = len(rows)
        debug["by_id"]["data"] = rows[0] if rows else None
        if rows:
            perfil = rows[0]
            debug["source"] = "id"
    except Exception as exc:
        debug["by_id"]["status"] = "error"
        debug["by_id"]["error"] = str(exc)

    if not perfil and email_norm:
        try:
            res = client.table("usuarios_app").select("*").eq("email", email_norm).limit(1).execute()
            rows = getattr(res, "data", None) or []
            debug["by_email"]["status"] = "success"
            debug["by_email"]["row_count"] = len(rows)
            debug["by_email"]["data"] = rows[0] if rows else None
            if rows:
                perfil = rows[0]
                debug["source"] = "email"
        except Exception as exc:
            debug["by_email"]["status"] = "error"
            debug["by_email"]["error"] = str(exc)

    if not perfil and email_norm:
        try:
            res = client.table("usuarios_app").select("*").ilike("email", email_norm).limit(1).execute()
            rows = getattr(res, "data", None) or []
            debug["by_email_ilike"]["status"] = "success"
            debug["by_email_ilike"]["row_count"] = len(rows)
            debug["by_email_ilike"]["data"] = rows[0] if rows else None
            if rows:
                perfil = rows[0]
                debug["source"] = "email_ilike"
        except Exception as exc:
            debug["by_email_ilike"]["status"] = "error"
            debug["by_email_ilike"]["error"] = str(exc)

    st.session_state["_perfil_debug"] = debug

    if not isinstance(perfil, dict):
        perfil = {}

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
        if "role" not in perfil or not str(perfil.get("role", "")).strip():
            perfil["role"] = "admin"

    if perfil:
        perfil["_source"] = debug.get("source", "none")

    return perfil or None


def _persist_supabase_session(auth_response, email: str) -> None:
    try:
        session_obj = getattr(auth_response, "session", None)
        if not session_obj:
            return

        access_token = getattr(session_obj, "access_token", None)
        refresh_token = getattr(session_obj, "refresh_token", None)

        if not access_token or not refresh_token:
            return

        _write_auth_cookie(
            {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "email": _normalized_email(email),
                "saved_at": datetime.now(timezone.utc).isoformat(),
            }
        )
    except Exception:
        pass


def try_restore_auth_session(session, client) -> bool:
    if st.session_state.get("auth_force_logged_out"):
        return False

    if session.is_authenticated or _is_local_runtime(client):
        return bool(session.is_authenticated)

    cookie_data = _read_auth_cookie()
    access_token = str(cookie_data.get("access_token", "")).strip()
    refresh_token = str(cookie_data.get("refresh_token", "")).strip()

    if access_token and refresh_token:
        try:
            client.auth.set_session(access_token, refresh_token)
        except Exception:
            pass

    user = _get_authenticated_user(client)
    if not user:
        _clear_auth_cookie()
        return False

    email = _normalized_email(
        getattr(user, "email", None)
        or st.session_state.get("auth_user_email")
        or cookie_data.get("email", "")
    )
    perfil = _carregar_perfil_usuario(client, user.id, email, getattr(user, "user_metadata", None))
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
    perfil = _carregar_perfil_usuario(client, user.id, email, getattr(user, "user_metadata", None))
    perfil = _build_profile(perfil, user, email)
    st.session_state["auth_user_profile"] = perfil
    st.session_state["auth_user_email"] = email
    st.session_state["auth_user_id"] = getattr(user, "id", st.session_state.get("auth_user_id"))
    st.session_state.pop("_access_cache_key", None)
    st.session_state.pop("_access_cache_value", None)
    st.session_state.pop("_admin_cache_key", None)
    st.session_state.pop("_admin_cache_value", None)


def logout_and_clear(session, client=None) -> None:
    try:
        if client is not None:
            try:
                client.auth.sign_out()
            except Exception:
                pass
        _clear_auth_cookie()
        session.logout()
    except Exception:
        session.logout()


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
        st.session_state["_post_login_route_applied"] = False
        st.session_state.pop("route", None)
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
    st.caption("Planos: Free (teaser de consulta) | Pago (consulta completa + cadastro + diagnostico) | Admin (gestao total).")

    if st.session_state.get("auth_force_logged_out"):
        st.info("Sessao encerrada com sucesso. Faca login novamente.")

    tab_login, tab_cadastro = st.tabs(["Entrar", "Criar Conta"])

    with tab_login:
        email = st.text_input("E-mail", key="login_email")
        senha = st.text_input("Senha", type="password", key="login_pass")

        if st.button("Acessar Sistema", use_container_width=True):
            email_norm = (email or "").strip().lower()
            if not email_norm or not senha:
                st.warning("Por favor, preencha todos os campos.")
            elif "@" not in email_norm:
                st.warning("Informe um e-mail valido para login.")
            else:
                try:
                    auth_response = client.auth.sign_in_with_password(
                        {"email": email_norm, "password": senha}
                    )
                    user = _get_authenticated_user(client)
                    if not user or not getattr(user, "id", None):
                        st.error("Login sem usuario valido retornado pelo Supabase Auth.")
                        return False

                    _persist_supabase_session(auth_response, email_norm)

                    perfil = _carregar_perfil_usuario(
                        client,
                        user.id,
                        email_norm,
                        getattr(user, "user_metadata", None),
                    )
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

        if st.button("Cadastrar", use_container_width=True):
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
