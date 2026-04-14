from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st

from core.access_control import (
    DEFAULT_PLAN,
    PAID_PLANS,
    describe_access_tier,
    get_access_profile,
    get_usuario_for_admin,
    grant_cadastro_access_for_user,
    list_cadastro_allowed_users,
    require_admin_access,
    resolve_access_tier,
    revoke_cadastro_access_for_user,
    search_usuarios_for_cadastro_access,
    update_usuario_for_admin,
)
from core.navigation import Route

SECTIONS = {
    "General": "general",
    "Usuarios": "users",
    "Permissao Cadastro": "cadastro_permissions",
    "Matriz de Acesso": "access_matrix",
}

ROLE_OPTIONS = ["user", "admin"]
PLAN_OPTIONS = [DEFAULT_PLAN] + sorted(PAID_PLANS)


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    txt = _to_text(value).lower()
    return txt in {"1", "true", "yes", "sim"}


def _query_users_snapshot(client) -> List[Dict[str, Any]]:
    if getattr(client, "is_local_runtime", False):
        return []
    try:
        res = (
            client
            .table("usuarios_app")
            .select("id,role,plan,ativo")
            .order("created_at", desc=True)
            .limit(2000)
            .execute()
        )
        rows = getattr(res, "data", None) or []
        return rows if isinstance(rows, list) else []
    except Exception:
        return []


def _render_header() -> None:
    st.markdown(
        """
        <div class="admin-hero">
            <div class="admin-hero__tag">ADMIN SETTINGS</div>
            <h1>Painel Administrativo</h1>
            <p>Configure acessos, planos e permissoes da plataforma em um unico lugar.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_general(client) -> None:
    access = get_access_profile(client=client)
    tier = resolve_access_tier(client=client)
    rows = _query_users_snapshot(client)
    manual_cadastro = list_cadastro_allowed_users(client=client)

    total_users = len(rows)
    total_paid = sum(1 for r in rows if _to_text(r.get("plan")).lower() in PAID_PLANS)
    total_admin = sum(1 for r in rows if _to_text(r.get("role")).lower() == "admin" and _safe_bool(r.get("ativo")))
    total_active = sum(1 for r in rows if _safe_bool(r.get("ativo")))

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="dash-kpi"><span>Usuarios</span><strong>{total_users}</strong></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="dash-kpi"><span>Pagos</span><strong>{total_paid}</strong></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="dash-kpi"><span>Admins</span><strong>{total_admin}</strong></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="dash-kpi"><span>Ativos</span><strong>{total_active}</strong></div>', unsafe_allow_html=True)

    st.markdown("### Seu contexto")
    st.caption(f"Plano atual: {_to_text(access.get('plan')).lower() or DEFAULT_PLAN}")
    st.caption(f"Acesso atual: {describe_access_tier(tier)}")
    st.caption(f"Usuarios com liberacao manual de cadastro: {len(manual_cadastro)}")

    if not rows and not getattr(client, "is_local_runtime", False):
        st.info("Nao foi possivel carregar o resumo de usuarios. Verifique permissoes RLS para admin.")


def _resolve_selected_user(client) -> Dict[str, Any] | None:
    query = st.text_input(
        "Buscar usuario por username, nome ou email",
        key="admin_user_search",
        placeholder="Ex.: mickear",
    ).strip()
    if len(query) < 2:
        st.caption("Digite ao menos 2 caracteres para buscar.")
        return None

    matches = search_usuarios_for_cadastro_access(query, client=client, limit=50)
    if not matches:
        st.caption("Nenhum usuario encontrado.")
        return None

    options = [f"{m.get('label', '')} | id:{m.get('user_id', '')}" for m in matches]
    selected_label = st.selectbox("Resultados", options, key="admin_user_pick")
    selected = next((m for m in matches if f"{m.get('label', '')} | id:{m.get('user_id', '')}" == selected_label), None)
    if not selected:
        return None

    user_id = _to_text(selected.get("user_id"))
    if not user_id:
        return None
    return get_usuario_for_admin(user_id, client=client)


def _render_users(client) -> None:
    st.markdown("### Usuarios e planos")
    user = _resolve_selected_user(client)
    if not user:
        return

    user_id = _to_text(user.get("id"))
    st.markdown(
        f"""
        <div class="data-panel">
            <div class="data-label">Usuario selecionado</div>
            <div class="data-value">{_to_text(user.get('email')) or user_id}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form(f"admin_user_form_{user_id}"):
        c1, c2 = st.columns(2)
        with c1:
            username = st.text_input("Username", value=_to_text(user.get("username")))
            nome = st.text_input("Nome", value=_to_text(user.get("nome")))
            ativo = st.toggle("Conta ativa", value=_safe_bool(user.get("ativo")))
        with c2:
            role_default = _to_text(user.get("role")).lower()
            if role_default not in ROLE_OPTIONS:
                role_default = "user"
            role = st.selectbox("Role", ROLE_OPTIONS, index=ROLE_OPTIONS.index(role_default))

            plan_default = _to_text(user.get("plan")).lower() or DEFAULT_PLAN
            if plan_default not in PLAN_OPTIONS:
                plan_default = DEFAULT_PLAN
            plan = st.selectbox("Plano", PLAN_OPTIONS, index=PLAN_OPTIONS.index(plan_default))

        submitted = st.form_submit_button("Salvar alteracoes", use_container_width=True)
        if submitted:
            ok, message = update_usuario_for_admin(
                user_id,
                username=username,
                nome=nome,
                role=role,
                plan=plan,
                ativo=ativo,
                client=client,
            )
            if ok:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

    q1, q2 = st.columns(2)
    with q1:
        if st.button("Definir plano pago", key=f"admin_paid_{user_id}", use_container_width=True):
            ok, message = update_usuario_for_admin(
                user_id,
                username=_to_text(user.get("username")),
                nome=_to_text(user.get("nome")),
                role=_to_text(user.get("role")).lower() or "user",
                plan="paid",
                ativo=True,
                client=client,
            )
            if ok:
                st.success("Plano atualizado para paid.")
                st.rerun()
            else:
                st.error(message)
    with q2:
        if st.button("Voltar para free", key=f"admin_free_{user_id}", use_container_width=True):
            ok, message = update_usuario_for_admin(
                user_id,
                username=_to_text(user.get("username")),
                nome=_to_text(user.get("nome")),
                role=_to_text(user.get("role")).lower() or "user",
                plan=DEFAULT_PLAN,
                ativo=_safe_bool(user.get("ativo")),
                client=client,
            )
            if ok:
                st.success("Plano atualizado para free.")
                st.rerun()
            else:
                st.error(message)


def _render_cadastro_permissions(client) -> None:
    st.markdown("### Permissao de cadastro (manual)")
    st.caption("Use esta liberacao para casos especificos. Usuario pago e admin ja acessam cadastro automaticamente.")

    query = st.text_input(
        "Buscar para liberar cadastro",
        key="admin_cadastro_search",
        placeholder="username, nome ou email",
    ).strip()
    selected_user_id = ""
    matches = search_usuarios_for_cadastro_access(query, client=client, limit=50) if len(query) >= 2 else []
    if len(query) >= 2 and not matches:
        st.caption("Nenhum usuario encontrado.")
    if matches:
        options = [f"{m.get('label', '')} | id:{m.get('user_id', '')}" for m in matches]
        selected_label = st.selectbox("Resultados", options, key="admin_cadastro_pick")
        selected = next((m for m in matches if f"{m.get('label', '')} | id:{m.get('user_id', '')}" == selected_label), None)
        selected_user_id = _to_text((selected or {}).get("user_id"))

    if st.button("Adicionar permissao de cadastro", use_container_width=True, key="admin_cadastro_add"):
        ok, message = grant_cadastro_access_for_user(selected_user_id, client=client)
        if ok:
            st.success(message)
            st.rerun()
        else:
            st.error(message)

    st.markdown("### Usuarios liberados")
    allowed_users = list_cadastro_allowed_users(client=client)
    if not allowed_users:
        st.caption("Nenhum usuario liberado manualmente.")
        return

    for row in allowed_users:
        uid = _to_text(row.get("user_id"))
        label = _to_text(row.get("label")) or uid
        c1, c2 = st.columns([3, 1])
        with c1:
            st.caption(label)
        with c2:
            if st.button("Remover", key=f"admin_cadastro_rm_{uid}", use_container_width=True):
                ok, message = revoke_cadastro_access_for_user(uid, client=client)
                if ok:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)


