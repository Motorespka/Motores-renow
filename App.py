from pathlib import Path
import hashlib
import json
import os
import time
import uuid

import streamlit as st
import streamlit.components.v1 as components

try:
    from supabase import create_client
except Exception:
    create_client = None

from auth.login import render_login, sync_authenticated_profile
from core.access_control import can_access_cadastro, can_access_paid_features, get_access_profile
from core.development_mode import ensure_dev_mode_access, is_dev_mode, render_dev_banner_if_needed
from core.feature_flags import get_feature_flags
from core.navigation import AppContext, Route, Router, render_navigation_sidebar
from core.session_manager import SessionManager
from page import admin_panel, atualizacoes, cadastro, consulta, diagnostico, edit, hub_comercial, motor_detail
from services.database import bootstrap_database, build_local_runtime_client

st.set_page_config(page_title="Moto-Renow", page_icon=":gear:", layout="wide")
DEBUG_ACCESS = str(os.environ.get("DEBUG_ACCESS", "")).strip().lower() in {"1", "true", "yes", "on"}
RUNTIME_CACHE_QP_KEY = "mrw_sid"


def _read_secret_or_env(*names: str) -> str:
    for name in names:
        try:
            value = st.secrets.get(name)
            if value:
                return str(value).strip()
        except Exception:
            pass
        value = os.environ.get(name)
        if value:
            return str(value).strip()
    return ""


def _read_int_secret_or_env(*names: str, default: int, minimum: int = 5, maximum: int = 180) -> int:
    for name in names:
        raw = ""
        try:
            value = st.secrets.get(name)
            if value is not None:
                raw = str(value).strip()
        except Exception:
            raw = ""
        if not raw:
            env_value = os.environ.get(name)
            if env_value:
                raw = str(env_value).strip()
        if not raw:
            continue
        try:
            parsed = int(raw)
            if parsed < minimum:
                return minimum
            if parsed > maximum:
                return maximum
            return parsed
        except Exception:
            continue
    if default < minimum:
        return minimum
    if default > maximum:
        return maximum
    return default


def _to_plain_mapping(value) -> dict:
    try:
        if value is None:
            return {}
        if isinstance(value, dict):
            return {str(k): str(v) for k, v in value.items()}
        return {str(k): str(v) for k, v in dict(value).items()}
    except Exception:
        return {}


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
    return str(value or "").strip()


def _write_query_param(name: str, value: str | None) -> None:
    current = _read_query_param(name)
    target = str(value or "").strip()
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


def _normalize_cache_key(raw_value) -> str:
    value = str(raw_value or "").strip().lower()
    if len(value) != 24:
        return ""
    if all(ch in "0123456789abcdef" for ch in value):
        return value
    return ""


def _resolve_browser_cache_key() -> str:
    cached = _normalize_cache_key(st.session_state.get("_browser_cache_key"))
    if cached:
        return cached

    cookies = {}
    headers = {}
    try:
        cookies = _to_plain_mapping(getattr(st.context, "cookies", {}))
    except Exception:
        cookies = {}
    try:
        headers = _to_plain_mapping(getattr(st.context, "headers", {}))
    except Exception:
        headers = {}

    user_agent = str(headers.get("user-agent", "")).strip()
    accept_language = str(headers.get("accept-language", "")).strip()
    host = str(headers.get("host", "")).strip()
    has_fingerprint_signal = bool(cookies) or bool(user_agent) or bool(accept_language) or bool(host)

    fingerprint = {
        "cookies": cookies,
        "user_agent": user_agent,
        "accept_language": accept_language,
        "host": host,
    }
    if has_fingerprint_signal:
        serialized = json.dumps(fingerprint, sort_keys=True, ensure_ascii=True)
        key = hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:24]
    else:
        from_query = _normalize_cache_key(_read_query_param(RUNTIME_CACHE_QP_KEY))
        if from_query:
            key = from_query
        else:
            key = uuid.uuid4().hex[:24]
            _write_query_param(RUNTIME_CACHE_QP_KEY, key)

    st.session_state["_browser_cache_key"] = key
    return key


