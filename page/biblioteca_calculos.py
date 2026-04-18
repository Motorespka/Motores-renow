from __future__ import annotations

import json
from typing import Any, Dict, List

import streamlit as st

from components.motor_rebobinagem_panel import render_rebobinagem_panel
from core.access_control import require_paid_access
from services.oficina_workshop import (
    build_calc_payload_from_parts,
    get_calculo,
    insert_calculo,
    list_calculos,
    parse_tags_csv,
    workshop_tables_available,
)


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _parse_int_list(raw: str) -> List[Any]:
    out: List[Any] = []
    for part in _to_text(raw).replace(";", ",").split(","):
        p = part.strip()
        if not p:
            continue
        try:
            out.append(int(p))
        except ValueError:
            out.append(p)
    return out


def render(ctx) -> None:
    if not require_paid_access("Biblioteca de calculos", client=ctx.supabase):
        return

    st.markdown("### Biblioteca de calculos (rebobinagem)")
    st.caption(
        "Guarde receitas reutilizaveis (passo, espiras, fio, ligacao). "
        "Procure antes de rebobinar; se nao existir, crie e depois duplique como **revisao** quando ajustar o calculo."
    )

    if not workshop_tables_available(ctx.supabase):
        st.error(
            "Tabelas `rebobinagem_calculos` / `oficina_ordens_servico` indisponiveis neste banco. "
            "No Supabase Cloud, execute o SQL em `backend/migrations/20260418_0044_rebobinagem_calculos_oficina_os.sql`. "
            "No modo DEV local, reinicie o app para criar as tabelas SQLite."
        )
        return

    uid = _to_text(st.session_state.get("auth_user_id") or st.session_state.get("auth_user_email"))

    parent_id = st.session_state.get("bib_calc_revision_parent")
    if parent_id and st.button("Cancelar modo revisao", key="bib_cancel_rev"):
        st.session_state.pop("bib_calc_revision_parent", None)
        st.rerun()

    q = st.text_input("Buscar (titulo, tags, notas, conteudo)", value="", key="bib_q")
    rows = list_calculos(ctx.supabase, q=q, limit=100)
    st.caption(f"{len(rows)} registro(s) listados.")

    sel_options = {f"{r.get('id')} — {r.get('titulo', '')}": str(r.get("id")) for r in rows if r.get("id") is not None}
    pick = st.selectbox("Abrir registro", options=[""] + list(sel_options.keys()), key="bib_pick")
    selected_id = sel_options.get(pick) if pick else None

    if selected_id:
        rec = get_calculo(ctx.supabase, selected_id)
        if rec:
            st.markdown("#### Registro selecionado")
            c1, c2 = st.columns(2)
            with c1:
                st.write("**Titulo:**", rec.get("titulo"))
                st.write("**Fases:**", rec.get("fases") or "—")
                st.write("**Tags:**", rec.get("tags") or [])
            with c2:
                st.write("**Pot. (CV):**", rec.get("potencia_cv"))
                st.write("**RPM / polos / tensao / ranhuras:**", rec.get("rpm"), "/", rec.get("polos"), "/", rec.get("tensao_v"), "/", rec.get("ranhuras"))
            if rec.get("revision_of"):
                st.caption(f"Revisao de: `{rec.get('revision_of')}` — {rec.get('revision_label') or ''}")
            if rec.get("notas"):
                st.markdown(rec.get("notas"))

            payload = rec.get("payload") if isinstance(rec.get("payload"), dict) else {}
            merged: Dict[str, Any] = {
                "motor": payload.get("motor") or {},
                "bobinagem_principal": payload.get("bobinagem_principal") or {},
                "bobinagem_auxiliar": payload.get("bobinagem_auxiliar") or {},
                "esquema": payload.get("esquema") or {},
            }
            with st.expander("Coerencia (read-only)", expanded=False):
                fake_row = {"dados_tecnicos_json": merged}
                render_rebobinagem_panel(fake_row, key_prefix=f"bib_rb_{selected_id}", title="Validacao rapida")

            dl = json.dumps(rec, ensure_ascii=False, indent=2, default=str)
            st.download_button("Baixar JSON", data=dl, file_name=f"calculo_{selected_id}.json", mime="application/json", key="bib_dl")

            if st.button("Preparar nova revisao a partir deste", key="bib_rev_btn"):
                st.session_state["bib_calc_revision_parent"] = str(rec.get("id"))
                st.rerun()

    st.markdown("---")
    st.markdown("#### Novo calculo (ou revisao)")
    if parent_id:
        st.info(f"Modo revisao: novo registro apontara para `{parent_id}`.")

    with st.form("bib_novo_calc"):
        titulo = st.text_input("Titulo (ex.: WEG 10CV 4 polos 220/380)", key="bib_titulo")
        tags_raw = st.text_input("Tags (separadas por virgula)", value="", key="bib_tags")
        fases = st.selectbox("Fases", ["", "Trifasico", "Monofasico"], key="bib_fases")
        n1, n2, n3, n4 = st.columns(4)
        with n1:
            pot_cv = st.number_input("Potencia (CV)", min_value=0.0, value=0.0, step=0.5, key="bib_cv")
        with n2:
            rpm = st.number_input("RPM", min_value=0, value=0, step=10, key="bib_rpm")
        with n3:
            polos = st.number_input("Polos", min_value=0, value=0, step=2, key="bib_polos")
        with n4:
            tensao = st.number_input("Tensao nominal (V)", min_value=0.0, value=0.0, step=10.0, key="bib_tensao")
        ranhuras = st.number_input("Ranhuras", min_value=0, value=0, step=1, key="bib_ran")
        st.markdown("**Motor (placa / referencia)**")
        m1, m2 = st.columns(2)
        with m1:
            marca = st.text_input("Marca", key="bib_marca")
            modelo = st.text_input("Modelo", key="bib_modelo")
        with m2:
            pot_txt = st.text_input("Potencia texto (opcional)", key="bib_pot_txt")
            tensao_txt = st.text_input("Tensao texto (ex.: 220/380)", key="bib_tensao_txt")

        st.markdown("**Bobinagem principal**")
        passos_raw = st.text_area("Passos (numeros separados por virgula)", value="", key="bib_passos")
        espiras_raw = st.text_area("Espiras (numeros separados por virgula)", value="", key="bib_esp")
        fios_raw = st.text_area("Fios (lista, ex.: 18,18 ou AWG20)", value="", key="bib_fios")
        ligacao = st.text_input("Ligacao", key="bib_lig")
        obs_bob = st.text_area("Observacoes bobinagem", value="", key="bib_obs_bob")
        st.markdown("**Esquema**")
        ranh_esq = st.text_input("Ranhuras (esquema, texto)", key="bib_ran_esq")
        dist = st.text_input("Distribuicao bobinas", key="bib_dist")
        notas = st.text_area("Notas da biblioteca", value="", key="bib_notas")
        rev_label = st.text_input("Rotulo da revisao (se revisao)", value="", key="bib_rev_lbl")
        save = st.form_submit_button("Salvar na biblioteca", use_container_width=True)

    if save:
        motor: Dict[str, Any] = {
            "marca": _to_text(marca),
            "modelo": _to_text(modelo),
            "potencia": _to_text(pot_txt) or (str(pot_cv) if pot_cv else ""),
            "rpm": str(int(rpm)) if rpm else "",
            "polos": str(int(polos)) if polos else "",
            "tensao": _to_text(tensao_txt) or (str(tensao) if tensao else ""),
            "fases": _to_text(fases),
        }
        bp: Dict[str, Any] = {
            "passos": _parse_int_list(passos_raw),
            "espiras": _parse_int_list(espiras_raw),
            "fios": [x.strip() for x in _to_text(fios_raw).split(",") if x.strip()],
            "ligacao": _to_text(ligacao),
            "observacoes": _to_text(obs_bob),
        }
        esq: Dict[str, Any] = {
            "ranhuras": _to_text(ranh_esq) or (str(int(ranhuras)) if ranhuras else ""),
            "distribuicao_bobinas": _to_text(dist),
        }
        payload = build_calc_payload_from_parts(motor=motor, bobinagem_principal=bp, esquema=esq)
        try:
            out = insert_calculo(
                ctx.supabase,
                titulo=titulo or "Sem titulo",
                notas=notas,
                tags=parse_tags_csv(tags_raw),
                fases=fases,
                potencia_cv=float(pot_cv) if pot_cv else None,
                rpm=int(rpm) if rpm else None,
                polos=int(polos) if polos else None,
                tensao_v=float(tensao) if tensao else None,
                ranhuras=int(ranhuras) if ranhuras else None,
                payload=payload,
                revision_of=str(parent_id) if parent_id else None,
                revision_label=rev_label,
                created_by=uid or None,
            )
            st.success(f"Salvo com id `{out.get('id')}`.")
            st.session_state.pop("bib_calc_revision_parent", None)
            st.rerun()
        except Exception as exc:
            st.error(str(exc))


def show(ctx):
    return render(ctx)
