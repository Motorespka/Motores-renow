#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Demo calculo proporcional + Gemini sobre acervo OFICIAL (Streamlit)."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

from app.oficial_engine import validate_required_motor_inputs
from engine.winding_optimizer import StatorInput, WindingOptimizer
from engine.winding_sanity import MSG_MAGNETIC_GATE_HIST_OVERRIDE
from app.search_lib import (
    DEFAULT_DB,
    connect,
    load_all_motors,
    parse_awg_number,
    parse_polos_for_calc,
    parse_ranhuras_for_calc,
    parse_scalar,
)
from core.access_control import require_admin_access
from core.navigation import Route
from core.streamlit_perf import maybe_fragment, pop_page_ctx_pack, stash_page_ctx
from core.ui_feedback import mrw_render_banner_zone
from app.topologia_bobinagem import TIPOS_BOBINAGEM, TIPOS_UI_ORDER, label_tipo
from services.acervo_oficial_stats import load_acervo_stats
from services.demo_calculo_report import build_report_html


@st.dialog("Prévia do Relatório de Engenharia", width="large")
def _report_preview_dialog() -> None:
    entrada = st.session_state.get("demo_calculo_entrada") or {}
    res = st.session_state.get("demo_calculo_result") or {}
    html_doc = st.session_state.get("demo_calculo_report_html") or build_report_html(
        entrada=entrada, result=res
    )
    ref = datetime.now(timezone.utc).strftime("PRE-%Y%m%d-%H%M%S")
    st.caption(
        "Somente visualização — não grava cadastro, manifesto nem banco. "
        "Use **Imprimir / Salvar PDF** no documento abaixo ou baixe o HTML."
    )
    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "Baixar HTML",
            data=html_doc,
            file_name=f"previa-rebobinagem-{ref}.html",
            mime="text/html",
            use_container_width=True,
            key="demo_report_download",
        )
    with c2:
        if st.button("Fechar", use_container_width=True, key="demo_report_close"):
            st.rerun()
    components.html(html_doc, height=780, scrolling=True)


@st.cache_resource
def _catalog():
    conn = connect(DEFAULT_DB)
    motors = load_all_motors(conn)
    meta = {r["key"]: r["value"] for r in conn.execute("SELECT key, value FROM index_meta").fetchall()}
    conn.close()
    return motors, meta


def _render_scenario_card(cen: dict, *, recomendado: bool = False) -> None:
    if recomendado:
        st.success("Cenário recomendado (referência principal)")
    if cen.get("desabilitado"):
        st.error("Cenário indisponível — calibre fora do intervalo seguro.")
    score = int(cen.get("confidence_score", 0))
    c1, c2, c3 = st.columns(3)
    c1.metric("Espiras", cen.get("espiras", "—"))
    c2.metric("Confiança", f"{score}%")
    c3.metric("Ocupação ranhura", f"{cen.get('fator_ocupacao_ranhura', '—')}%")
    fio_show = cen.get("fio_texto", "") or cen.get("calibre_display", "")
    if fio_show == "CALIBRE INVÁLIDO":
        st.error("**CALIBRE INVÁLIDO** — use o Cenário B como referência.")
    else:
        st.markdown(f"**{fio_show}**")
    alt_par = cen.get("fio_alternativa_paralelo") or ""
    if alt_par and alt_par != cen.get("fio_texto"):
        st.info(f"Alternativa em paralelo: {alt_par}")
    st.caption(cen.get("descricao", ""))
    if score < 50:
        st.error("Confiança baixa — revisar na bancada antes de bobinar.")
    for alerta in cen.get("alertas") or []:
        if "Saturação" in alerta:
            st.warning(alerta)
        elif "Ocupação" in alerta:
            st.warning(alerta)
        elif "Desvio" in alerta:
            st.warning(alerta)
        else:
            st.warning(alerta)
    if cen.get("desvio_historico_pct") is not None:
        pct = float(cen["desvio_historico_pct"]) * 100
        st.caption(f"Desvio vs média histórica: {pct:.1f}%")
    st.caption(
        f"Índice fluxo (proxy): {cen.get('densidade_fluxo_indice', '—')} · "
        f"Bússola hist.: {cen.get('espiras_busola_ref', '—')} · "
        f"Prop.: {cen.get('espiras_proporcional_ref', '—')} espiras"
    )


