import base64
from datetime import datetime, timedelta
import hashlib
import hmac
import json
import os
import time

import streamlit as st

try:
    from postgrest.exceptions import APIError
except Exception:
    class APIError(Exception):
        pass

PERSISTED_AUTH_QP_KEY = "mrw_auth"
PERSISTED_AUTH_TTL_HOURS = 8
PROFILE_CACHE_TTL_SECONDS = 45
PROFILE_SYNC_TTL_SECONDS = 20


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


def _to_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _get_query_params() -> dict:
    try:
        return dict(st.query_params)
    except Exception:
        try:
            return dict(st.experimental_get_query_params())
        except Exception:
            return {}


def _read_query_param(name: str) -> str:
    value = _get_query_params().get(name)
    if isinstance(value, list):
        value = value[0] if value else ""
    return _to_text(value)


def _write_query_param(name: str, value: str | None) -> None:
    current = _read_query_param(name)
    target = _to_text(value)
    if value is not None and current == target:
        return
    if value is None and not current:
        return

    try:
        if value is None:
            st.query_params.pop(name, None)
        else:
            st.query_params[name] = target
        return
    except Exception:
        pass

    try:
        params = _get_query_params()
        if value is None:
            params.pop(name, None)
        else:
            params[name] = target
        st.experimental_set_query_params(**params)
    except Exception:
        pass


def _secret_key() -> bytes:
    try:
        auth_secret = _to_text(st.secrets.get("AUTH_SECRET_KEY"))
    except Exception:
        auth_secret = ""
    try:
        app_secret = _to_text(st.secrets.get("APP_PASSWORD"))
    except Exception:
        app_secret = ""

    key = (
        auth_secret
        or _to_text(os.environ.get("AUTH_SECRET_KEY"))
        or app_secret
        or _to_text(os.environ.get("APP_PASSWORD"))
        or "dev"
    )
    return key.encode("utf-8")


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")


def _b64url_decode(txt: str) -> bytes:
    padding = "=" * (-len(txt) % 4)
    return base64.urlsafe_b64decode((txt + padding).encode("utf-8"))


def _sign(payload: str) -> str:
    signature = hmac.new(_secret_key(), payload.encode("utf-8"), hashlib.sha256).digest()
    return _b64url_encode(signature)


def _build_persisted_auth_token(refresh_token: str) -> str:
    payload = {
        "rt": _to_text(refresh_token),
        "exp": int((datetime.utcnow() + timedelta(hours=PERSISTED_AUTH_TTL_HOURS)).timestamp()),
    }
    payload_txt = json.dumps(payload, separators=(",", ":"), ensure_ascii=True)
    payload_b64 = _b64url_encode(payload_txt.encode("utf-8"))
    return f"{payload_b64}.{_sign(payload_b64)}"


def _parse_persisted_auth_token(raw_token: str) -> str:
    token = _to_text(raw_token)
    if not token or "." not in token:
        return ""
    payload_b64, signature = token.rsplit(".", 1)
    if not hmac.compare_digest(_sign(payload_b64), signature):
        return ""

    try:
        payload_raw = _b64url_decode(payload_b64).decode("utf-8")
        payload = json.loads(payload_raw)
    except Exception:
        return ""

    refresh_token = _to_text(payload.get("rt"))
    try:
        exp_ts = int(payload.get("exp") or 0)
    except Exception:
        return ""

    if not refresh_token or exp_ts <= 0:
        return ""
    if datetime.utcnow().timestamp() > exp_ts:
        return ""
    return refresh_token


def _clear_persisted_auth_query_param() -> None:
    _write_query_param(PERSISTED_AUTH_QP_KEY, None)


def _persist_refresh_token(refresh_token: str) -> None:
    token = _to_text(refresh_token)
    if not token:
        return
    _write_query_param(PERSISTED_AUTH_QP_KEY, _build_persisted_auth_token(token))


def _persist_supabase_refresh_token(client) -> None:
    if _is_local_runtime(client):
        return
    try:
        session = client.auth.get_session()
    except Exception:
        return
    _persist_refresh_token(getattr(session, "refresh_token", None))


def _persist_auth_response(auth_response) -> None:
    session = getattr(auth_response, "session", None)
    _persist_refresh_token(getattr(session, "refresh_token", None))


