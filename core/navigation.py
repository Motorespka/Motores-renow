from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Dict

import streamlit as st

from core.access_control import is_admin_user

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


def render_navigation_sidebar(session) -> None:
    with st.sidebar:
        st.markdown("## Moto-Renow")
        admin_user = is_admin_user()
        intents = [
            ("Cadastro (Admin)", Route.CADASTRO, True),
            ("Consulta", Route.CONSULTA),
            ("Diagnostico", Route.DIAGNOSTICO),
        ]
        for item in intents:
            if len(item) == 3:
                label, route, admin_only = item
            else:
                label, route = item
                admin_only = False
            locked = admin_only and not admin_user
            if st.button(label, use_container_width=True, key=f"nav_{route.value}", disabled=locked):
                session.set_route(route)

        st.divider()
        if not admin_user:
            st.caption("Conta sem permissao de admin para cadastro/edicao.")
        st.caption(f"Rota atual: {session.get_route().value}")
        if st.button("Logout", use_container_width=True, key="nav_logout"):
            session.logout()
            st.rerun()
