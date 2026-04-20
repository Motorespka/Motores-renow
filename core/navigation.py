from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict

import json
from pathlib import Path

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

MRW_SEARCH_HIST_KEY = "mrw_global_search_history"
MRW_SEARCH_HIST_MAX = 40


def _append_mrw_search_hist(term: str) -> None:
    t = str(term or "").strip()
    if not t:
        return
    prev = list(st.session_state.get(MRW_SEARCH_HIST_KEY) or [])
    prev = [x for x in prev if str(x).lower() != t.lower()]
    prev.insert(0, t)
    st.session_state[MRW_SEARCH_HIST_KEY] = prev[:MRW_SEARCH_HIST_MAX]


def _releases_head_caption() -> str:
    rel = Path(__file__).resolve().parent.parent / "data" / "releases.json"
    if not rel.is_file():
        return ""
    try:
        ch = json.loads(rel.read_text(encoding="utf-8")).get("changelog") or []
        head = ch[0] if ch else {}
        ver = str(head.get("versao") or "").strip()
        dt = str(head.get("data") or "").strip()
        if not ver:
            return ""
        return f"Versao do sistema (releases): **{ver}**" + (f" · {dt}" if dt else "")
    except Exception:
        return ""


def _render_external_links() -> None:
    """Reservado: conteúdo comercial e ajuda passaram para a rota **Sobre a plataforma** (sem Next.js nem FastAPI)."""
    return

class Route(str, Enum):
    DASHBOARD = "dashboard"
    CADASTRO = "cadastro"
    CONSULTA = "consulta"
    GUIA_OFICINA = "guia_oficina"
    FERRAMENTAS_BOBINAGEM = "ferramentas_bobinagem"
    ATUALIZACOES = "atualizacoes"
    DETALHE = "detalhe"
    EDIT = "edit"
    DIAGNOSTICO = "diagnostico"
    BIBLIOTECA_CALCULOS = "biblioteca_calculos"
    ORDENS_SERVICO = "ordens_servico"
    ADMIN = "admin"
    HUB_COMERCIAL = "hub_comercial"
    SITE_MOTO_RENOW = "site_moto_renow"


class Router:
    """Router definido antes de AppContext para evitar forward-ref no @dataclass (Cloud/import)."""

    def __init__(self) -> None:
        self._handlers: Dict[Route, Callable[..., None]] = {}

    def register(self, route: Route, handler: Callable[..., None]) -> None:
        self._handlers[route] = handler

    def dispatch(self, ctx: "AppContext", route: Route) -> None:
        if route not in self._handlers:
            raise RuntimeError(f"Rota nao registrada: {route.value}")
        self._handlers[route](ctx)