def _restore_user_from_persisted_refresh_token(client):
    if _is_local_runtime(client):
        return None

    persisted = _read_query_param(PERSISTED_AUTH_QP_KEY)
    refresh_token = _parse_persisted_auth_token(persisted)
    if not refresh_token:
        if persisted:
            _clear_persisted_auth_query_param()
        return None

    try:
        auth_response = client.auth.refresh_session(refresh_token)
    except Exception:
        _clear_persisted_auth_query_param()
        return None

    # Sessao fica no cliente Supabase; nao regravar refresh na URL (evita partilhar ?mrw_auth=).
    _clear_persisted_auth_query_param()

    user = getattr(auth_response, "user", None)
    if user and getattr(user, "id", None):
        return user
    return _get_authenticated_user(client)


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


def _default_username(email: str, user_id: str) -> str:
    base = _normalized_email(email).split("@")[0]
    base = "".join(ch for ch in base if ch.isalnum() or ch == "_")
    if not base:
        base = "user"
    suffix = (user_id or "").replace("-", "")[:6]
    return f"{base}_{suffix}" if suffix else base


def _profile_cache_key(user_id: str, email: str) -> str:
    raw = f"{_to_text(user_id)}|{_normalized_email(email)}"
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]
    return f"_perfil_cache_{digest}"


def _read_cached_profile(user_id: str, email: str):
    key = _profile_cache_key(user_id, email)
    cached = st.session_state.get(key)
    if not isinstance(cached, dict):
        return None
    ts = float(cached.get("ts") or 0.0)
    if (time.time() - ts) > PROFILE_CACHE_TTL_SECONDS:
        return None
    perfil = cached.get("perfil")
    if isinstance(perfil, dict):
        return dict(perfil)
    return None


def _write_cached_profile(user_id: str, email: str, perfil: dict | None) -> None:
    if not user_id and not email:
        return
    key = _profile_cache_key(user_id, email)
    st.session_state[key] = {
        "ts": float(time.time()),
        "perfil": dict(perfil or {}),
    }


def _ensure_usuario_app_profile(client, user, email: str, perfil: dict | None) -> None:
    if _is_local_runtime(client):
        return

    user_id = _to_text(getattr(user, "id", ""))
    email_norm = _normalized_email(email or getattr(user, "email", ""))
    if not user_id or not email_norm:
        return

    existing = perfil if isinstance(perfil, dict) else {}
    existing_id = _to_text(existing.get("id"))
    existing_email = _normalized_email(existing.get("email"))
    if existing_id == user_id and existing_email == email_norm:
        return

    metadata = getattr(user, "user_metadata", None) or {}
    if not isinstance(metadata, dict):
        metadata = {}

    username = _to_text(existing.get("username")) or _to_text(metadata.get("username")) or _default_username(email_norm, user_id)
    nome = _to_text(existing.get("nome")) or _to_text(metadata.get("nome"))
    role = _to_text(existing.get("role")).lower() or "user"
    plan = _to_text(existing.get("plan")).lower() or "free"
    ativo = existing.get("ativo")
    if ativo is None:
        ativo = True

    payload = {
        "id": user_id,
        "email": email_norm,
        "username": username,
        "nome": nome or None,
        "role": role,
        "plan": plan,
        "ativo": bool(ativo),
    }

    try:
        client.table("usuarios_app").upsert(payload, on_conflict="id").execute()
    except Exception:
        return

    merged = dict(existing)
    merged.update(payload)
    _write_cached_profile(user_id, email_norm, merged)


