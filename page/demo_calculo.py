#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Demo cálculo — Gêmeo Digital (UI industrial premium + motor PINN)."""

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
from saas.audit import record_calculation
from saas.auth_guard import require_gemelo_digital_access
from core.navigation import Route
from core.streamlit_perf import maybe_fragment, pop_page_ctx_pack, stash_page_ctx
from core.ui_feedback import mrw_render_banner_zone
from app.topologia_bobinagem import TIPOS_BOBINAGEM, TIPOS_UI_ORDER, label_tipo
from services.acervo_oficial_stats import load_acervo_stats
from services.demo_calculo_report import build_report_html
from services.ordem_servico_report import (
    build_ordem_servico_html,
    calculation_ready_for_export,
)
from services.digital_twin_engine import (
    run_auditoria,
    run_caixa_preta,
    twin_result_to_optimizer_payload,
)
from services.gemini_engineering_validator import get_agent_system_prompt
from engine.physics_audit import MSG_B_ABORT
from page.demo_calculo_ui import (
    close_dashboard_shell,
    open_dashboard_shell,
    panel_title,
    pick_primary_candidate,
    render_candidates_table,
    render_checklist,
    render_critical_alert,
    render_empty_report,
    render_hero,
    render_kpi_row,
    render_mermaid_dark,
    render_vision_manual_warning,
    confidence_tier,
)
from page.demo_calculo_validation import validate_demo_submit, vision_needs_manual_fallback


@st.dialog("Prévia do Relatório de Engenharia", width="large")
def _report_preview_dialog() -> None:
    html_doc = st.session_state.get("demo_calculo_report_html") or ""
    if not html_doc:
        st.warning("Relatório indisponível — recalcule e tente novamente.")
        if st.button("Fechar", use_container_width=True, key="demo_report_close_empty"):
            st.rerun()
        return
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


