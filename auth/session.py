import streamlit as st


class SessionManager:
    def __init__(self):
        pass

    def bootstrap(self) -> None:
        st.session_state.setdefault("is_authenticated", False)
        st.session_state.setdefault("route", "consulta")
        st.session_state.setdefault("auth_force_logged_out", False)
        st.session_state.setdefault("_post_login_route_applied", False)

    @property
    def is_authenticated(self) -> bool:
        return bool(st.session_state.get("is_authenticated", False))

    def login(self) -> None:
        st.session_state["is_authenticated"] = True
        st.session_state["auth_force_logged_out"] = False

    def logout(self) -> None:
        st.session_state["is_authenticated"] = False
        st.session_state["auth_force_logged_out"] = True

        keys_to_clear = [
            "auth_user_id",
            "auth_user_email",
            "auth_user_profile",
            "_access_cache_key",
            "_access_cache_value",
            "_admin_cache_key",
            "_admin_cache_value",
            "_access_profile",
            "_paid_allowed",
            "_cadastro_allowed",
            "_perfil_debug",
            "_post_login_route_applied",
        ]

        for key in keys_to_clear:
            st.session_state.pop(key, None)

        st.session_state["route"] = "consulta"

        try:
            st.query_params.pop("auth", None)
        except Exception:
            try:
                q = st.experimental_get_query_params()
                q.pop("auth", None)
                st.experimental_set_query_params(**q)
            except Exception:
                pass

    def get_route(self):
        return st.session_state.get("route", "consulta")

    def set_route(self, route) -> None:
        st.session_state["route"] = route