def _set_authenticated_state(session, user, email: str, perfil: dict | None) -> None:
    st.session_state["auth_user_id"] = getattr(user, "id", "")
    st.session_state["auth_user_email"] = _normalized_email(email)
    st.session_state["auth_user_profile"] = perfil or {}
    st.session_state["auth_force_logged_out"] = False
    st.session_state["_post_login_route_applied"] = False
    st.session_state["_auth_profile_sync_ts"] = 0.0
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
    cached = _read_cached_profile(user_id, email)
    if isinstance(cached, dict) and cached:
        return cached

    perfil = None
    email_norm = _normalized_email(email)
    user_meta = user_metadata if isinstance(user_metadata, dict) else {}
    username_hint = _to_text(user_meta.get("username"))
    supabase_url = ""
    try:
        supabase_url = str(st.secrets.get("SUPABASE_URL") or "")
    except Exception:
        supabase_url = ""
    if not supabase_url:
        try:
            supabase_url = str(os.environ.get("SUPABASE_URL") or "")
        except Exception:
            supabase_url = ""

    debug = {
        "table": "usuarios_app",
        "supabase_url_partial": _partial_url(supabase_url),
        "is_local_runtime": _is_local_runtime(client),
        "user_id": user_id,
        "email": email_norm,
        "username_hint": username_hint,
        "source": "none",
        "by_id": _query_debug_payload("usuarios_app", "eq", "id", user_id),
        "by_email": _query_debug_payload("usuarios_app", "eq", "email", email_norm),
        "by_email_ilike": _query_debug_payload("usuarios_app", "ilike", "email", email_norm),
        "by_username": _query_debug_payload("usuarios_app", "eq", "username", username_hint),
        "by_username_ilike": _query_debug_payload("usuarios_app", "ilike", "username", username_hint),
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

    if not perfil and username_hint:
        try:
            res = client.table("usuarios_app").select("*").eq("username", username_hint).limit(1).execute()
            rows = getattr(res, "data", None) or []
            debug["by_username"]["status"] = "success"
            debug["by_username"]["row_count"] = len(rows)
            debug["by_username"]["data"] = rows[0] if rows else None
            if rows:
                perfil = rows[0]
                debug["source"] = "username"
        except Exception as exc:
            debug["by_username"]["status"] = "error"
            debug["by_username"]["error"] = str(exc)

    if not perfil and username_hint:
        try:
            res = client.table("usuarios_app").select("*").ilike("username", username_hint).limit(1).execute()
            rows = getattr(res, "data", None) or []
            debug["by_username_ilike"]["status"] = "success"
            debug["by_username_ilike"]["row_count"] = len(rows)
            debug["by_username_ilike"]["data"] = rows[0] if rows else None
            if rows:
                perfil = rows[0]
                debug["source"] = "username_ilike"
        except Exception as exc:
            debug["by_username_ilike"]["status"] = "error"
            debug["by_username_ilike"]["error"] = str(exc)

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
        perfil["_admin_match"] = True

    if perfil:
        perfil["_source"] = debug.get("source", "none")

    final_profile = perfil or None
    if isinstance(final_profile, dict):
        _write_cached_profile(user_id, email_norm, final_profile)
    return final_profile


def try_restore_auth_session(session, client) -> bool:
    if st.session_state.get("auth_force_logged_out"):
        return False

    if session.is_authenticated or _is_local_runtime(client):
        return bool(session.is_authenticated)

    user = _get_authenticated_user(client)
    if not user:
        user = _restore_user_from_persisted_refresh_token(client)
    if not user:
        return False

    email = _normalized_email(getattr(user, "email", None) or st.session_state.get("auth_user_email") or "")
    perfil = _carregar_perfil_usuario(client, user.id, email, getattr(user, "user_metadata", None))
    perfil = _build_profile(perfil, user, email)
    _ensure_usuario_app_profile(client, user, email, perfil)
    _set_authenticated_state(session, user, email, perfil)
    return True


def sync_authenticated_profile(session, client) -> None:
    if not session.is_authenticated or _is_local_runtime(client):
        return

    now = float(time.time())
    last_sync = float(st.session_state.get("_auth_profile_sync_ts") or 0.0)
    if (now - last_sync) < PROFILE_SYNC_TTL_SECONDS:
        return

    user = _get_authenticated_user(client)
    if not user:
        return

    email = _normalized_email(getattr(user, "email", None) or st.session_state.get("auth_user_email") or "")
    perfil = _carregar_perfil_usuario(client, user.id, email, getattr(user, "user_metadata", None))
    perfil = _build_profile(perfil, user, email)
    _ensure_usuario_app_profile(client, user, email, perfil)

    prev_profile = st.session_state.get("auth_user_profile")
    prev_email = _normalized_email(st.session_state.get("auth_user_email") or "")
    prev_user_id = _to_text(st.session_state.get("auth_user_id"))
    new_user_id = _to_text(getattr(user, "id", prev_user_id))

    profile_changed = (prev_profile != perfil) or (prev_email != email) or (prev_user_id != new_user_id)

    st.session_state["auth_user_profile"] = perfil
    st.session_state["auth_user_email"] = email
    st.session_state["auth_user_id"] = new_user_id
    if profile_changed:
        st.session_state.pop("_access_cache_key", None)
        st.session_state.pop("_access_cache_value", None)
        st.session_state.pop("_admin_cache_key", None)
        st.session_state.pop("_admin_cache_value", None)

    st.session_state["_auth_profile_sync_ts"] = now


def logout_and_clear(session, client=None) -> None:
    st.session_state["auth_force_logged_out"] = True

    try:
        if client is not None and not _is_local_runtime(client):
            client.auth.sign_out()
    except Exception:
        pass

    for key in [
        "auth_user_id",
        "auth_user_email",
        "auth_user_profile",
        "route",
        "_auth_profile_sync_ts",
        "_access_cache_key",
        "_access_cache_value",
        "_admin_cache_key",
        "_admin_cache_value",
        "logado",
        "expira_em",
    ]:
        st.session_state.pop(key, None)

    _clear_persisted_auth_query_param()
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
        username_norm = _default_username(email_norm, f"local-{email_norm}")
        st.session_state["auth_user_id"] = f"local-{email_norm}"
        st.session_state["auth_user_email"] = email_norm
        st.session_state["auth_user_profile"] = {
            "id": f"local-{email_norm}",
            "username": username_norm,
            "nome": nome_norm,
            "email": email_norm,
            "local_mode": True,
            "role": "admin",
            "plan": "paid",
            "ativo": True,
            "is_admin": True,
            "_admin_match": True,
        }
        st.session_state.pop("_access_cache_key", None)
        st.session_state.pop("_access_cache_value", None)
        st.session_state.pop("_admin_cache_key", None)
        st.session_state.pop("_admin_cache_value", None)
        st.session_state["_auth_profile_sync_ts"] = 0.0
        session.login()
        st.session_state["auth_force_logged_out"] = False
        st.session_state["_post_login_route_applied"] = False
        st.session_state.pop("route", None)
        st.session_state.pop("logado", None)
        st.session_state.pop("expira_em", None)
        _clear_persisted_auth_query_param()
        st.success("Login local realizado.")
        st.rerun()

    return False


def render_login(session, client) -> bool:
    if session.is_authenticated:
        if not _is_local_runtime(client):
            try:
                if _read_query_param(PERSISTED_AUTH_QP_KEY):
                    _clear_persisted_auth_query_param()
            except Exception:
                pass
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

        if st.button("Acessar Sistema"):
            email_norm = (email or "").strip().lower()
            if not email_norm or not senha:
                st.warning("Por favor, preencha todos os campos.")
            elif "@" not in email_norm:
                st.warning("Informe um e-mail valido para login.")
            else:
                try:
                    auth_response = client.auth.sign_in_with_password({"email": email_norm, "password": senha})
                    user = _get_authenticated_user(client) or getattr(auth_response, "user", None)
                    if not user or not getattr(user, "id", None):
                        st.error("Login sem usuario valido retornado pelo Supabase Auth.")
                        return False

                    perfil = _carregar_perfil_usuario(client, user.id, email_norm, getattr(user, "user_metadata", None))
                    perfil = _build_profile(perfil, user, email_norm)
                    _ensure_usuario_app_profile(client, user, email_norm, perfil)
                    _set_authenticated_state(session, user, email_norm, perfil)
                    _clear_persisted_auth_query_param()
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
                        try:
                            _ensure_usuario_app_profile(
                                client,
                                user,
                                email_reg_norm,
                                {
                                    "username": username_norm,
                                    "nome": nome_norm,
                                    "role": "user",
                                    "plan": "free",
                                    "ativo": True,
                                },
                            )
                        except Exception:
                            pass
                        st.success("Conta criada no Auth com sucesso!")
                except APIError as api_exc:
                    st.error(f"Erro ao cadastrar no Supabase Auth: {api_exc}")
                except Exception as exc:
                    st.error(f"Erro ao cadastrar no Supabase Auth: {exc}")

    return False
