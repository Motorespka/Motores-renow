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
    is_admin_user,
    resolve_access_tier,
)
from core.user_identity import resolve_current_user_identity

class Route(str, Enum):
    CADASTRO = "cadastro"
    CONSULTA = "consulta"
    ATUALIZACOES = "atualizacoes"
    DETALHE = "detalhe"
    EDIT = "edit"
    DIAGNOSTICO = "diagnostico"
    ADMIN = "admin"


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
        "_runtime_client",
        "_runtime_client_mode",
        "_supabase_client",
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
        st.query_params.pop("mrw_auth", None)
    except Exception:
        try:
            q = st.experimental_get_query_params()
            q.pop("auth", None)
            q.pop("mrw_auth", None)
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
        intents.append(("Atualizacoes", Route.ATUALIZACOES))
        if paid_allowed:
            intents.append(("Diagnostico", Route.DIAGNOSTICO))
        if admin_user:
            intents.append(("Admin", Route.ADMIN))
        for item in intents:
            label, route = item
            if st.button(label, use_container_width=True, key=f"nav_{route.value}"):
                session.set_route(route)
                st.rerun()

        st.divider()
        st.caption(f"Rota atual: {session.get_route().value}")
        if st.button("Logout", use_container_width=True, key="nav_logout"):
            _perform_logout(session, supabase_client=supabase_client)