@st.cache_resource
def init_connection(mode: str, cache_key: str):
    _ = cache_key
    if mode == "DEV":
        return build_local_runtime_client(mode="DEV")

    if create_client is None:
        raise RuntimeError("SDK do Supabase indisponivel neste ambiente.")

    url = _read_secret_or_env("SUPABASE_URL")
    key = _read_secret_or_env("SUPABASE_KEY", "SUPABASE_ANON_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL/SUPABASE_KEY (ou SUPABASE_ANON_KEY) nao configurados.")

    return create_client(url, key)


def bootstrap_styles() -> None:
    css_path = Path(__file__).resolve().parent / "assets" / "style.css"
    st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def build_router() -> Router:
    router = Router()
    router.register(Route.CADASTRO, cadastro.show)
    router.register(Route.CONSULTA, consulta.show)
    router.register(Route.ATUALIZACOES, atualizacoes.show)
    router.register(Route.DETALHE, motor_detail.show)
    router.register(Route.EDIT, edit.show)
    router.register(Route.DIAGNOSTICO, diagnostico.show)
    router.register(Route.ADMIN, admin_panel.show)
    router.register(Route.HUB_COMERCIAL, hub_comercial.show)
    return router


def bootstrap_system(session: SessionManager) -> None:
    bootstrap_database()
    session.bootstrap()
    try:
        bootstrap_styles()
    except Exception:
        pass


def validate_database_schema(client) -> None:
    try:
        client.table("motores").select("id").limit(1).execute()
    except Exception as exc:
        msg = str(exc).lower()
        if any(token in msg for token in ["permission", "row level", "rls", "jwt", "not authenticated"]):
            return
        raise


def resolve_runtime_mode() -> str:
    env_var = str(os.environ.get("ENV", "")).strip().upper()
    if env_var:
        return env_var

    try:
        env = str(st.secrets.get("ENV", "PROD")).strip().upper()
    except Exception:
        env = ""
    if env:
        return env

    has_supabase = bool(_read_secret_or_env("SUPABASE_URL")) and bool(
        _read_secret_or_env("SUPABASE_KEY", "SUPABASE_ANON_KEY")
    )

    if not has_supabase:
        return "DEV"

    return "PROD"


def connect_runtime_client(mode: str):
    target_mode = "DEV" if str(mode).upper() == "DEV" else "PROD"
    cache_key = _resolve_browser_cache_key()

    if target_mode == "DEV":
        runtime = init_connection("DEV", cache_key)
    else:
        runtime = init_connection("PROD", cache_key)
        validate_database_schema(runtime)

    st.session_state["_runtime_client"] = runtime
    st.session_state["_runtime_client_mode"] = target_mode
    st.session_state["_runtime_client_cache_key"] = cache_key
    return runtime


def _read_route_state(session: SessionManager) -> str:
    route = st.session_state.get("route")
    if isinstance(route, str) and route.strip():
        return route.strip().lower()
    try:
        route = session.get_route().value
    except Exception:
        route = ""
    route = str(route or "").strip().lower()
    st.session_state["route"] = route
    return route


def _set_route_state(session: SessionManager, route_value: str) -> None:
    route_value = str(route_value or "").strip().lower()
    st.session_state["route"] = route_value
    if route_value in {r.value for r in Route}:
        session.set_route(Route(route_value))


