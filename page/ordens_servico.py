from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st

from core.access_control import require_paid_access
from core.navigation import Route
from services.oficina_export import build_os_csv_row_bytes, build_os_json_snapshot_bytes
from services.oficina_pdf import build_os_delivery_pdf_bytes
from services.oficina_os_operacao import normalize_operacao_payload_patch
from services.oficina_workshop import (
    OS_ETAPAS,
    append_os_event,
    get_calculo,
    get_ordem_servico,
    insert_ordem_servico,
    link_os_to_calculo,
    list_calculos,
    list_ordens_servico,
    merge_ordem_servico_payload,
    workshop_tables_available,
)


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _fmt_calc_option(r: Dict[str, Any]) -> str:
    return f"{r.get('id')} — {r.get('titulo', '')}"


def _anexos_lines_from_payload(pl: Dict[str, Any]) -> str:
    raw = pl.get("anexos_urls")
    if not isinstance(raw, list):
        return ""
    lines = [_to_text(x) for x in raw if _to_text(x)]
    return "\n".join(lines)


def render(ctx) -> None:
    if not require_paid_access("Ordens de servico", client=ctx.supabase):
        return

    st.markdown("### Ordens de servico (oficina)")
    st.caption(
        "Acompanhe o fluxo: recebe → busca/cria calculo → limpeza → rebobina → impregna → montagem → teste → pecas → entrega. "
        "Cada mudanca de etapa fica registrada na linha do tempo da OS. Ver **Guia oficina** no menu para o passo a passo."
    )

    if not workshop_tables_available(ctx.supabase):
        st.error(
            "Tabelas indisponiveis. No Supabase, rode `backend/migrations/20260418_0044_rebobinagem_calculos_oficina_os.sql`. "
            "Em DEV local, reinicie para criar SQLite. Opcional: `20260418_0049_oficina_workshop_rls.sql` para RLS."
        )
        return

    uid = _to_text(st.session_state.get("auth_user_id") or st.session_state.get("auth_user_email"))

    calcs = list_calculos(ctx.supabase, q="", limit=80)
    calc_labels = [""] + [_fmt_calc_option(c) for c in calcs if c.get("id")]
    calc_map = {_fmt_calc_option(c): str(c.get("id")) for c in calcs if c.get("id")}

    st.markdown("#### Nova OS")
    st.caption(
        "**Titulo:** referencia interna do servico (sem dados pessoais de cliente). **Motor id:** UUID do motor na base "
        "(opcional; use o detalhe do motor para copiar). **Calculo:** receita da biblioteca para amarrar ao PDF."
    )
    with st.form("os_nova"):
        titulo = st.text_input("Titulo / cliente ou referencia", key="os_titulo", help="Aparece no PDF e na lista.")
        motor_id = st.text_input(
            "Motor id (UUID opcional)",
            value="",
            key="os_motor",
            help="Se preenchido, liga esta OS ao registo do motor para rastreio.",
        )
        etapa_ini = st.selectbox("Etapa inicial", list(OS_ETAPAS), index=0, key="os_etapa_ini")
        calc_pick = st.selectbox(
            "Vincular calculo da biblioteca (opcional)",
            calc_labels,
            key="os_calc_pick",
            help="O PDF inclui titulo e testes de bancada do calculo escolhido.",
        )
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

    st.markdown("#### Filtrar lista")
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        etapa_opts = ["(todas)"] + list(OS_ETAPAS)
        f_etapa = st.selectbox("Etapa", etapa_opts, index=0, key="os_f_etapa")
    with fc2:
        f_motor = st.text_input("Motor id contem", value="", key="os_f_motor")
    with fc3:
        f_txt = st.text_input("Texto (numero, titulo, payload)", value="", key="os_f_txt")
    fc4, fc5 = st.columns(2)
    with fc4:
        f_days = st.number_input("Ultimos N dias (0 = todos)", min_value=0, max_value=3650, value=0, step=1, key="os_f_days")
    with fc5:
        f_mine = st.checkbox("So as minhas (created_by = eu)", value=False, key="os_f_mine")

    fc6, fc7 = st.columns([1, 3])
    with fc6:
        if st.button("Limpar filtros", key="os_f_clear", help="Volta a etapa (todas), limpa texto, dias = 0 e desmarca so as minhas."):
            for k in ("os_f_etapa", "os_f_motor", "os_f_txt", "os_f_days", "os_f_mine"):
                st.session_state.pop(k, None)
            st.rerun()
    filtros_txt: List[str] = []
    if f_etapa != "(todas)":
        filtros_txt.append(f"etapa={f_etapa}")
    if _to_text(f_motor):
        filtros_txt.append(f"motor contem `{_to_text(f_motor)}`")
    if _to_text(f_txt):
        filtros_txt.append("texto livre")
    if int(f_days) > 0:
        filtros_txt.append(f"ultimos {int(f_days)} dias")
    if f_mine:
        filtros_txt.append("so as minhas")
    with fc7:
        if filtros_txt:
            st.caption("Filtros ativos: " + " · ".join(filtros_txt))
        else:
            st.caption("Nenhum filtro restritivo (lista completa ate ao limite).")

    etapa_f = "" if f_etapa == "(todas)" else str(f_etapa)
    lista = list_ordens_servico(
        ctx.supabase,
        limit=80,
        etapa=etapa_f,
        motor_q=f_motor,
        texto=f_txt,
        since_days=int(f_days) if f_days else 0,
        only_created_by=uid if f_mine else "",
    )

    st.markdown(f"##### OS listadas ({len(lista)})")
    if not lista:
        st.info(
            "Nenhuma OS corresponde aos filtros — ou ainda nao ha ordens. "
            "Crie uma com **Nova OS** ou limpe os filtros (etapa **(todas)**, dias **0**, desmarque *So as minhas*)."
        )
        if st.button("Ver guia da oficina", key="os_empty_guia"):
            ctx.session.set_route(Route.GUIA_OFICINA)
            st.rerun()
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

    pl_os = os_row.get("payload") if isinstance(os_row.get("payload"), dict) else {}

    calc_id_cur = os_row.get("calc_id")
    cdoc = None
    if calc_id_cur:
        cdoc = get_calculo(ctx.supabase, str(calc_id_cur))
        st.caption(f"Calculo vinculado: {cdoc.get('titulo') if cdoc else calc_id_cur}")
    else:
        st.caption("Nenhum calculo da biblioteca vinculado.")

    pdf_bytes = None
    try:
        pdf_bytes = build_os_delivery_pdf_bytes(os_row=os_row, calc_row=cdoc)
    except Exception:
        pdf_bytes = None

    d1, d2, d3 = st.columns(3)
    with d1:
        st.download_button(
            "Baixar relatorio de entrega (PDF)",
            data=pdf_bytes or b"",
            file_name=f"OS_{_to_text(os_row.get('numero') or os_id)}.pdf",
            mime="application/pdf",
            use_container_width=True,
            disabled=pdf_bytes is None,
            key=f"os_dl_pdf_{os_id}",
        )
    with d2:
        st.download_button(
            "Exportar JSON (arquivo interno)",
            data=build_os_json_snapshot_bytes(os_row=os_row, calc_row=cdoc),
            file_name=f"OS_{_to_text(os_row.get('numero') or os_id)}.json",
            mime="application/json",
            use_container_width=True,
            key=f"os_dl_json_{os_id}",
        )
    with d3:
        st.download_button(
            "Exportar CSV (uma linha)",
            data=build_os_csv_row_bytes(os_row=os_row),
            file_name=f"OS_{_to_text(os_row.get('numero') or os_id)}.csv",
            mime="text/csv",
            use_container_width=True,
            key=f"os_dl_csv_{os_id}",
        )

    with st.expander("Texto para o cliente (aparece no PDF de entrega)", expanded=False):
        st.caption(
            "Opcional. Bloco no relatorio (apos a capa): garantia, observacoes de entrega, etc. "
            "``payload.texto_relatorio_entrega``."
        )
        txt_cli = st.text_area(
            "Notas / texto para o cliente",
            value=_to_text(pl_os.get("texto_relatorio_entrega")),
            height=120,
            key=f"os_txt_rel_{os_id}",
        )
        if st.button("Guardar texto do relatorio", use_container_width=True, key=f"os_btn_txt_rel_{os_id}"):
            try:
                merge_ordem_servico_payload(ctx.supabase, os_id, {"texto_relatorio_entrega": _to_text(txt_cli)})
                st.success("Texto guardado.")
                st.session_state["os_selected_id"] = os_id
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    with st.expander("Capa do PDF e anexos (URLs)", expanded=False):
        st.caption(
            "**Responsavel** na capa (opcional). **Anexos:** uma URL por linha — links para Storage, Drive, etc.; "
            "o PDF lista os enderecos sem embutir imagens. ``payload.capa_responsavel`` e ``payload.anexos_urls``."
        )
        capa_r = st.text_input(
            "Responsavel / oficina (capa do PDF)",
            value=_to_text(pl_os.get("capa_responsavel")),
            key=f"os_capa_resp_{os_id}",
        )
        anexos_raw = st.text_area(
            "URLs de anexos (uma por linha)",
            value=_anexos_lines_from_payload(pl_os),
            height=100,
            key=f"os_anexos_{os_id}",
        )
        if st.button("Guardar capa e anexos", use_container_width=True, key=f"os_btn_anexos_{os_id}"):
            urls: List[str] = []
            for line in anexos_raw.replace("\r\n", "\n").split("\n"):
                u = _to_text(line)
                if u:
                    urls.append(u)
            try:
                merge_ordem_servico_payload(
                    ctx.supabase,
                    os_id,
                    {"capa_responsavel": _to_text(capa_r), "anexos_urls": urls},
                )
                st.success("Guardado.")
                st.session_state["os_selected_id"] = os_id
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    with st.expander("Operacao interna (prazo e custos — sem dados de cliente)", expanded=False):
        st.caption(
            "Opcional. **So referencia de trabalho / motor** — nao armazene nome, telefone ou documento de cliente. "
            "Valores em reais (internamente gravados em centavos). Prazo: AAAA-MM-DD."
        )
        ref_i = st.text_input(
            "Referencia interna (ex.: pedido fornecedor, nota fiscal material)",
            value=_to_text(pl_os.get("referencia_interna_os")),
            max_chars=200,
            key=f"os_ref_int_{os_id}",
        )
        prazo_v = _to_text(pl_os.get("prazo_entrega_previsto"))

        def _reais_from_cent(c: Any) -> float:
            try:
                n = int(c)
            except (TypeError, ValueError):
                return 0.0
            return round(n / 100.0, 2)

        oc0 = pl_os.get("orcamento_centavos")
        cm0 = pl_os.get("custo_material_centavos")
        cl0 = pl_os.get("custo_mao_obra_centavos")
        prazo_in = st.text_input("Prazo previsto (AAAA-MM-DD)", value=prazo_v, key=f"os_prazo_{os_id}")
        orc_r = st.number_input("Orcamento interno (R$)", min_value=0.0, value=float(_reais_from_cent(oc0)), step=10.0, key=f"os_orc_{os_id}")
        cm_r = st.number_input("Custo material (R$)", min_value=0.0, value=float(_reais_from_cent(cm0)), step=10.0, key=f"os_cm_{os_id}")
        cl_r = st.number_input("Custo mao-de-obra (R$)", min_value=0.0, value=float(_reais_from_cent(cl0)), step=10.0, key=f"os_cl_{os_id}")
        if st.button("Guardar operacao interna", use_container_width=True, key=f"os_btn_op_{os_id}"):
            patch_raw: Dict[str, Any] = {
                "referencia_interna_os": _to_text(ref_i),
                "prazo_entrega_previsto": _to_text(prazo_in),
                "orcamento_centavos": int(round(orc_r * 100)) if orc_r > 0 else None,
                "custo_material_centavos": int(round(cm_r * 100)) if cm_r > 0 else None,
                "custo_mao_obra_centavos": int(round(cl_r * 100)) if cl_r > 0 else None,
            }
            try:
                patch = normalize_operacao_payload_patch(patch_raw)
                merge_ordem_servico_payload(ctx.supabase, os_id, patch)
                st.success("Operacao interna guardada (aparece no PDF de entrega).")
                st.session_state["os_selected_id"] = os_id
                st.rerun()
            except ValueError as ve:
                st.error(str(ve))
            except Exception as exc:
                st.error(str(exc))

    ficha = pl_os.get("ficha_mecanica") if isinstance(pl_os.get("ficha_mecanica"), dict) else {}
    with st.expander("Ficha mecanica (rolamentos, alinhamento, antes/depois)", expanded=False):
        st.caption(
            "Registo objectivo para manutencao: rolamentos, folgas, alinhamento, vibracao/temperatura em bancada. "
            "``payload.ficha_mecanica``."
        )
        if ficha and any(_to_text(v) for v in ficha.values()):
            for k, v in ficha.items():
                st.write(f"- **{k}**: {_to_text(v) or '—'}")
        else:
            st.caption("Sem dados ainda — use o formulario abaixo.")

        fk = f"os_{os_id}_"
        with st.form(f"os_ficha_mec_{os_id}"):
            rl_d = st.text_input(
                "Rolamento lado acoplamento (recebimento)",
                value=ficha.get("rolamento_drive", "") or "",
                key=fk + "rl_d",
            )
            rl_o = st.text_input("Rolamento lado oposto", value=ficha.get("rolamento_oposto", "") or "", key=fk + "rl_o")
            alin = st.text_input("Alinhamento / acoplamento", value=ficha.get("alinhamento", "") or "", key=fk + "alin")
            torque = st.text_input("Torque / parafusos carcaca (referencia)", value=ficha.get("torque_carcaca", "") or "", key=fk + "torque")
            vib = st.text_input("Vibracao / observacao mecanica", value=ficha.get("vibracao", "") or "", key=fk + "vib")
            temp = st.text_input("Temperatura em teste (°C max)", value=ficha.get("temperatura_teste", "") or "", key=fk + "temp")
            antes = st.text_area("Antes (chegada): folgas, ruido, foto ref.", value=ficha.get("obs_antes", "") or "", key=fk + "antes")
            depois = st.text_area("Depois (entrega): medicao final, observacoes", value=ficha.get("obs_depois", "") or "", key=fk + "depois")
            sub_f = st.form_submit_button("Salvar ficha mecanica", use_container_width=True)

            if sub_f:
                patch = {
                    "rolamento_drive": _to_text(rl_d),
                    "rolamento_oposto": _to_text(rl_o),
                    "alinhamento": _to_text(alin),
                    "torque_carcaca": _to_text(torque),
                    "vibracao": _to_text(vib),
                    "temperatura_teste": _to_text(temp),
                    "obs_antes": _to_text(antes),
                    "obs_depois": _to_text(depois),
                }
                patch = {k: v for k, v in patch.items() if v}
                try:
                    merge_ordem_servico_payload(ctx.supabase, os_id, {"ficha_mecanica": patch})
                    st.success("Ficha mecanica guardada.")
                    st.session_state["os_selected_id"] = os_id
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))

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

    ev: List[Dict[str, Any]] = pl_os.get("eventos") if isinstance(pl_os.get("eventos"), list) else []
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
