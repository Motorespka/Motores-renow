from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Dict

import streamlit as st


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
        intents = [
            ("Cadastro", Route.CADASTRO),
            ("Consulta", Route.CONSULTA),
            ("Diagnostico", Route.DIAGNOSTICO),
        ]
        for label, route in intents:
            if st.button(label, use_container_width=True, key=f"nav_{route.value}"):
                session.set_route(route)

        st.divider()
        st.caption(f"Rota atual: {session.get_route().value}")
        if st.button("Logout", use_container_width=True, key="nav_logout"):
            session.logout()
            st.rerun()