@dataclass
class AppContext:
    supabase: object
    session: object
    router: Router


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

        _render_external_links()
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
        current_route = session.get_route()

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
            badge_html = []
            if badge:
                badge_html.append(f'<span class="mrw-badge mrw-badge--{badge_kind}">{badge}</span>')
            if current_route == route:
                badge_html.append('<span class="mrw-badge mrw-badge--active">ATUAL</span>')
            if badge_html:
                st.markdown(
                    f'<div class="mrw-nav-badge-row">{"".join(badge_html)}</div>',
                    unsafe_allow_html=True,
                )

        _group("SITE")
        _nav_button("Sobre a plataforma", Route.SITE_MOTO_RENOW, badge="INFO", badge_kind="accent")

        _group("OPERAÇÃO")
        _nav_button("Consulta", Route.CONSULTA, badge="BASE", badge_kind="accent")
        _nav_button("Guia oficina", Route.GUIA_OFICINA, badge="AJUDA", badge_kind="accent")
        _nav_button("Ferramentas bobinagem", Route.FERRAMENTAS_BOBINAGEM, badge="OFIC", badge_kind="accent")
        _nav_button("Visão geral", Route.DASHBOARD)
        _nav_button("Atualizações", Route.ATUALIZACOES, badge="NEW", badge_kind="accent")
        if cadastro_allowed:
            _nav_button("Cadastro / OCR", Route.CADASTRO, badge="OCR", badge_kind="primary")

        _group("ANÁLISE TÉCNICA")
        if paid_allowed:
            _nav_button("Diagnóstico", Route.DIAGNOSTICO, badge="PRO", badge_kind="warning")
            _nav_button("Biblioteca de cálculos", Route.BIBLIOTECA_CALCULOS, badge="PRO", badge_kind="warning")
            _nav_button("Ordens de serviço", Route.ORDENS_SERVICO, badge="PRO", badge_kind="warning")
            if st.button(
                "Minhas OS",
                use_container_width=True,
                key="nav_shortcut_os_mine",
                help="Abre Ordens de servico com o filtro So as minhas activo.",
            ):
                st.session_state["os_f_mine"] = True
                session.set_route(Route.ORDENS_SERVICO)
                st.rerun()

        if flags.any_marketplace_enabled() or dev_mode:
            _group("ECOSSISTEMA")
            _nav_button("Hub Comercial", Route.HUB_COMERCIAL)

        if admin_user:
            _group("SISTEMA")
            _nav_button("Administração", Route.ADMIN, badge="ADMIN", badge_kind="destructive")

        st.divider()
        st.caption(f"Rota atual: {current_route.value}")
        if admin_user:
            rel = Path(__file__).resolve().parent.parent / "data" / "releases.json"
            if rel.is_file():
                try:
                    ch = json.loads(rel.read_text(encoding="utf-8")).get("changelog") or []
                    head = ch[0] if ch else {}
                    ver = str(head.get("versao") or "?").strip() or "?"
                    data = str(head.get("data") or "").strip()
                    hint = f"Referencia: {ver}" + (f" ({data})" if data else "")
                    st.caption(hint)
                except Exception:
                    pass
        with st.expander("Teclado e ritmo (Streamlit)", expanded=False):
            st.markdown(
                """
- **Tab** / **Shift+Tab**: mover o foco entre campos e botoes.
- **Enter**: em **formularios**, envia quando o foco esta no botao de submissao.
- **Espaco**: marcar / desmarcar **checkbox**.
- A **busca global** no topo relanca a app como o resto dos controlos; o **historico** grava **automaticamente** a cada alteracao no texto (sessao).
- **Ctrl+S** do navegador **nao** grava na base — use o botao **Salvar** / **Guardar** de cada ecra.
                """.strip()
            )
        if st.button("Logout", use_container_width=True, key="nav_logout"):
            _perform_logout(session, supabase_client=supabase_client)


def _render_route_header_search() -> None:
    cols = st.columns([2, 1])
    with cols[0]:
        st.markdown('<div class="mrw-global-search-anchor"></div>', unsafe_allow_html=True)

        def _on_global_search_hist_push() -> None:
            _append_mrw_search_hist(str(st.session_state.get("_global_search") or ""))

        st.text_input(
            "Buscar",
            placeholder="Buscar motor, série, fabricante, laudo...",
            key="_global_search",
            label_visibility="collapsed",
            on_change=_on_global_search_hist_push,
        )
    with cols[1]:
        st.markdown(
            '<div class="mrw-header__hint">Historico de sessao (cada alteracao no texto)</div>',
            unsafe_allow_html=True,
        )
    if st.button("Limpar historico de busca", key="mrw_search_hist_clear"):
        st.session_state.pop(MRW_SEARCH_HIST_KEY, None)
        st.rerun()
    hist_list = list(st.session_state.get(MRW_SEARCH_HIST_KEY) or [])
    if hist_list:
        st.caption("Historico (sessao) — clique para repor o campo")
        nh = min(6, len(hist_list))
        hcols = st.columns(nh)
        for i, term in enumerate(hist_list[:6]):
            short = term if len(term) <= 22 else term[:19] + "…"
            tid = abs(hash(f"{term}|{i}")) % 1_000_000_000
            with hcols[i]:
                if st.button(short, key=f"mrw_hist_pick_{i}_{tid}", help="Repor Buscar com este termo"):
                    st.session_state["_global_search"] = term
                    st.rerun()


