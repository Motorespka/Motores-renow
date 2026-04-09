from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Dict

import streamlit as st

from core.access_control import (
    can_access_cadastro,
    can_access_paid_features,
    describe_access_tier,
    get_access_profile,
    grant_cadastro_access_for_user,
    is_admin_user,
    list_cadastro_allowed_users,
    resolve_access_tier,
    revoke_cadastro_access_for_user,
    search_usuarios_for_cadastro_access,
)
from core.user_identity import resolve_current_user_identity

class Route(str, Enum):
    CADASTRO = "cadastro"
    CONSULTA = "consulta"
    DETALHE = "detalhe"
    EDIT = "edit"
    DIAGNOSTICO = "diagnostico"


@dataclass
class AppContext:
    supabase: object
    session: object
    router: "Router"


class Router:
    def __init__(self) -> None:
        self._handlers: Dict[Route, Callable[[AppContext], None]] = {}

    def register(self, route: Route, handler: Callable[[AppContext], None]) -> None:
        self._handlers[route] = handler

    def dispatch(self, ctx: AppContext, route: Route) -> None:
        if route not in self._handlers:
            raise RuntimeError(f"Rota nao registrada: {route.value}")
        self._handlers[route](ctx)


def _perform_logout(session, supabase_client=None) -> None:
    # Evita restaurar login automaticamente na proxima execucao.
    st.session_state["auth_force_logged_out"] = True

    try:
        if supabase_client is not None and not getattr(supabase_client, "is_local_runtime", False):
            supabase_client.auth.sign_out()
    except Exception:
        pass

    for key in [
        "auth_user_id",
        "auth_user_email",
        "auth_user_profile",
        "route",
        "_access_cache_key",
        "_access_cache_value",
        "_admin_cache_key",
        "_admin_cache_value",
        "_post_login_route_applied",
        "logado",
        "expira_em",
    ]:
        st.session_state.pop(key, None)

    # Compatibilidade com sessao legada baseada em query param.
    try:
        st.query_params.pop("auth", None)
    except Exception:
        try:
            q = st.experimental_get_query_params()
            q.pop("auth", None)
            st.experimental_set_query_params(**q)
        except Exception:
            pass

    session.logout()
    st.rerun()


def render_navigation_sidebar(session, supabase_client=None) -> None:
    with st.sidebar:
        st.markdown("## Moto-Renow")
        identity = resolve_current_user_identity()
        st.caption(f"Logado como: {identity.get('display_name', 'Usuario')}")
        access = get_access_profile(client=supabase_client)
        admin_user = is_admin_user()
        paid_allowed = can_access_paid_features(supabase_client)
        cadastro_allowed = can_access_cadastro(supabase_client)
        tier = resolve_access_tier(client=supabase_client)
        plan_label = str(access.get("plan") or "free").strip().lower() or "free"
        st.caption(f"Plano: {plan_label} | Acesso: {describe_access_tier(tier)}")
        if tier == "teaser":
            st.caption("Modo teaser ativo: solicite ao admin para liberar plano pago.")
        intents = []
        if cadastro_allowed:
            intents.append(("Cadastro", Route.CADASTRO))
        intents.append(("Consulta", Route.CONSULTA))
        if paid_allowed:
            intents.append(("Diagnostico", Route.DIAGNOSTICO))
        for item in intents:
            label, route = item
            if st.button(label, use_container_width=True, key=f"nav_{route.value}"):
                session.set_route(route)

        if admin_user:
            st.divider()
            with st.expander("Permissao de Cadastro", expanded=False):
                st.markdown("### Liberar por usuario")
                user_query = st.text_input(
                    "Buscar por username, nome ou email",
                    key="nav_cadastro_user_query",
                    placeholder="Ex.: mickear",
                ).strip()
                matches = search_usuarios_for_cadastro_access(user_query, client=supabase_client) if len(user_query) >= 2 else []
                if len(user_query) >= 2 and not matches:
                    st.caption("Nenhum usuario encontrado.")
                selected_user_id = ""
                if matches:
                    options = [f"{m.get('label', '')} | id:{m.get('user_id', '')}" for m in matches]
                    selected_label = st.selectbox("Resultados", options, key="nav_cadastro_user_pick")
                    selected = next((m for m in matches if f"{m.get('label', '')} | id:{m.get('user_id', '')}" == selected_label), None)
                    selected_user_id = str((selected or {}).get("user_id") or "")

                if st.button("Adicionar usuario", use_container_width=True, key="nav_cadastro_user_add"):
                    ok, message = grant_cadastro_access_for_user(selected_user_id, client=supabase_client)
                    if ok:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

                st.markdown("### Usuarios com acesso")
                allowed_users = list_cadastro_allowed_users(client=supabase_client)
                if not allowed_users:
                    st.caption("Nenhum usuario liberado manualmente.")
                for row in allowed_users:
                    uid = str(row.get("user_id") or "")
                    label = str(row.get("label") or uid)
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.caption(label)
                    with c2:
                        if st.button("Remover", key=f"nav_cadastro_rm_{uid}", use_container_width=True):
                            ok, message = revoke_cadastro_access_for_user(uid, client=supabase_client)
                            if ok:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)

        st.divider()
        st.caption(f"Rota atual: {session.get_route().value}")
        if st.button("Logout", use_container_width=True, key="nav_logout"):
            _perform_logout(session, supabase_client=supabase_client)