def _debug_access_state(access: dict, current_before: str, current_after: str) -> None:
    if not DEBUG_ACCESS:
        return
    supabase_url = _read_secret_or_env("SUPABASE_URL")
    supabase_key = _read_secret_or_env("SUPABASE_KEY", "SUPABASE_ANON_KEY")
    project_ref = ""
    if ".supabase.co" in supabase_url:
        try:
            project_ref = supabase_url.split("://", 1)[-1].split(".supabase.co", 1)[0]
        except Exception:
            project_ref = ""
    expected_project_ref = _read_secret_or_env("SUPABASE_PROJECT_REF", "EXPECTED_SUPABASE_PROJECT_REF")
    project_ref_match = None
    if expected_project_ref:
        project_ref_match = project_ref == expected_project_ref
    masked_key = ""
    if supabase_key:
        if len(supabase_key) > 12:
            masked_key = f"{supabase_key[:6]}...{supabase_key[-4:]}"
        else:
            masked_key = f"{supabase_key[:3]}..."

    st.write("DEBUG auth_user_id:", st.session_state.get("auth_user_id"))
    st.write("DEBUG auth_user_email:", st.session_state.get("auth_user_email"))
    st.write("DEBUG auth_user_profile:", st.session_state.get("auth_user_profile"))
    st.write(
        "DEBUG supabase_env:",
        {
            "url_partial": (supabase_url[:28] + "...") if supabase_url else "",
            "project_ref": project_ref,
            "expected_project_ref": expected_project_ref,
            "project_ref_match": project_ref_match,
            "anon_key_masked": masked_key,
            "client_initialized": st.session_state.get("_supabase_client") is not None,
            "is_local_runtime": bool(getattr(st.session_state.get("_supabase_client"), "is_local_runtime", False)),
        },
    )
    st.write("DEBUG access:", access)
    st.write("DEBUG _perfil_debug:", st.session_state.get("_perfil_debug"))
    st.write("DEBUG _access_profile_debug:", st.session_state.get("_access_profile_debug"))
    st.write("DEBUG current_route_before:", current_before)
    st.write("DEBUG current_route_after:", current_after)


def _render_scroll_reset_if_needed() -> None:
    token = int(st.session_state.get("_scroll_reset_token", 0) or 0)
    rendered = int(st.session_state.get("_scroll_reset_rendered", 0) or 0)
    if token <= 0 or token == rendered:
        return

    st.session_state["_scroll_reset_rendered"] = token
    html_payload = """
        <script>
        (function () {
            const jumpTop = function () {
                try {
                    const root = window.parent || window;
                    const doc = root.document;
                    const candidates = [
                        doc.querySelector('[data-testid="stAppViewContainer"]'),
                        doc.querySelector("section.main"),
                        doc.scrollingElement,
                        doc.documentElement,
                        doc.body,
                    ].filter(Boolean);

                    for (const el of candidates) {
                        try { if (typeof el.scrollTo === "function") el.scrollTo(0, 0); } catch (e) {}
                        try { el.scrollTop = 0; } catch (e) {}
                    }

                    try { if (typeof root.scrollTo === "function") root.scrollTo(0, 0); } catch (e) {}
                } catch (e) {}
            };

            jumpTop();
            setTimeout(jumpTop, 30);
            setTimeout(jumpTop, 120);
        })();
        </script>
    """ + f"\n<div style=\"display:none\">{token}</div>\n"

    components.html(
        html_payload,
        height=1,
        width=1,
    )


def _resolve_live_update_seconds(route: str) -> int:
    route_value = str(route or "").strip().lower()
    default_seconds = 8
    if route_value in {"cadastro", "diagnostico", "edit"}:
        default_seconds = 20
    if route_value == "admin":
        default_seconds = 12
    return _read_int_secret_or_env("LIVE_UPDATE_SECONDS", default=default_seconds, minimum=5, maximum=180)