def render_route_header(route: Route, session: Any = None) -> None:
    route_value = str(getattr(route, "value", route) or "").strip().lower()
    titles: dict[str, tuple[str, str, str, str]] = {
        Route.DASHBOARD.value: ("VISÃO GERAL", "Painel operacional do workspace", "DASH", "accent"),
        Route.CONSULTA.value: ("CONSULTA TÉCNICA", "Base de motores cadastrados", "BASE", "accent"),
        Route.GUIA_OFICINA.value: (
            "GUIA DA OFICINA",
            "Fluxo biblioteca, OS, PDF e boas práticas",
            "AJUDA",
            "accent",
        ),
        Route.FERRAMENTAS_BOBINAGEM.value: (
            "FERRAMENTAS DE BOBINAGEM",
            "Equivalência de fio, espiras e tensão (bancada)",
            "OFIC",
            "accent",
        ),
        Route.CADASTRO.value: ("CADASTRO / OCR", "Leitura de plaqueta e revisão assistida", "OCR", "primary"),
        Route.DIAGNOSTICO.value: ("DIAGNÓSTICO TÉCNICO", "Análise assistida de condição", "PRO", "warning"),
        Route.BIBLIOTECA_CALCULOS.value: (
            "BIBLIOTECA DE CÁLCULOS",
            "Receitas de rebobinagem reutilizáveis e revisões",
            "PRO",
            "warning",
        ),
        Route.ORDENS_SERVICO.value: (
            "ORDENS DE SERVIÇO",
            "Fluxo oficina: recebe até entrega",
            "PRO",
            "warning",
        ),
        Route.ADMIN.value: ("ADMINISTRAÇÃO", "Controle do workspace", "ADMIN", "destructive"),
        Route.ATUALIZACOES.value: ("ATUALIZAÇÕES", "Notas de versão e mudanças do sistema", "NEW", "accent"),
        Route.DETALHE.value: ("DETALHE DO MOTOR", "Visualização técnica e histórico", "MOTOR", "primary"),
        Route.EDIT.value: ("EDIÇÃO", "Ajustes e correções do cadastro", "EDIT", "warning"),
        Route.HUB_COMERCIAL.value: ("HUB COMERCIAL", "Integrações e marketplace", "HUB", "accent"),
        Route.SITE_MOTO_RENOW.value: (
            "SOBRE A PLATAFORMA",
            "Informação para oficina — donos, técnicos e planos",
            "INFO",
            "accent",
        ),
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

    rel_cap = _releases_head_caption()
    if rel_cap:
        st.caption(rel_cap)

    if session is not None and route_value in (Route.DETALHE.value, Route.EDIT.value):
        b1, b2, b3 = st.columns([1.05, 1.05, 3.9])
        with b1:
            if st.button(
                "← Consulta",
                key="mrw_bc_consulta",
                help="Volta ao catalogo; filtros e busca da Consulta mantem-se na mesma sessao.",
            ):
                session.set_route(Route.CONSULTA)
                st.rerun()
        with b2:
            if st.button(
                "Ordens",
                key="mrw_bc_os",
                help="Abre Ordens de servico (plano PRO).",
            ):
                session.set_route(Route.ORDENS_SERVICO)
                st.rerun()
        with b3:
            st.caption(
                "Atalho de fluxo: use o campo **Buscar** abaixo para copiar texto para a Consulta manualmente."
            )

    # Busca global: fora de `st.fragment` para nao quebrar paginas seguintes (ex.: Consulta).
    _render_route_header_search()
