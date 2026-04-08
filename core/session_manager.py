from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

import streamlit as st

from core.navigation import Route


@dataclass
class SessionManager:
    auth_key: str = "auth_is_authenticated"
    route_key: str = "pagina"
    legacy_route_key: str = "nav_current_route"
    selected_motor_key: str = "nav_selected_motor_id"

    def bootstrap(self) -> None:
        if self.auth_key not in st.session_state:
            st.session_state[self.auth_key] = False
        if self.route_key not in st.session_state:
            legacy_value = st.session_state.get(self.legacy_route_key)
            st.session_state[self.route_key] = legacy_value or Route.CADASTRO.value
        st.session_state[self.legacy_route_key] = st.session_state[self.route_key]
        if self.selected_motor_key not in st.session_state:
            st.session_state[self.selected_motor_key] = None

    @property
    def is_authenticated(self) -> bool:
        return bool(st.session_state.get(self.auth_key, False))

    def login(self) -> None:
        st.session_state[self.auth_key] = True

    def logout(self) -> None:
        st.session_state[self.auth_key] = False
        st.session_state[self.route_key] = Route.CADASTRO.value
        st.session_state[self.legacy_route_key] = Route.CADASTRO.value
        st.session_state[self.selected_motor_key] = None

    def set_route(self, route: Route) -> None:
        st.session_state[self.route_key] = route.value
        st.session_state[self.legacy_route_key] = route.value

    def get_route(self) -> Route:
        value = st.session_state.get(self.route_key, Route.CADASTRO.value)
        try:
            route = Route(value)
        except ValueError:
            route = Route.CADASTRO
        st.session_state[self.route_key] = route.value
        st.session_state[self.legacy_route_key] = route.value
        return route

    @property
    def selected_motor_id(self) -> Optional[Any]:
        value = st.session_state.get(self.selected_motor_key)
        if value in (None, ""):
            return None
        return value

    @selected_motor_id.setter
    def selected_motor_id(self, value: Optional[Any]) -> None:
        st.session_state[self.selected_motor_key] = value
