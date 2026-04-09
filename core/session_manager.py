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
    route_query_key: str = "route"

    def _read_route_from_query(self) -> Optional[str]:
        # Streamlit >= 1.30
        try:
            value = st.query_params.get(self.route_query_key)
            if isinstance(value, list):
                value = value[0] if value else None
            if isinstance(value, str) and value.strip():
                return value.strip()
        except Exception:
            pass

        # Fallback para APIs antigas
        try:
            q = st.experimental_get_query_params()
            values = q.get(self.route_query_key) or []
            if values:
                return str(values[0]).strip()
        except Exception:
            pass
        return None

    def _write_route_to_query(self, route_value: str) -> None:
        # Streamlit >= 1.30
        try:
            st.query_params[self.route_query_key] = route_value
            return
        except Exception:
            pass

        # Fallback para APIs antigas
        try:
            st.experimental_set_query_params(**{self.route_query_key: route_value})
        except Exception:
            pass

    def bootstrap(self) -> None:
        if self.auth_key not in st.session_state:
            st.session_state[self.auth_key] = False
        if self.route_key not in st.session_state:
            query_value = self._read_route_from_query()
            legacy_value = st.session_state.get(self.legacy_route_key)
            candidate = query_value or legacy_value or Route.CADASTRO.value
            try:
                st.session_state[self.route_key] = Route(candidate).value
            except Exception:
                st.session_state[self.route_key] = Route.CADASTRO.value
        st.session_state[self.legacy_route_key] = st.session_state[self.route_key]
        self._write_route_to_query(st.session_state[self.route_key])
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
        self._write_route_to_query(Route.CADASTRO.value)
        st.session_state[self.selected_motor_key] = None

    def set_route(self, route: Route) -> None:
        st.session_state[self.route_key] = route.value
        st.session_state[self.legacy_route_key] = route.value
        self._write_route_to_query(route.value)

    def get_route(self) -> Route:
        value = st.session_state.get(self.route_key, Route.CADASTRO.value)
        try:
            route = Route(value)
        except ValueError:
            route = Route.CADASTRO
        st.session_state[self.route_key] = route.value
        st.session_state[self.legacy_route_key] = route.value
        self._write_route_to_query(route.value)
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