def _render_stats_bar() -> None:
    acervo = load_acervo_stats()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("OFICIAIS (manifest)", acervo.get("oficial_manifest", 0))
    c2.metric("No indice SQLite", acervo.get("indexed_total", 0))
    c3.metric("Registros completos (file)", acervo.get("file_complete", 0))
    c4.metric("Indice gerado em", acervo.get("index_generated_at", "—")[:10] or "—")
    if not Path(DEFAULT_DB).is_file():
        st.error(
            "Indice local ausente. No servidor, rode: `python scripts/index_for_search.py` "
            "ou confirme que `data/oficial_search.sqlite` esta no deploy."
        )


def _render_form(ctx) -> None:
    st.markdown("### Entrada do motor")
    st.session_state.setdefault("demo_ranhuras", 36)
    st.session_state.setdefault("demo_polos", 0)
    c1, c2, c3 = st.columns(3)
    with c1:
        diametro = st.text_input("Diametro estator (mm)", value="80", key="demo_diam")
    with c2:
        pacote = st.text_input("Comprimento pacote (mm)", value="70", key="demo_pac")
    with c3:
        carcaca = st.text_input("Carcaça NEMA/IEC", value="80A", key="demo_carc")
    topo_opts = {"(Inferir automaticamente)": ""}
    topo_opts.update(
        {label_tipo(k): k for k in TIPOS_UI_ORDER if k in TIPOS_BOBINAGEM and k != "DESCONHECIDO"}
    )
    topo_labels = list(topo_opts.keys())
    tipo_bob_label = st.selectbox(
        "Tipo de bobinagem",
        options=topo_labels,
        index=0,
        key="demo_tipo_bob",
        help="Opcional. Se nao souber, deixe em inferir automaticamente — o sistema explica o tipo detectado.",
    )
    tipo_bob = topo_opts[tipo_bob_label]

    c4, c5, c6 = st.columns(3)
    with c4:
        ranhuras = st.number_input(
            "Número de ranhuras *",
            min_value=1,
            step=1,
            key="demo_ranhuras",
            help="Obrigatório. Padrão: 36 ranhuras.",
        )
    with c5:
        polos = st.number_input(
            "Número de polos (opcional)",
            min_value=0,
            max_value=12,
            step=2,
            key="demo_polos",
            help=(
                "Opcional (polaridade). Deixe **0** se não souber — o cálculo usa ferro, "
                "passo e ranhuras. Se souber: 2, 4, 6, 8, 10 ou 12."
            ),
        )
    with c6:
        ligacao = st.text_input("Tipo de ligacao", value="Estrela", key="demo_lig")

    c7, c8 = st.columns(2)
    with c7:
        passo = st.text_input(
            "Passos bobinagem (opcional no modo sobrevivência)",
            value="1:7",
            key="demo_passo",
        )
    with c8:
        st.caption(
            "Sem passo: o sistema estima pelo ferro (Ø, pacote, ranhuras, polos) "
            "usando referências de geometria similar."
        )

    st.markdown("### Seu calculo (validacao)")
    e1, e2 = st.columns(2)
    with e1:
        fio_eng = st.text_input("Fio AWG", value="23", key="demo_fio")
    with e2:
        esp_eng = st.text_input("Espiras", value="", key="demo_esp")

    if st.button(
        "Gerar Projetos de Bobinagem (3 cenários)",
        type="primary",
        use_container_width=True,
    ):
        try:
            d = float(str(diametro).replace(",", "."))
            p = float(str(pacote).replace(",", "."))
        except ValueError:
            st.warning("Informe diametro e pacote numericos.")
            return
        if d <= 0 or p <= 0:
            st.warning("Diametro e pacote devem ser maiores que zero.")
            return
        n_ranh = parse_ranhuras_for_calc(ranhuras, default=36)
        n_polos = parse_polos_for_calc(polos)
        ok_req, req_msg = validate_required_motor_inputs(
            diametro_mm=d,
            pacote_mm=p,
            ranhuras=n_ranh,
            polos=n_polos,
        )
        if not ok_req:
            st.warning(req_msg)
            return
        try:
            motors, _ = _catalog()
        except FileNotFoundError as exc:
            st.error(str(exc))
            return
        esp_user = parse_scalar(str(esp_eng).strip()) if str(esp_eng).strip() else None
        fio_user = parse_awg_number(str(fio_eng).strip()) if str(fio_eng).strip() else None

        with st.spinner("Otimizando bobinagem (3 cenários)..."):
            opt = WindingOptimizer(motors)
            opt_res = opt.optimize(
                StatorInput(
                    diametro_mm=d,
                    pacote_mm=p,
                    ranhuras=int(n_ranh),
                    polos=n_polos,
                    carcaca=carcaca,
                    passo=passo,
                    tipo_bobinagem=tipo_bob,
                    ligacao=ligacao,
                    espiras_validacao_usuario=esp_user,
                    fio_validacao_usuario_awg=fio_user,
                ),
                use_gemini=True,
                top_k=5,
            )
        if opt_res.validation_status == "INCOMPLETO" or not opt_res.cenarios:
            st.error(
                opt_res.validation_message
                or "Cálculo bloqueado — confira diâmetro, pacote, ranhuras e polos."
            )
            return
        st.session_state["demo_calculo_optimizer"] = {
            "entrada": opt_res.entrada,
            "cenarios": [asdict(c) for c in opt_res.cenarios],
            "calculo_baseado_em": opt_res.calculo_baseado_em,
            "media_historica_espiras": opt_res.media_historica_espiras,
            "media_proporcional_espiras": opt_res.media_proporcional_espiras,
            "slot_fill_limite": opt_res.slot_fill_limite,
            "n_referencias": opt_res.n_referencias,
            "validation_status": opt_res.validation_status,
            "validation_message": opt_res.validation_message,
            "modo_sobrevivencia": opt_res.modo_sobrevivencia,
            "is_estimativa": opt_res.is_estimativa,
            "forcar_gemini": opt_res.forcar_gemini,
            "cenario_recomendado": opt_res.cenario_recomendado,
            "tipo_inferido": opt_res.tipo_inferido,
            "tipo_inferido_label": opt_res.tipo_inferido_label,
            "explicacao_tipo": opt_res.explicacao_tipo,
            "tipo_foi_inferido": opt_res.tipo_foi_inferido,
            "media_historica_limpa": opt_res.media_historica_limpa,
            "n_outliers_removidos": opt_res.n_outliers_removidos,
            "cenario_a_suprimido": opt_res.cenario_a_suprimido,
            "usa_validacao_usuario": opt_res.usa_validacao_usuario,
            "busola_historica_inconsistente": opt_res.busola_historica_inconsistente,
            "espiras_validacao_usuario": opt_res.espiras_validacao_usuario,
            "magnetic_sanity_gate_active": opt_res.magnetic_sanity_gate_active,
            "volume_estator_mm3": opt_res.volume_estator_mm3,
            "n_removed_pollution": opt_res.n_removed_pollution,
        }
        st.session_state["demo_calculo_result"] = opt_res.base_suggestion or {}
        st.session_state["demo_calculo_entrada"] = {
            "diametro_mm": d,
            "pacote_mm": p,
            "carcaca": carcaca,
            "passo": passo,
            "tipo_bobinagem": tipo_bob,
            "ligacao": ligacao,
            "ranhuras": int(n_ranh),
            "polos": n_polos,
            "fio_engenheiro": fio_eng,
            "espiras_engenheiro": esp_eng,
        }

    opt_data = st.session_state.get("demo_calculo_optimizer")
    res = st.session_state.get("demo_calculo_result")
    if not opt_data and not res:
        return

    if opt_data and opt_data.get("cenarios"):
        st.divider()
        st.markdown("### Motor de Projetos de Bobinagem")
        if opt_data.get("tipo_foi_inferido") and opt_data.get("explicacao_tipo"):
            st.info(opt_data["explicacao_tipo"])
        elif opt_data.get("tipo_inferido_label"):
            st.caption(f"Tipo de bobinagem: **{opt_data['tipo_inferido_label']}**")
        if opt_data.get("is_estimativa"):
            st.warning(
                opt_data.get("calculo_baseado_em")
                or "Referência exata não encontrada. Sugestão baseada em motores similares "
                "da mesma carcaça (confiança: média)."
            )
        elif opt_data.get("calculo_baseado_em"):
            st.info(opt_data["calculo_baseado_em"])
        if opt_data.get("forcar_gemini"):
            st.caption("Validação / interpolação proporcional via Gemini (≥3 motores na mesma carcaça).")
        n_out = int(opt_data.get("n_outliers_removidos") or 0)
        hist_txt = f"**{opt_data.get('media_historica_espiras', '—')}**"
        if n_out > 0:
            hist_txt += f" (mediana limpa; {n_out} outlier(s) removido(s) ±30%)"
        npoll = int(opt_data.get("n_removed_pollution") or 0)
        if npoll > 0:
            st.caption(
                f"Filtro de cadastro: **{npoll}** referência(s) em carcaça 80–90 com < 20 espiras "
                "excluída(s) da bússola."
            )
        if opt_data.get("magnetic_sanity_gate_active"):
            st.warning(MSG_MAGNETIC_GATE_HIST_OVERRIDE)
            vol = opt_data.get("volume_estator_mm3")
            if vol:
                st.caption(f"Volume útil do estator (proxy πr²h): **{float(vol):,.0f} mm³**")
        if opt_data.get("usa_validacao_usuario"):
            st.success(
                f"Validação do usuário ativa: **{opt_data.get('espiras_validacao_usuario', '—')}** "
                "espiras definem o cálculo (Constante K). Média histórica só como comparativo."
            )
        if opt_data.get("busola_historica_inconsistente"):
            st.warning(
                "Bússola histórica divergente: usando valores validados pelo usuário."
            )
        busola_lbl = (
            "Média histórica (comparativo)"
            if opt_data.get("usa_validacao_usuario")
            else "Média histórica (referência)"
        )
        st.caption(
            f"Referências: **{opt_data.get('n_referencias', 0)}** · "
            f"Cenário B = padrão principal · "
            f"{busola_lbl}: {hist_txt} espiras · "
            f"Média proporcional (comparativo): **{opt_data.get('media_proporcional_espiras', '—')}** espiras"
        )
        if opt_data.get("cenario_a_suprimido"):
            st.warning(
                "Cenário A oculto: cálculo inválido por inconsistência física "
                "(desvio >20% da média histórica ou ocupação de ranhura inaceitável). "
                "Use o **Cenário B** como referência principal."
            )
        rec_id = str(opt_data.get("cenario_recomendado") or "B")
        _TAB_TITLES = {
            "A": "A — Otimizado / Eficiência",
            "B": "B — Padrão de Referência",
            "C": "C — Facilidade de Execução",
        }
        tab_labels = []
        for cen in opt_data["cenarios"]:
            cid = str(cen.get("cenario_id", "B"))
            lbl = _TAB_TITLES.get(cid, cid)
            if cid == rec_id:
                lbl = f"{lbl} ★"
            tab_labels.append(lbl)
        tabs = st.tabs(tab_labels)
        for tab, cen in zip(tabs, opt_data["cenarios"]):
            with tab:
                _render_scenario_card(
                    cen, recomendado=str(cen.get("cenario_id")) == rec_id
                )
        st.divider()

    if not res:
        return

    st.divider()
    st.markdown("### Prévia de relatório (bancada)")
    if st.button(
        "Visualizar Relatório",
        type="secondary",
        use_container_width=True,
        key="demo_btn_visualizar_relatorio",
        help="Abre documento A4 para impressão ou print — não salva no banco.",
    ):
        entrada = st.session_state.get("demo_calculo_entrada") or {
            "diametro_mm": diametro,
            "pacote_mm": pacote,
            "carcaca": carcaca,
            "passo": passo,
            "tipo_bobinagem": tipo_bob,
            "ligacao": ligacao,
            "fio_engenheiro": fio_eng,
            "espiras_engenheiro": esp_eng,
        }
        st.session_state["demo_calculo_report_html"] = build_report_html(
            entrada=entrada, result=res
        )
        _report_preview_dialog()

    a, b, c = st.columns(3)
    with a:
        st.markdown("#### Sugestao do Sistema")
        if res.get("calculo_baseado_em"):
            st.info(res.get("calculo_baseado_em"))
        st.metric("Espiras (formula proporcional)", res.get("sugestao_espira", "—"))
        if res.get("sugestao_fio_texto"):
            st.markdown(f"**{res.get('sugestao_fio_texto')}**")
        else:
            st.metric("Fio AWG sugerido", res.get("sugestao_fio_awg", "—"))
        st.caption(
            f"Modo: **{res.get('modo_processamento', '')}** · "
            f"Gemini validador: **{'Sim' if res.get('gemini_usado') else 'Nao'}**"
        )
        if res.get("modo_sobrevivencia"):
            st.caption("Modo Sobrevivência — estimativa de ferro ativa.")
        if res.get("ranhura_saturada"):
            st.error("AVISO: Ranhura Saturada, verifique a bitola do fio.")
        st.write(res.get("justificativa_tecnica") or "")
        if res.get("alerta_risco"):
            st.warning(res.get("alerta_risco"))
        st.caption(f"Media proporcional (ref.): {res.get('espiras_media_top5', '—')} espiras")
        if res.get("media_historica_espiras") is not None:
            st.caption(f"Media historica (mesmo passo): {res.get('media_historica_espiras')} espiras")
        if res.get("slot_fill_limit") is not None:
            st.caption(
                f"Enchimento ranhura: {res.get('slot_fill_actual', '—')} / limite {res.get('slot_fill_limit')}"
            )
    with b:
        st.markdown("#### Sua Entrada")
        st.write(f"Estator: **{diametro}** x **{pacote}** mm")
        st.write(f"Carcaça: **{carcaca}** · Passo: **{passo}** · Ligacao: **{ligacao}**")
        st.write(f"Fio: **{fio_eng or '—'}** · Espiras: **{esp_eng or '—'}**")
    with c:
        st.markdown("#### Validacao")
        vstat = res.get("validation_status", "—")
        tipo_lbl = res.get("tipo_bobinagem_label") or label_tipo(res.get("tipo_bobinagem", ""))
        st.markdown(f"**{vstat}**")
        st.caption(f"Tipo de bobinagem detectado: **{tipo_lbl or '—'}**")
        if res.get("topologia_mistura"):
            st.warning(
                "Atenção: Mistura de topologias de bobinagem detectada. Precisão reduzida."
            )
        st.write(res.get("validation_message") or "")
        for line in res.get("lei_ranhura_logs") or []:
            st.caption(line)
        if vstat == "REVISAR":
            st.warning("Calculo nao aprovado automaticamente — revisar na bancada antes de bobinar.")

    matches = res.get("top_matches") or []
    if matches:
        st.markdown("#### Top 5 — formula proporcional aplicada")
        st.caption(
            "Espiras_calc = Espiras_hist × (Pacote_in/Pacote_hist) × (Area_in/Area_hist). "
            "**Nunca** copia espiras do historico sem recalcular."
        )
        st.dataframe(
            [
                {
                    "arquivo": (m.get("arquivo_rel") or "")[:48],
                    "diam_hist": m.get("diametro_mm"),
                    "pac_hist": m.get("pacote_mm"),
                    "esp_hist": m.get("espiras_historico"),
                    "esp_calc": m.get("espiras_calculadas"),
                    "R_pacote": m.get("pacote_ratio"),
                    "R_area": m.get("area_ratio"),
                    "score": round(float(m.get("score", 0)), 3),
                }
                for m in matches
            ],
            use_container_width=True,
            hide_index=True,
        )

    if res.get("validation_status") == "REVISAR":
        st.caption("Salvar no manifesto so apos conferencia fisica (status REVISAR).")

    if st.button("Salvar Novo Calculo Oficial", use_container_width=True):
        from app.oficial_engine import save_official_calculation

        try:
            d_save = float(str(diametro).replace(",", "."))
            p_save = float(str(pacote).replace(",", "."))
            saved = save_official_calculation(
                {
                    "diametro_mm": d_save,
                    "pacote_mm": p_save,
                    "carcaca": carcaca,
                    "passo": passo,
                    "ligacao": ligacao,
                    "fio_principal": fio_eng or str(res.get("sugestao_fio_awg") or ""),
                    "espiras_principal": esp_eng or str(res.get("sugestao_espira") or ""),
                    "observacoes": "Salvo via Streamlit demo-calculo",
                }
            )
            st.success(f"Gravado no manifesto OFICIAL. SHA: {saved['sha256_arquivo'][:16]}…")
            _catalog.clear()
        except Exception as exc:
            st.error(f"Falha ao salvar: {exc}")


@maybe_fragment
def _demo_calculo_fragment() -> None:
    mrw_render_banner_zone()
    ctx = pop_page_ctx_pack().get("ctx")
    if ctx is None:
        return
    _render_stats_bar()
    _render_form(ctx)


def show(ctx) -> None:
    if not require_admin_access("Demo calculo (acervo oficial)", client=ctx.supabase):
        if st.button("Voltar para consulta", use_container_width=True):
            ctx.session.set_route(Route.CONSULTA)
            st.rerun()
        return
    stash_page_ctx(ctx)
    _demo_calculo_fragment()


def render(ctx) -> None:
    show(ctx)
