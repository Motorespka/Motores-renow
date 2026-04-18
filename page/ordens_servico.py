from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st

from core.access_control import require_paid_access
from services.oficina_workshop import (
    OS_ETAPAS,
    append_os_event,
    get_calculo,
    get_ordem_servico,
    insert_ordem_servico,
    link_os_to_calculo,
    list_calculos,
    list_ordens_servico,
    workshop_tables_available,
)


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _fmt_calc_option(r: Dict[str, Any]) -> str:
    return f"{r.get('id')} — {r.get('titulo', '')}"


def render(ctx) -> None:
    if not require_paid_access("Ordens de servico", client=ctx.supabase):
        return

    st.markdown("### Ordens de servico (oficina)")
    st.caption(
        "Acompanhe o fluxo: recebe → busca/cria calculo → limpeza → rebobina → impregna → montagem → teste → pecas → entrega. "
        "Cada mudanca de etapa fica registrada na linha do tempo da OS."
    )

    if not workshop_tables_available(ctx.supabase):
        st.error(
            "Tabelas indisponiveis. No Supabase, rode `backend/migrations/20260418_0044_rebobinagem_calculos_oficina_os.sql`. "
            "Em DEV local, reinicie para criar SQLite."
        )
        return

    uid = _to_text(st.session_state.get("auth_user_id") or st.session_state.get("auth_user_email"))

    calcs = list_calculos(ctx.supabase, q="", limit=60)
    calc_labels = [""] + [_fmt_calc_option(c) for c in calcs if c.get("id")]
    calc_map = {_fmt_calc_option(c): str(c.get("id")) for c in calcs if c.get("id")}

    st.markdown("#### Nova OS")
    with st.form("os_nova"):
        titulo = st.text_input("Titulo / cliente ou referencia", key="os_titulo")
        motor_id = st.text_input("Motor id (UUID opcional)", value="", key="os_motor")
        etapa_ini = st.selectbox("Etapa inicial", list(OS_ETAPAS), index=0, key="os_etapa_ini")
        calc_pick = st.selectbox("Vincular calculo da biblioteca (opcional)", calc_labels, key="os_calc_pick")
        go = st.form_submit_button("Abrir OS", use_container_width=True)

    if go:
        cid = calc_map.get(calc_pick) if calc_pick else None
        try:
            row = insert_ordem_servico(
                ctx.supabase,
                titulo=titulo or "Ordem de servico",
                motor_id=motor_id.strip() or None,
                etapa=etapa_ini,
                calc_id=cid,
                created_by=uid or None,
            )
            st.success(f"OS `{row.get('numero')}` criada (id `{row.get('id')}`).")
            st.session_state["os_selected_id"] = str(row.get("id"))
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

    lista = list_ordens_servico(ctx.supabase, limit=80)
    st.markdown(f"#### OS abertas / recentes ({len(lista)})")
    if not lista:
        st.info("Nenhuma OS ainda.")
        return

    labels = [_to_text(r.get("numero")) + " — " + _to_text(r.get("titulo")) for r in lista]
    id_by_label = {labels[i]: str(lista[i].get("id")) for i in range(len(lista))}
    default_sel = st.session_state.get("os_selected_id")
    default_label = ""
    for lab, oid in id_by_label.items():
        if oid == default_sel:
            default_label = lab
            break
    idx = labels.index(default_label) if default_label in labels else 0
    choice = st.selectbox("Selecionar OS", labels, index=idx, key="os_sel_detail")
    os_id = id_by_label.get(choice)
    if not os_id:
        return

    os_row = get_ordem_servico(ctx.supabase, os_id)
    if not os_row:
        st.warning("OS nao encontrada.")
        return

    st.markdown("##### Detalhe")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Numero", os_row.get("numero"))
    with c2:
        st.write("**Etapa atual:**", os_row.get("etapa"))
    with c3:
        st.write("**Motor id:**", os_row.get("motor_id") or "—")

    calc_id_cur = os_row.get("calc_id")
    if calc_id_cur:
        cdoc = get_calculo(ctx.supabase, str(calc_id_cur))
        st.caption(f"Calculo vinculado: {cdoc.get('titulo') if cdoc else calc_id_cur}")
    else:
        st.caption("Nenhum calculo da biblioteca vinculado.")

    with st.form("os_link_calc"):
        cp = st.selectbox("Alterar vinculo do calculo", calc_labels, key="os_relink")
        rel = st.form_submit_button("Atualizar vinculo", use_container_width=True)
    if rel:
        new_id = calc_map.get(cp) if cp else None
        try:
            link_os_to_calculo(ctx.supabase, os_id, new_id)
            st.success("Vinculo atualizado.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))

    payload = os_row.get("payload") if isinstance(os_row.get("payload"), dict) else {}
    ev: List[Dict[str, Any]] = payload.get("eventos") if isinstance(payload.get("eventos"), list) else []
    st.markdown("##### Linha do tempo")
    for e in reversed(ev[-30:]):
        st.write(f"- **{e.get('data')}** — `{e.get('etapa')}` — {_to_text(e.get('nota'))}")

    st.markdown("##### Registrar avanco de etapa")
    with st.form("os_avanco"):
        nova = st.selectbox("Proxima etapa", list(OS_ETAPAS), key="os_nova_etapa")
        nota = st.text_area("Nota (o que foi feito / observacao)", value="", key="os_nota_etapa")
        sub = st.form_submit_button("Registrar", use_container_width=True)
    if sub:
        try:
            append_os_event(ctx.supabase, os_id, etapa=nova, nota=nota)
            st.success("Etapa atualizada.")
            st.session_state["os_selected_id"] = os_id
            st.rerun()
        except Exception as exc:
            st.error(str(exc))


def show(ctx):
    return render(ctx)