def _render_live_update_if_needed(flags, access: dict, route: str) -> None:
    if not bool(access.get("authenticated")):
        return
    if not bool(getattr(flags, "enable_live_updates", True)):
        return

    route_value = str(route or "").strip().lower()
    if not route_value or route_value == "login":
        return

    interval_seconds = _resolve_live_update_seconds(route_value)
    state_key = f"_live_update_last_full_rerun_{route_value}"

    if hasattr(st, "fragment"):
        @st.fragment(run_every=interval_seconds)
        def _live_update_fragment() -> None:
            current_route = str(st.session_state.get("route") or "").strip().lower()
            if current_route != route_value:
                return

            now = time.time()
            last_full_rerun = float(st.session_state.get(state_key, 0.0) or 0.0)
            if now - last_full_rerun < max(float(interval_seconds) * 0.6, 1.0):
                return

            st.session_state[state_key] = now
            st.session_state["_live_update_pulse"] = int(st.session_state.get("_live_update_pulse", 0) or 0) + 1
            st.rerun()

        _live_update_fragment()
        return

    interval_ms = int(interval_seconds * 1000)
    pulse = int(st.session_state.get("_live_update_pulse", 0) or 0) + 1
    st.session_state["_live_update_pulse"] = pulse

    html_payload = f"""
        <script>
        (function () {{
            try {{
                const root = window.parent || window;
                const timerKey = "__mrw_live_update_timer";
                if (root[timerKey]) {{
                    clearTimeout(root[timerKey]);
                }}
                root[timerKey] = setTimeout(function () {{
                    try {{
                        const url = new URL(root.location.href);
                        url.searchParams.set("mrw_live_tick", String(Date.now()));
                        root.location.replace(url.toString());
                    }} catch (e) {{
                        try {{ root.location.reload(); }} catch (_e) {{}}
                    }}
                }}, {interval_ms});
            }} catch (e) {{}}
        }})();
        </script>
    """ + f"\n<div style=\"display:none\">live:{route_value}:{pulse}:{interval_ms}</div>\n"

    components.html(
        html_payload,
        height=1,
        width=1,
    )


def main() -> None:
    session = SessionManager()
    try:
        bootstrap_system(session)
    except Exception as exc:
        st.error(f"Falha na inicializacao do sistema: {exc}")
        return

    runtime_mode = resolve_runtime_mode()
    try:
        client = connect_runtime_client(runtime_mode)
    except Exception as exc:
        st.error(f"Falha ao conectar no banco de producao: {exc}")
        st.stop()
    st.session_state["_supabase_client"] = client

    if runtime_mode == "DEV" or getattr(client, "is_local_runtime", False):
        st.warning("MODO DEV ATIVO")

    if not render_login(session, client):
        st.session_state["route"] = "login"
        st.stop()

    sync_authenticated_profile(session, client)
    access = get_access_profile(client=client)
    flags = get_feature_flags()
    if not flags.enable_dev_env and is_dev_mode():
        st.session_state["dev_mode"] = False
    ensure_dev_mode_access(bool(access.get("is_admin")))
    paid_allowed = can_access_paid_features(client=client)
    cadastro_allowed = can_access_cadastro(client=client)
    current_route_before = _read_route_state(session)
    current_route = current_route_before

    if not access.get("authenticated"):
        st.session_state["route"] = "login"
    else:
        if cadastro_allowed:
            if current_route in {"", "login"}:
                _set_route_state(session, "cadastro")
        else:
            if current_route in {"", "login", "cadastro", "edit", "diagnostico", "detalhe", "admin"}:
                _set_route_state(session, "consulta")

    current_route_after = _read_route_state(session)
    _debug_access_state(access, current_route_before, current_route_after)

    if not access.get("authenticated"):
        st.stop()

    route = st.session_state.get("route", "login")
    if access.get("authenticated") and (not cadastro_allowed) and route == "cadastro":
        _set_route_state(session, "consulta")
        st.rerun()

    if access.get("authenticated") and (not access.get("is_admin")) and route == "edit":
        _set_route_state(session, "consulta")
        st.rerun()

    if access.get("authenticated") and (not access.get("is_admin")) and route == "admin":
        _set_route_state(session, "consulta")
        st.rerun()

    if access.get("authenticated") and (not paid_allowed) and route in ("diagnostico", "detalhe"):
        _set_route_state(session, "consulta")
        st.rerun()

    render_dev_banner_if_needed(flags)

    router = build_router()
    render_navigation_sidebar(session, client)

    ctx = AppContext(supabase=client, session=session, router=router)
    router.dispatch(ctx, session.get_route())
    _render_scroll_reset_if_needed()
    _render_live_update_if_needed(flags=flags, access=access, route=session.get_route().value)


if __name__ == "__main__":
    main()
