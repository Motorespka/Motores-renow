from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Dict

import streamlit as st

from core.access_control import (
    can_access_cadastro,
    get_cadastro_open_setting,
    is_admin_user,
    set_cadastro_open_setting,
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
        admin_user = is_admin_user()
        cadastro_allowed = can_access_cadastro(supabase_client)
        intents = []
        if cadastro_allowed:
            intents.append(("Cadastro", Route.CADASTRO))
        intents.extend(
            [
                ("Consulta", Route.CONSULTA),
                ("Diagnostico", Route.DIAGNOSTICO),
            ]
        )
        for item in intents:
            label, route = item
            if st.button(label, use_container_width=True, key=f"nav_{route.value}"):
                session.set_route(route)

        if admin_user:
            st.divider()
            with st.expander("Permissao de Cadastro", expanded=False):
                current_open = get_cadastro_open_setting(supabase_client)
                desired_open = st.toggle(
                    "Liberar cadastro para todos os usuarios logados",
                    value=current_open,
                    key="nav_cadastro_open_toggle",
                )
                if st.button("Salvar permissao", use_container_width=True, key="nav_cadastro_open_save"):
                    ok, message = set_cadastro_open_setting(desired_open, client=supabase_client)
                    if ok:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                st.caption("Quando ligado, qualquer usuario autenticado pode abrir e usar a aba Cadastro.")

        st.divider()
        st.caption(f"Rota atual: {session.get_route().value}")
        if st.button("Logout", use_container_width=True, key="nav_logout"):
            _perform_logout(session, supabase_client=supabase_client)