def _optimizer_session_payload(opt_res) -> dict[str, Any]:
    return {
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


_AUTH_KEYS_PRESERVE = frozenset(
    {
        "is_authenticated",
        "auth_user_id",
        "auth_user_email",
        "auth_user_profile",
        "auth_force_logged_out",
        "authentication_status",
        "username",
        "name",
        "logout",
        "route",
        "_supabase_client",
        "_runtime_client_mode",
        "_access_cache_key",
        "_access_cache_value",
        "user_plan",
        "user_id",
        "user_email",
        "access_token",
    }
)


def _reset_demo_session() -> None:
    """Novo motor na bancada — st.session_state.clear() preservando login."""
    preserved = {k: st.session_state[k] for k in _AUTH_KEYS_PRESERVE if k in st.session_state}
    st.session_state.clear()
    for k, v in preserved.items():
        st.session_state[k] = v


def _entrada_from_form(
    *,
    d: float,
    p: float,
    carcaca: str,
    passo: str,
    tipo_bob: str,
    ligacao: str,
    n_ranh: int,
    n_polos: int | None,
    fio_eng: str,
    esp_eng: str,
    tensao_v: float | None = None,
    corrente_nominal_a: float | None = None,
    potencia_cv: float | None = None,
) -> dict[str, Any]:
    out: dict[str, Any] = {
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
    if tensao_v is not None:
        out["tensao_v"] = float(tensao_v)
        out["voltagem"] = float(tensao_v)
    if corrente_nominal_a is not None and corrente_nominal_a > 0:
        out["corrente_nominal_a"] = float(corrente_nominal_a)
    if potencia_cv is not None and potencia_cv > 0:
        out["potencia_cv"] = float(potencia_cv)
    return out


def _run_demo_optimizer(
    *,
    d: float,
    p: float,
    n_ranh: int,
    n_polos: int | None,
    carcaca: str,
    passo: str,
    tipo_bob: str,
    ligacao: str,
    esp_user: float | None,
    fio_user: float | None,
    use_gemini: bool = True,
):
    motors, _ = _catalog()
    opt = WindingOptimizer(motors)
    return opt.optimize(
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
        use_gemini=use_gemini,
        top_k=5,
    )


def _persist_demo_results(*, opt_res, entrada: dict[str, Any]) -> None:
    st.session_state["demo_calculo_optimizer"] = _optimizer_session_payload(opt_res)
    st.session_state["demo_calculo_result"] = opt_res.base_suggestion or {}
    st.session_state["demo_calculo_entrada"] = entrada
    st.session_state.pop("demo_calculo_report_html", None)


def _refresh_demo_report(*, entrada: dict[str, Any], opt_data: dict[str, Any], res: dict[str, Any]) -> str:
    html_doc = build_report_html(entrada=entrada, result=res, optimizer=opt_data)
    st.session_state["demo_calculo_report_html"] = html_doc
    return html_doc


def _parse_form_inputs(
    *,
    diametro: str,
    pacote: str,
    ranhuras: int,
    polos: int,
    carcaca: str,
    passo: str,
    tipo_bob: str,
    ligacao: str,
    fio_eng: str,
    esp_eng: str,
) -> dict[str, Any] | None:
    try:
        d = float(str(diametro).replace(",", "."))
        p = float(str(pacote).replace(",", "."))
    except ValueError:
        st.warning("Informe diâmetro e pacote numéricos.")
        return None
    if d <= 0 or p <= 0:
        st.warning("Diâmetro e pacote devem ser maiores que zero.")
        return None
    n_ranh = parse_ranhuras_for_calc(ranhuras, default=36)
    n_polos = parse_polos_for_calc(polos)
    ok_req, req_msg = validate_required_motor_inputs(
        diametro_mm=d, pacote_mm=p, ranhuras=n_ranh, polos=n_polos
    )
    if not ok_req:
        st.warning(req_msg)
        return None
    esp_user = parse_scalar(str(esp_eng).strip()) if str(esp_eng).strip() else None
    fio_user = parse_awg_number(str(fio_eng).strip()) if str(fio_eng).strip() else None
    return {
        "d": d,
        "p": p,
        "n_ranh": n_ranh,
        "n_polos": n_polos,
        "carcaca": carcaca,
        "passo": passo,
        "tipo_bob": tipo_bob,
        "ligacao": ligacao,
        "fio_eng": fio_eng,
        "esp_eng": esp_eng,
        "esp_user": esp_user,
        "fio_user": fio_user,
    }


def _render_stats_compact() -> None:
    acervo = load_acervo_stats()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("OFICIAIS", acervo.get("oficial_manifest", 0))
    c2.metric("Índice", acervo.get("indexed_total", 0))
    c3.metric("Completos", acervo.get("file_complete", 0))
    c4.metric("Atualizado", (acervo.get("index_generated_at") or "—")[:10])
    if not Path(DEFAULT_DB).is_file():
        st.error("Índice ausente — rode `python scripts/index_for_search.py`.")


def _render_scenario_card_compact(cen: dict, *, recomendado: bool = False) -> None:
    score = int(cen.get("physics_confidence") or cen.get("confidence_score") or 0)
    tier = confidence_tier(score)
    if recomendado:
        st.markdown(
            f'<span class="dt-badge dt-badge-ok">★ Cenário recomendado</span>',
            unsafe_allow_html=True,
        )
    render_kpi_row(
        espiras=cen.get("espiras", "—"),
        bitola=cen.get("fio_texto") or cen.get("calibre_display") or "—",
        confianca=score,
        ocupacao=cen.get("fator_ocupacao_ranhura"),
    )
    if cen.get("desabilitado"):
        st.error("Cenário indisponível — calibre fora do intervalo seguro.")
    alt_par = cen.get("fio_alternativa_paralelo") or ""
    if alt_par and alt_par != cen.get("fio_texto"):
        st.info(f"Alternativa: {alt_par}")
    if tier == "red":
        st.error("Confiança baixa — revisar na bancada antes de bobinar.")
    for alerta in cen.get("alertas") or []:
        st.warning(alerta)


def _resolve_export_entrada(
    twin_data: dict[str, Any] | None,
) -> dict[str, Any]:
    stored = st.session_state.get("demo_calculo_entrada")
    if isinstance(stored, dict) and stored:
        return stored
    if twin_data and isinstance(twin_data.get("entrada"), dict):
        return twin_data["entrada"]
    return {}


def _render_ordem_servico_export(
    *,
    twin_data: dict[str, Any] | None,
    opt_data: dict[str, Any] | None,
    res: dict[str, Any] | None,
) -> None:
    if not calculation_ready_for_export(twin_data, opt_data, res):
        return
    entrada = _resolve_export_entrada(twin_data)
    st.divider()
    if st.button(
        "🖨️ Gerar Ordem de Serviço (PDF/Impressão)",
        type="secondary",
        use_container_width=True,
        key="demo_btn_ordem_servico",
    ):
        st.session_state["demo_ordem_servico_html"] = build_ordem_servico_html(
            entrada=entrada,
            twin_data=twin_data,
            opt_data=opt_data,
            res=res,
        )
        st.toast("Ordem de Serviço gerada — baixe o HTML ou use Ctrl+P.", icon="✅")
    html_os = st.session_state.get("demo_ordem_servico_html")
    if html_os:
        ref = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        st.download_button(
            "⬇️ Baixar Ordem de Serviço (.html)",
            data=html_os,
            file_name=f"ordem-servico-rebobinagem-{ref}.html",
            mime="text/html",
            use_container_width=True,
            key="demo_download_ordem_servico",
            help="Abra o arquivo no navegador e use Imprimir → Salvar como PDF.",
        )
        with st.expander("Prévia da Ordem de Serviço", expanded=False):
            components.html(html_os, height=520, scrolling=True)


def _render_report_panel(
    *,
    twin_data: dict[str, Any] | None,
    opt_data: dict[str, Any] | None,
    res: dict[str, Any] | None,
) -> None:
    """Painel direito — relatório executivo e KPIs."""
    st.markdown('<div class="dt-report-panel">', unsafe_allow_html=True)
    panel_title("Relatório executivo")

    if not twin_data and not opt_data and not res:
        render_empty_report(
            "Configure o motor à esquerda, envie fotos (modo caixa preta) "
            "e execute o cálculo para ver candidatos, FEM e score de confiança."
        )
        st.markdown("</div>", unsafe_allow_html=True)
        return

    esp, bitola, conf, occ, kpi_tier = pick_primary_candidate(twin_data, opt_data)
    render_kpi_row(
        espiras=esp,
        bitola=bitola,
        confianca=conf,
        ocupacao=occ,
        force_tier=kpi_tier,
    )

    if twin_data:
        if twin_data.get("saturacao_abortada"):
            render_critical_alert(
                MSG_B_ABORT,
                b_tesla=twin_data.get("flux_density_b_t"),
            )
        if vision_needs_manual_fallback(twin_data.get("visao")):
            render_vision_manual_warning()
        modo_lbl = "Caixa preta" if twin_data.get("modo") == "caixa_preta" else "Auditoria"
        st.caption(f"Modo ativo: **{modo_lbl}** · Completo: **{'Sim' if twin_data.get('completo') else 'Não'}**")
        if twin_data.get("bloqueado"):
            render_checklist(twin_data.get("checklist") or [])
        md = twin_data.get("relatorio_markdown") or ""
        if md and twin_data.get("completo"):
            st.markdown(md)
        cands = twin_data.get("candidatos") or []
        if cands:
            panel_title("Candidatos otimizados")
            render_candidates_table(cands)
        mv = twin_data.get("mermaid_validacao")
        ml = twin_data.get("mermaid_ligacao")
        if mv:
            render_mermaid_dark(mv, height=320, title="Fluxo de validação física")
        if ml:
            render_mermaid_dark(ml, height=220, title="Esquema de ligação")

    if opt_data and opt_data.get("cenarios"):
        panel_title("Cenários A / B / C")
        rec_id = str(opt_data.get("cenario_recomendado") or "B")
        tab_map = {
            "A": "A — Eficiência",
            "B": "B — Referência ★",
            "C": "C — Execução",
        }
        labels = []
        for cen in opt_data["cenarios"]:
            cid = str(cen.get("cenario_id", "B"))
            labels.append(tab_map.get(cid, cid))
        tabs = st.tabs(labels)
        for tab, cen in zip(tabs, opt_data["cenarios"]):
            with tab:
                _render_scenario_card_compact(
                    cen, recomendado=str(cen.get("cenario_id")) == rec_id
                )

    if res and not twin_data:
        st.caption(f"Validação: **{res.get('validation_status', '—')}**")
        if res.get("alerta_risco"):
            st.warning(res.get("alerta_risco"))
        if res.get("justificativa_tecnica"):
            st.info(res.get("justificativa_tecnica"))

    _render_ordem_servico_export(twin_data=twin_data, opt_data=opt_data, res=res)

    st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("Dados de auditoria", expanded=False):
        if twin_data:
            st.json({"visao": twin_data.get("visao"), "gemini": twin_data.get("gemini")})
        if opt_data:
            st.json(
                {
                    "n_referencias": opt_data.get("n_referencias"),
                    "media_historica": opt_data.get("media_historica_espiras"),
                    "media_proporcional": opt_data.get("media_proporcional_espiras"),
                    "magnetic_gate": opt_data.get("magnetic_sanity_gate_active"),
                }
            )
        if res:
            st.json({"validation": res.get("validation_status"), "modo": res.get("modo_processamento")})

    with st.expander("Logs de processamento", expanded=False):
        if twin_data and twin_data.get("visao", {}).get("preprocess_meta"):
            st.write("Pré-processamento de imagens")
            st.json(twin_data["visao"]["preprocess_meta"])
        if opt_data:
            for cen in opt_data.get("cenarios") or []:
                st.caption(f"Cenário {cen.get('cenario_id')}")
                st.json(
                    {
                        "slot_fill_units": cen.get("slot_fill_units"),
                        "slot_fill_limite": cen.get("slot_fill_limite"),
                        "J": cen.get("current_density_j"),
                        "ff": cen.get("fill_factor_ff"),
                        "flux_idx": cen.get("densidade_fluxo_indice"),
                    }
                )


def _render_form(ctx) -> None:
    open_dashboard_shell()
    render_hero()

    with st.expander("Status do acervo oficial", expanded=False):
        _render_stats_compact()

    twin_data = st.session_state.get("demo_digital_twin")
    opt_data = st.session_state.get("demo_calculo_optimizer")
    res = st.session_state.get("demo_calculo_result")

    col_in, col_out = st.columns([2, 3], gap="large")

    with col_in:
        st.markdown('<div class="dt-panel">', unsafe_allow_html=True)
        panel_title("Entrada e visão")

        if st.button(
            "Limpar dados / Novo cálculo",
            use_container_width=True,
            key="demo_btn_reset",
            help="Zera resultados e formulário de cálculo para testar outro motor sem F5.",
        ):
            _reset_demo_session()
            st.rerun()

        modo_op = st.radio(
            "Modo de operação",
            options=[
                "Acervo proporcional (3 cenários A/B/C)",
                "Caixa preta — estator vazio (FEM + visão)",
                "Auditoria — cálculo suspeito",
            ],
            key="demo_modo_operacao",
            label_visibility="collapsed",
        )
        st.caption(f"**{modo_op}**")

        st.session_state.setdefault("demo_ranhuras", 24)
        st.session_state.setdefault("demo_polos", 2)

        g1, g2, g3 = st.columns(3)
        with g1:
            diametro = st.number_input(
                "Ø estator (mm)",
                min_value=20.0,
                max_value=500.0,
                value=80.0,
                step=1.0,
                key="demo_diam",
            )
        with g2:
            pacote = st.number_input(
                "Pacote (mm)",
                min_value=5.0,
                max_value=800.0,
                value=70.0,
                step=1.0,
                key="demo_pac",
            )
        with g3:
            carcaca = st.text_input("Carcaça", value="80A", key="demo_carc")

        topo_opts = {"(Inferir)": ""}
        topo_opts.update(
            {label_tipo(k): k for k in TIPOS_UI_ORDER if k in TIPOS_BOBINAGEM and k != "DESCONHECIDO"}
        )
        tipo_bob = topo_opts[
            st.selectbox("Bobinagem", list(topo_opts.keys()), key="demo_tipo_bob")
        ]

        g4, g5, g6 = st.columns(3)
        with g4:
            ranhuras = st.number_input(
                "Ranhuras *",
                min_value=1,
                max_value=120,
                step=1,
                key="demo_ranhuras",
            )
        with g5:
            polos = st.number_input(
                "Polos (0=auto)",
                min_value=0,
                max_value=12,
                step=2,
                key="demo_polos",
            )
        with g6:
            ligacao = st.text_input("Ligação", value="Estrela", key="demo_lig")

        tensao = st.number_input(
            "Tensão rede (V) *",
            min_value=110,
            max_value=480,
            value=220,
            step=10,
            key="demo_tensao",
            help="Obrigatório para FEM, densidade J e execução do gêmeo digital.",
        )

        imagens_upload: list = []
        if modo_op == "Caixa preta — estator vazio (FEM + visão)":
            panel_title("Fotos do estator")
            imagens_upload = st.file_uploader(
                "HEIC / JPG / PNG — inclua régua ou paquímetro",
                type=["jpg", "jpeg", "png", "webp", "heic", "heif"],
                accept_multiple_files=True,
                key="demo_stator_images",
            )

        passo = st.text_input(
            "Passo (opcional)",
            value="1:7",
            key="demo_passo",
            help="Camada dupla: use 4-6-8 ou 1:4-6-8 conforme a bobina.",
        )

        corrente_nominal_a: float | None = None
        potencia_cv: float | None = None
        if modo_op == "Auditoria — cálculo suspeito":
            panel_title("Dados elétricos (auditoria)")
            st.caption(
                "Informe corrente ou potência reais da placa para J e B corretos "
                "(ex.: 1,5 CV ≈ 3,5–4 A em 220 V)."
            )
            e1, e2 = st.columns(2)
            with e1:
                corrente_nominal_a = st.number_input(
                    "Corrente nominal (A)",
                    min_value=0.0,
                    max_value=200.0,
                    value=0.0,
                    step=0.1,
                    key="demo_corrente_nom",
                    help="0 = estimar pela potência ou pelo ferro.",
                )
            with e2:
                potencia_cv = st.number_input(
                    "Potência (CV)",
                    min_value=0.0,
                    max_value=500.0,
                    value=0.0,
                    step=0.1,
                    key="demo_potencia_cv",
                    help="0 = usar 1,5 CV implícito só se corrente também estiver vazia.",
                )

        panel_title("Validação / auditoria")
        v1, v2 = st.columns(2)
        with v1:
            fio_eng = st.text_input("Fio AWG", value="19", key="demo_fio")
        with v2:
            esp_eng = st.text_input("Espiras", value="45", key="demo_esp")

        btn_label = (
            "Gerar 3 cenários (A/B/C)"
            if modo_op == "Acervo proporcional (3 cenários A/B/C)"
            else "Executar gêmeo digital"
        )
        run_calc = st.button(btn_label, type="primary", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        with st.expander("System prompt IA (PINN)", expanded=False):
            st.code(get_agent_system_prompt(), language=None)

    with col_out:
        _render_report_panel(twin_data=twin_data, opt_data=opt_data, res=res)

    if run_calc:
        val_errors = validate_demo_submit(
            modo_op=modo_op,
            diametro_mm=float(diametro),
            pacote_mm=float(pacote),
            ranhuras=int(ranhuras),
            tensao_v=float(tensao) if tensao else None,
            esp_eng=esp_eng,
            fio_eng=fio_eng,
            polos=int(polos),
            has_stator_images=bool(imagens_upload),
        )
        if val_errors:
            for err in val_errors:
                st.toast(err, icon="⚠️")
            st.error(val_errors[0])
            if len(val_errors) > 1:
                for err in val_errors[1:]:
                    st.warning(err)
            return

        parsed = _parse_form_inputs(
            diametro=str(diametro),
            pacote=str(pacote),
            ranhuras=ranhuras,
            polos=polos,
            carcaca=carcaca,
            passo=passo,
            tipo_bob=tipo_bob,
            ligacao=ligacao,
            fio_eng=fio_eng,
            esp_eng=esp_eng,
        )
        if not parsed:
            return

        corrente_in = float(corrente_nominal_a) if corrente_nominal_a and corrente_nominal_a > 0 else None
        pot_cv_in = float(potencia_cv) if potencia_cv and potencia_cv > 0 else None
        if modo_op == "Auditoria — cálculo suspeito" and not corrente_in and not pot_cv_in:
            pot_cv_in = 1.5

        entrada_twin = _entrada_from_form(
            d=parsed["d"],
            p=parsed["p"],
            carcaca=parsed["carcaca"],
            passo=parsed["passo"],
            tipo_bob=parsed["tipo_bob"],
            ligacao=ligacao,
            n_ranh=parsed["n_ranh"],
            n_polos=parsed["n_polos"],
            fio_eng=parsed["fio_eng"],
            esp_eng=parsed["esp_eng"],
            tensao_v=float(tensao),
            corrente_nominal_a=corrente_in,
            potencia_cv=pot_cv_in,
        )

        if modo_op == "Caixa preta — estator vazio (FEM + visão)":
            with st.spinner("Visão + FEM + candidatos…"):
                twin = run_caixa_preta(
                    entrada_twin,
                    images=list(imagens_upload or []),
                    use_vision=bool(imagens_upload),
                )
            st.session_state["demo_digital_twin"] = twin_result_to_optimizer_payload(twin)
            st.session_state["demo_calculo_entrada"] = entrada_twin
            st.session_state.pop("demo_calculo_optimizer", None)
            st.session_state.pop("demo_calculo_result", None)
            st.session_state.pop("demo_ordem_servico_html", None)
            record_calculation(
                modo=twin.modo or "caixa_preta",
                entrada=entrada_twin,
                resultado_resumo={
                    "bloqueado": twin.bloqueado,
                    "saturacao_abortada": twin.saturacao_abortada,
                    "candidatos": len(twin.candidatos or []),
                },
            )
            st.rerun()

        if modo_op == "Auditoria — cálculo suspeito":
            with st.spinner("Auditoria física…"):
                twin = run_auditoria(entrada_twin, use_gemini=True)
            st.session_state["demo_digital_twin"] = twin_result_to_optimizer_payload(twin)
            st.session_state["demo_calculo_entrada"] = entrada_twin
            st.session_state.pop("demo_calculo_optimizer", None)
            st.session_state.pop("demo_calculo_result", None)
            st.session_state.pop("demo_ordem_servico_html", None)
            record_calculation(
                modo=twin.modo or "auditoria",
                entrada=entrada_twin,
                resultado_resumo={
                    "bloqueado": twin.bloqueado,
                    "gemini": bool(twin.gemini_auditoria),
                    "candidatos": len(twin.candidatos or []),
                },
            )
            st.rerun()

        try:
            with st.spinner("Otimizando A/B/C…"):
                opt_res = _run_demo_optimizer(
                    d=parsed["d"],
                    p=parsed["p"],
                    n_ranh=parsed["n_ranh"],
                    n_polos=parsed["n_polos"],
                    carcaca=parsed["carcaca"],
                    passo=parsed["passo"],
                    tipo_bob=parsed["tipo_bob"],
                    ligacao=parsed["ligacao"],
                    esp_user=parsed["esp_user"],
                    fio_user=parsed["fio_user"],
                )
        except FileNotFoundError as exc:
            st.error(str(exc))
            return
        if opt_res.validation_status == "INCOMPLETO" or not opt_res.cenarios:
            st.error(opt_res.validation_message or "Cálculo bloqueado.")
            return
        entrada = _entrada_from_form(
            d=parsed["d"],
            p=parsed["p"],
            carcaca=parsed["carcaca"],
            passo=parsed["passo"],
            tipo_bob=parsed["tipo_bob"],
            ligacao=ligacao,
            n_ranh=parsed["n_ranh"],
            n_polos=parsed["n_polos"],
            fio_eng=parsed["fio_eng"],
            esp_eng=parsed["esp_eng"],
        )
        _persist_demo_results(opt_res=opt_res, entrada=entrada)
        entrada["tensao_v"] = float(tensao)
        st.session_state["demo_calculo_entrada"] = entrada
        st.session_state.pop("demo_digital_twin", None)
        st.session_state.pop("demo_ordem_servico_html", None)
        st.rerun()

    # Ações secundárias (abaixo do layout principal)
    if opt_data or res:
        st.divider()
        a1, a2, a3 = st.columns(3)
        with a1:
            if st.button("Visualizar relatório A4", use_container_width=True, key="demo_btn_rel"):
                parsed = _parse_form_inputs(
                    diametro=str(diametro),
                    pacote=str(pacote),
                    ranhuras=ranhuras,
                    polos=polos,
                    carcaca=carcaca,
                    passo=passo,
                    tipo_bob=tipo_bob,
                    ligacao=ligacao,
                    fio_eng=fio_eng,
                    esp_eng=esp_eng,
                )
                if parsed and opt_data and res:
                    entrada = _entrada_from_form(
                        d=parsed["d"],
                        p=parsed["p"],
                        carcaca=parsed["carcaca"],
                        passo=parsed["passo"],
                        tipo_bob=parsed["tipo_bob"],
                        ligacao=ligacao,
                        n_ranh=parsed["n_ranh"],
                        n_polos=parsed["n_polos"],
                        fio_eng=parsed["fio_eng"],
                        esp_eng=parsed["esp_eng"],
                    )
                    _refresh_demo_report(entrada=entrada, opt_data=opt_data, res=res)
                    st.session_state["demo_open_report_dialog"] = True
                    st.rerun()
        with a2:
            if opt_data and opt_data.get("magnetic_sanity_gate_active"):
                st.warning(MSG_MAGNETIC_GATE_HIST_OVERRIDE[:80] + "…")
        with a3:
            if st.button("Salvar cálculo oficial", use_container_width=True):
                from app.oficial_engine import save_official_calculation

                try:
                    saved = save_official_calculation(
                        {
                            "diametro_mm": float(str(diametro).replace(",", ".")),
                            "pacote_mm": float(str(pacote).replace(",", ".")),
                            "carcaca": carcaca,
                            "passo": passo,
                            "ligacao": ligacao,
                            "fio_principal": fio_eng,
                            "espiras_principal": esp_eng,
                            "observacoes": "Salvo via Gêmeo Digital",
                        }
                    )
                    st.success(f"Gravado. SHA: {saved['sha256_arquivo'][:16]}…")
                    _catalog.clear()
                except Exception as exc:
                    st.error(str(exc))

    if st.session_state.pop("demo_open_report_dialog", False):
        if st.session_state.get("demo_calculo_report_html"):
            _report_preview_dialog()

    # Mensagens de engenharia (compactas)
    if opt_data:
        with st.expander("Notas do motor de projetos", expanded=False):
            if opt_data.get("tipo_foi_inferido") and opt_data.get("explicacao_tipo"):
                st.info(opt_data["explicacao_tipo"])
            if opt_data.get("calculo_baseado_em"):
                st.caption(opt_data["calculo_baseado_em"])
            if opt_data.get("usa_validacao_usuario"):
                st.success(
                    f"Validação usuário: {opt_data.get('espiras_validacao_usuario')} espiras (Constante K)"
                )
            if opt_data.get("cenario_a_suprimido"):
                st.warning("Cenário A suprimido — use o B como referência.")

    close_dashboard_shell()


@maybe_fragment
def _demo_calculo_fragment() -> None:
    mrw_render_banner_zone()
    ctx = pop_page_ctx_pack().get("ctx")
    if ctx is None:
        return
    _render_form(ctx)


def show(ctx) -> None:
    if not require_gemelo_digital_access(
        "Demo calculo (acervo oficial)",
        client=ctx.supabase,
    ):
        if st.button("Voltar para consulta", use_container_width=True):
            ctx.session.set_route(Route.CONSULTA)
            st.rerun()
        return
    stash_page_ctx(ctx)
    _demo_calculo_fragment()


def render(ctx) -> None:
    show(ctx)
