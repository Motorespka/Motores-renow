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
from core.development_mode import is_dev_mode
from core.feature_flags import get_feature_flags
from core.user_identity import resolve_current_user_identity

class Route(str, Enum):
    CADASTRO = "cadastro"
    CONSULTA = "consulta"
    ATUALIZACOES = "atualizacoes"
    DETALHE = "detalhe"
    EDIT = "edit"
    DIAGNOSTICO = "diagnostico"
    ADMIN = "admin"
    HUB_COMERCIAL = "hub_comercial"


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
        st.markdown(
            """
            <div class="mrw-sidebar-brand">
              <div class="mrw-sidebar-mark">
                <div class="mrw-sidebar-mark__inner">MR</div>
                <div class="mrw-sidebar-mark__dot"></div>
              </div>
              <div class="mrw-sidebar-brand__text">
                <div class="mrw-sidebar-brand__title">MOTO-RENOW</div>
                <div class="mrw-sidebar-brand__subtitle">TECHNICAL PLATFORM</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        identity = resolve_current_user_identity()
        st.markdown(
            f"""
            <div class="mrw-sidebar-workspace">
              <div class="mrw-sidebar-workspace__row">
                <span class="mrw-kicker">WORKSPACE</span>
                <span class="mrw-status"><span class="mrw-status__dot"></span>ONLINE</span>
              </div>
              <div class="mrw-sidebar-workspace__user">
                <div class="mrw-sidebar-workspace__avatar">{(identity.get("display_name","U") or "U")[:1].upper()}</div>
                <div class="mrw-sidebar-workspace__meta">
                  <div class="mrw-sidebar-workspace__name">{identity.get("display_name", "Usuario")}</div>
                  <div class="mrw-sidebar-workspace__hint">Sessão autenticada</div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        access = get_access_profile(client=supabase_client)
        admin_user = is_admin_user()
        paid_allowed = can_access_paid_features(supabase_client)
        cadastro_allowed = can_access_cadastro(supabase_client)
        tier = resolve_access_tier(client=supabase_client)
        plan_label = str(access.get("plan") or "free").strip().lower() or "free"
        st.caption(f"Plano: {plan_label} | Acesso: {describe_access_tier(tier)}")
        flags = get_feature_flags()
        dev_mode = is_dev_mode()
        if dev_mode:
            st.caption("Development: ON")
        if tier == "teaser":
            st.caption("Modo teaser ativo: solicite ao admin para liberar plano pago.")
        def _group(label: str) -> None:
            st.markdown(f'<div class="mrw-nav-group">{label}</div>', unsafe_allow_html=True)

        def _nav_button(
            label: str,
            route: Route,
            *,
            badge: str = "",
            badge_kind: str = "primary",
        ) -> None:
            if st.button(label, use_container_width=True, key=f"nav_{route.value}"):
                session.set_route(route)
                st.rerun()
            if badge:
                st.markdown(
                    f'<div class="mrw-nav-badge-row"><span class="mrw-badge mrw-badge--{badge_kind}">{badge}</span></div>',
                    unsafe_allow_html=True,
                )

        _group("OPERAÇÃO")
        if cadastro_allowed:
            _nav_button("Cadastro / OCR", Route.CADASTRO, badge="OCR", badge_kind="primary")
        _nav_button("Consulta Técnica", Route.CONSULTA, badge="BASE", badge_kind="accent")
        _nav_button("Atualizações", Route.ATUALIZACOES, badge="NEW", badge_kind="accent")

        _group("ANÁLISE TÉCNICA")
        if paid_allowed:
            _nav_button("Diagnóstico", Route.DIAGNOSTICO, badge="PRO", badge_kind="warning")

        if flags.any_marketplace_enabled() or dev_mode:
            _group("ECOSSISTEMA")
            _nav_button("Hub Comercial", Route.HUB_COMERCIAL)

        if admin_user:
            _group("SISTEMA")
            _nav_button("Administração", Route.ADMIN, badge="ADMIN", badge_kind="destructive")

        st.divider()
        st.caption(f"Rota atual: {session.get_route().value}")
        if st.button("Logout", use_container_width=True, key="nav_logout"):
            _perform_logout(session, supabase_client=supabase_client)


def render_route_header(route: Route) -> None:
    route_value = str(getattr(route, "value", route) or "").strip().lower()
    titles: dict[str, tuple[str, str, str, str]] = {
        Route.CONSULTA.value: ("CONSULTA TÉCNICA", "Base de motores cadastrados", "BASE", "accent"),
        Route.CADASTRO.value: ("CADASTRO / OCR", "Leitura de plaqueta e revisão assistida", "OCR", "primary"),
        Route.DIAGNOSTICO.value: ("DIAGNÓSTICO TÉCNICO", "Análise assistida de condição", "PRO", "warning"),
        Route.ADMIN.value: ("ADMINISTRAÇÃO", "Controle do workspace", "ADMIN", "destructive"),
        Route.ATUALIZACOES.value: ("ATUALIZAÇÕES", "Notas de versão e mudanças do sistema", "NEW", "accent"),
        Route.DETALHE.value: ("DETALHE DO MOTOR", "Visualização técnica e histórico", "MOTOR", "primary"),
        Route.EDIT.value: ("EDIÇÃO", "Ajustes e correções do cadastro", "EDIT", "warning"),
        Route.HUB_COMERCIAL.value: ("HUB COMERCIAL", "Integrações e marketplace", "HUB", "accent"),
    }
    title, subtitle, tag, tag_kind = titles.get(route_value, ("MOTO-RENOW", "Plataforma técnica", "", "primary"))
    tag_html = (
        f'<span class="mrw-hero-tag mrw-hero-tag--{tag_kind}">{tag}</span>'
        if tag
        else ""
    )

    st.markdown(
        f"""
        <div class="mrw-header">
          <div class="mrw-header__topline"></div>
          <div class="mrw-header__left">
            <div class="mrw-header__marker">
              <div class="mrw-header__marker-core"></div>
            </div>
            <div class="mrw-header__titles">
              <div class="mrw-header__title">{title} {tag_html}</div>
              <div class="mrw-header__subtitle">{subtitle}</div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Busca global opcional (não interfere na lógica das páginas).
    cols = st.columns([2, 1])
    with cols[0]:
        st.markdown('<div class="mrw-global-search-anchor"></div>', unsafe_allow_html=True)
        st.text_input(
            "Buscar",
            placeholder="Buscar motor, série, fabricante, laudo...",
            key="_global_search",
            label_visibility="collapsed",
        )
    with cols[1]:
        st.markdown(
            '<div class="mrw-header__hint">Dica: use a busca como filtro manual nas telas</div>',
            unsafe_allow_html=True,
        )