def _render_access_matrix() -> None:
    st.markdown("### Matriz de acesso")
    st.markdown(
        """
| Nivel | Consulta | Cadastro | Diagnostico | Editar Motor | Gerir Usuarios |
|---|---|---|---|---|---|
| Free (teaser) | Parcial | Nao | Nao | Nao | Nao |
| Free + cadastro liberado | Parcial | Sim | Nao | Nao | Nao |
| Pago | Completa | Sim | Sim | Nao | Nao |
| Admin | Completa | Sim | Sim | Sim | Sim |
        """
    )
    st.info("Recomendacao comercial: Free para atracao, Paid para operacao tecnica completa, Admin somente para voce.")


def render(ctx) -> None:
    if not require_admin_access("Painel administrativo", client=ctx.supabase):
        if st.button("Voltar para consulta", use_container_width=True):
            ctx.session.set_route(Route.CONSULTA)
            st.rerun()
        return

    _render_header()

    left, right = st.columns([1.15, 3.25], gap="large")
    with left:
        st.markdown("### Configuracoes")
        labels = list(SECTIONS.keys())
        current = st.session_state.get("admin_panel_section_label", "General")
        if current not in labels:
            current = "General"
        section_label = st.radio(
            "Menu admin",
            labels,
            index=labels.index(current),
            key="admin_panel_section_menu",
            label_visibility="collapsed",
        )
        st.session_state["admin_panel_section_label"] = section_label

    with right:
        section = SECTIONS.get(st.session_state.get("admin_panel_section_label", "General"), "general")
        if section == "general":
            _render_general(ctx.supabase)
        elif section == "users":
            _render_users(ctx.supabase)
        elif section == "cadastro_permissions":
            _render_cadastro_permissions(ctx.supabase)
        else:
            _render_access_matrix()


def show(ctx) -> None:
    return render(ctx)
