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
from services.motor_qualidade import MSG_CALCULO_SEM_HISTORICO_OFICINA
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
from engine.physics_audit import (
    MSG_B_ABORT,
    cenario_valido_para_painel_recomendado,
    scenario_passes_hard_physics_limits,
)
from page.demo_calculo_components import (
    render_form_block_close,
    render_form_block_open,
    render_input_panel_close,
    render_input_panel_open,
    render_mode_hint,
    render_verdict_banner,
)
from page.demo_calculo_ui import (
    MSG_PROJETO_INVIAVEL,
    close_dashboard_shell,
    cenario_valido_para_painel_recomendado,
    is_projeto_inviavel_nuclear,
    optimizer_has_cenarios,
    open_dashboard_shell,
    panel_title,
    projeto_fisicamente_aprovado,
    render_candidates_table,
    render_checklist,
    render_critical_alert,
    render_empty_report,
    render_hero,
    render_kpi_row,
    render_mermaid_dark,
    render_vision_manual_warning,
    resolve_cenario_recomendado_raw,
    resolve_recommended_optimizer_scenario,
    confidence_tier,
)
from engine.physics_audit import scenario_dict_passes_hard_physics_limits
from page.demo_calculo_motor_form import MotorWindingForm, render_motor_winding_form
from page.demo_calculo_validation import (
    parse_tensao_rede,
    primary_voltage_for_physics,
    validate_demo_submit,
    vision_needs_manual_fallback,
)


def _optional_float(raw: Any) -> float | None:
    s = str(raw or "").strip().replace(",", ".")
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _optional_int(raw: Any) -> int | None:
    s = str(raw or "").strip()
    if not s:
        return None
    try:
        return int(float(s.replace(",", ".")))
    except ValueError:
        return None


_DEMO_FORM_KEYS = (
    "demo_diam",
    "demo_pac",
    "demo_carc",
    "demo_tipo_bob",
    "demo_ranhuras",
    "demo_polos",
    "demo_tipo_motor",
    "demo_tensao",
    "demo_ligacao_trif",
    "demo_passo_principal",
    "demo_passo_auxiliar",
    "demo_fio",
    "demo_esp",
    "demo_fio_aux",
    "demo_esp_aux",
    "demo_capacitor_uf",
    "demo_modo_operacao",
    "demo_corrente_nom",
    "demo_potencia_cv",
    "demo_stator_images",
)


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
    for key in _DEMO_FORM_KEYS:
        st.session_state.pop(key, None)


def _apply_tensao_to_entrada(out: dict[str, Any], winding: MotorWindingForm) -> None:
    raw = _read_tensao_raw(winding)
    tensoes, display = parse_tensao_rede(raw)
    if raw:
        out["tensao_rede"] = display or raw
    if tensoes:
        calc_v = primary_voltage_for_physics(tensoes, tipo_motor=winding.tipo_motor)
        out["tensoes_v"] = tensoes
        out["tensao_v"] = float(calc_v)
        out["voltagem"] = float(calc_v)
        out["tensao_calculo_v"] = float(calc_v)


def _read_tensao_raw(winding: MotorWindingForm) -> str:
    """Lê tensão do session_state (fonte do widget) com fallback no dataclass."""
    from_state = str(st.session_state.get("demo_tensao") or "").strip()
    from_winding = str(winding.tensao or "").strip()
    return from_state or from_winding


def _entrada_from_form(
    *,
    d: float,
    p: float,
    carcaca: str,
    tipo_bob: str,
    n_ranh: int,
    n_polos: int | None,
    winding: MotorWindingForm,
    corrente_nominal_a: float | None = None,
    potencia_cv: float | None = None,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "diametro_mm": d,
        "pacote_mm": p,
        "carcaca": carcaca,
        "tipo_bobinagem": tipo_bob,
        "ranhuras": int(n_ranh),
        "polos": n_polos,
    }
    out.update(winding.as_entrada_extra())
    _apply_tensao_to_entrada(out, winding)
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
    res = dict(opt_res.base_suggestion or {})
    rec_id = str(opt_res.cenario_recomendado or "").strip()
    rec = None
    if rec_id:
        rec = next((c for c in opt_res.cenarios if c.cenario_id == rec_id), None)
    if rec is None and opt_res.cenarios:
        for c in opt_res.cenarios:
            if scenario_passes_hard_physics_limits(c):
                rec = c
                break
    if rec and scenario_passes_hard_physics_limits(rec):
        res["sugestao_espira"] = rec.espiras
        res["sugestao_fio_awg"] = rec.wire.awg
        res["sugestao_fio_texto"] = rec.fio_texto
        res["calculo_abortado"] = False
    else:
        res["sugestao_espira"] = None
        res["sugestao_fio_awg"] = None
        res["sugestao_fio_texto"] = ""
        res["calculo_abortado"] = True
        res["justificativa_tecnica"] = MSG_PROJETO_INVIAVEL
        res["validacao_magnetica"] = "ABORTADO"
    st.session_state["demo_calculo_result"] = res
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
    ranhuras: Any,
    polos: Any,
    carcaca: str,
    tipo_bob: str,
    winding: MotorWindingForm,
) -> dict[str, Any] | None:
    d = _optional_float(diametro)
    p = _optional_float(pacote)
    if d is None or p is None:
        st.warning("Informe diâmetro e pacote (mm) com valores numéricos.")
        return None
    if d <= 0 or p <= 0:
        st.warning("Diâmetro e pacote devem ser maiores que zero.")
        return None
    n_ranh = parse_ranhuras_for_calc(ranhuras, default=None)
    if n_ranh is None or n_ranh <= 0:
        st.warning("Informe o número de ranhuras.")
        return None
    n_polos = parse_polos_for_calc(polos, default=None)
    ok_req, req_msg = validate_required_motor_inputs(
        diametro_mm=d, pacote_mm=p, ranhuras=n_ranh, polos=n_polos
    )
    if not ok_req:
        st.warning(req_msg)
        return None
    esp_user = (
        parse_scalar(winding.espiras_principal.strip())
        if winding.espiras_principal.strip()
        else None
    )
    fio_user = (
        parse_awg_number(winding.fio_principal.strip())
        if winding.fio_principal.strip()
        else None
    )
    return {
        "d": d,
        "p": p,
        "n_ranh": n_ranh,
        "n_polos": n_polos,
        "carcaca": carcaca,
        "passo": winding.passo_principal.strip(),
        "passo_principal": winding.passo_principal.strip(),
        "passo_auxiliar": winding.passo_auxiliar.strip(),
        "tipo_bob": tipo_bob,
        "ligacao": winding.ligacao.strip(),
        "fio_eng": winding.fio_principal.strip(),
        "esp_eng": winding.espiras_principal.strip(),
        "esp_user": esp_user,
        "fio_user": fio_user,
        "winding": winding,
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
    passes_physics = cenario_valido_para_painel_recomendado(cen)
    score = int(cen.get("physics_confidence") or cen.get("confidence_score") or 0)
    tier = confidence_tier(score)
    show_star = recomendado and passes_physics and score > 0
    if show_star:
        st.markdown(
            '<span class="dt-badge dt-badge-ok">★ Cenário recomendado</span>',
            unsafe_allow_html=True,
        )
    elif recomendado and score <= 0:
        st.caption("Falha na auditoria física — sem recomendação (confiança 0%).")
    elif recomendado:
        st.caption("Cenário reprovado pela física — sem recomendação para bobina.")
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
    inviable: bool = False,
) -> None:
    if inviable or not calculation_ready_for_export(twin_data, opt_data, res):
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
    if not twin_data and not opt_data and not res:
        st.markdown('<div class="dt-report-panel">', unsafe_allow_html=True)
        render_empty_report(
            "Configure o motor à esquerda, envie fotos (modo caixa preta) "
            "e execute o cálculo para ver candidatos, FEM e score de confiança."
        )
        st.markdown("</div>", unsafe_allow_html=True)
        return

    opt_abc = optimizer_has_cenarios(opt_data)
    optimizer_session = isinstance(opt_data, dict) and bool(opt_data)
    cenario_recomendado = resolve_cenario_recomendado_raw(opt_data) if opt_abc else None
    cenario_aprovado = resolve_recommended_optimizer_scenario(opt_data) if opt_abc else None

    if opt_abc:
        is_inviavel = (
            is_projeto_inviavel_nuclear(cenario_recomendado)
            or cenario_aprovado is None
            or bool(res and res.get("calculo_abortado"))
        )
    elif optimizer_session and (res and res.get("calculo_abortado")):
        is_inviavel = True
    else:
        is_inviavel = False

    st.markdown('<div class="dt-report-panel">', unsafe_allow_html=True)

    if is_inviavel:
        entrada_banner = st.session_state.get("demo_calculo_entrada") or {}
        render_verdict_banner(
            aprovado=False,
            confianca_pct=0.0,
            espiras=entrada_banner.get("espiras_engenheiro") or "—",
            bitola=entrada_banner.get("fio_engenheiro") or "—",
            subtitulo="Ajuste parâmetros físicos ou bitola antes de bobinar.",
        )
        st.error(
            "🚨 PROJETO INVIÁVEL: Os limites físicos obrigatórios (Saturação Magnética ou "
            "Fator de Enchimento) foram excedidos."
        )
        st.info(
            "Nenhuma configuração pode ser recomendada para este estator. "
            "Ajuste os parâmetros físicos."
        )
        st.warning("Motor reprovado na auditoria física.")
        if res:
            just = (res.get("justificativa_tecnica") or "").strip()
            if just:
                st.markdown(just)
            elif res.get("alerta_risco"):
                st.warning(res.get("alerta_risco"))
        if cenario_recomendado:
            for alerta in cenario_recomendado.get("alertas") or []:
                st.error(str(alerta))
        entrada_inv = st.session_state.get("demo_calculo_entrada") or {}
        if isinstance(entrada_inv, dict) and entrada_inv:
            from page.demo_calculo_diagnostics import render_diagnostic_suite

            render_diagnostic_suite(
                entrada=entrada_inv,
                opt_data=opt_data,
                twin_data=twin_data,
                res=res,
                show_pdf_button=True,
            )
    else:
        if opt_abc and cenario_aprovado:
            conf = float(
                cenario_aprovado.get("physics_confidence")
                or cenario_aprovado.get("confidence_score")
                or 0
            )
            render_verdict_banner(
                aprovado=True,
                confianca_pct=conf,
                espiras=cenario_aprovado.get("espiras", "—"),
                bitola=cenario_aprovado.get("fio_texto")
                or cenario_aprovado.get("calibre_display")
                or "—",
                lt_mm=entrada_diag.get("pacote_mm") if (entrada_diag := st.session_state.get("demo_calculo_entrada") or {}) else None,
            )
        elif twin_data and twin_data.get("completo"):
            cand = (twin_data.get("candidatos") or [{}])[0]
            render_verdict_banner(
                aprovado=not twin_data.get("bloqueado"),
                confianca_pct=float(cand.get("confianca_pct") or 0),
                espiras=cand.get("espiras_por_bobina", "—"),
                bitola=cand.get("descricao", "—"),
            )

        panel_title("Relatório executivo")

        if opt_abc and cenario_aprovado:
            panel_title("Cenário recomendado (★)")
            render_kpi_row(
                espiras=cenario_aprovado.get("espiras", "—"),
                bitola=cenario_aprovado.get("fio_texto")
                or cenario_aprovado.get("calibre_display")
                or "—",
                confianca=int(
                    cenario_aprovado.get("physics_confidence")
                    or cenario_aprovado.get("confidence_score")
                    or 0
                ),
                ocupacao=cenario_aprovado.get("fator_ocupacao_ranhura"),
            )
            st.caption(
                f"Fonte: otimizador A/B/C — cenário **{cenario_aprovado.get('cenario_id')}** "
                f"(veto FEM + bitola por ff)."
            )

        if twin_data and not opt_abc and not optimizer_session:
            if twin_data.get("saturacao_abortada"):
                render_critical_alert(
                    MSG_B_ABORT,
                    b_tesla=twin_data.get("flux_density_b_t"),
                )
            if vision_needs_manual_fallback(twin_data.get("visao")):
                render_vision_manual_warning()
            modo_lbl = "Caixa preta" if twin_data.get("modo") == "caixa_preta" else "Auditoria"
            st.caption(
                f"Modo ativo: **{modo_lbl}** · Completo: **"
                f"{'Sim' if twin_data.get('completo') else 'Não'}**"
            )
            for cand in twin_data.get("candidatos") or []:
                for alerta in cand.get("alertas") or []:
                    if MSG_CALCULO_SEM_HISTORICO_OFICINA in str(alerta):
                        st.warning(alerta)
                        break
                else:
                    continue
                break
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

        if opt_abc:
            panel_title("Cenários A / B / C")
            tab_map = {
                "A": "A — Eficiência",
                "B": "B — Referência",
                "C": "C — Execução",
            }
            rec_id_effective = (
                str(cenario_aprovado.get("cenario_id")) if cenario_aprovado else ""
            )
            labels = []
            for cen in opt_data["cenarios"]:
                cid = str(cen.get("cenario_id", "B"))
                lbl = tab_map.get(cid, cid)
                cen_score = int(
                    cen.get("physics_confidence") or cen.get("confidence_score") or 0
                )
                if (
                    rec_id_effective
                    and cid == rec_id_effective
                    and cenario_valido_para_painel_recomendado(cen)
                    and cen_score > 0
                ):
                    lbl = f"{lbl} ★"
                labels.append(lbl)
            tabs = st.tabs(labels)
            for tab, cen in zip(tabs, opt_data["cenarios"]):
                with tab:
                    _render_scenario_card_compact(
                        cen,
                        recomendado=bool(
                            rec_id_effective
                            and str(cen.get("cenario_id")) == rec_id_effective
                        ),
                    )

        if res and projeto_fisicamente_aprovado(opt_data):
            st.caption(f"Validação: **{res.get('validation_status', '—')}**")
            if res.get("alerta_risco"):
                st.warning(res.get("alerta_risco"))
            if res.get("justificativa_tecnica") and not res.get("calculo_abortado"):
                st.info(res.get("justificativa_tecnica"))

        _render_ordem_servico_export(
            twin_data=twin_data,
            opt_data=opt_data,
            res=res,
            inviable=False,
        )

        entrada_diag = st.session_state.get("demo_calculo_entrada") or {}
        if isinstance(entrada_diag, dict) and entrada_diag:
            from page.demo_calculo_diagnostics import render_diagnostic_suite

            render_diagnostic_suite(
                entrada=entrada_diag,
                opt_data=opt_data,
                twin_data=twin_data,
                res=res,
            )

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
        render_input_panel_open(
            title="Entrada de dados do motor",
            subtitle="Geometria · bobinagem · elétrico",
        )

        if st.button(
            "Limpar dados / Novo cálculo",
            use_container_width=True,
            key="demo_btn_reset",
            help="Zera resultados e formulário de cálculo para testar outro motor sem F5.",
        ):
            _reset_demo_session()
            st.rerun()

        st.markdown('<div class="dt-mode-wrap">', unsafe_allow_html=True)
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
        st.markdown("</div>", unsafe_allow_html=True)
        render_mode_hint(modo_op)

        render_form_block_open("ESTATOR · GEOMETRIA")
        g1, g2, g3 = st.columns(3)
        with g1:
            diametro = st.text_input("Ø estator (mm)", placeholder="—", key="demo_diam")
        with g2:
            pacote = st.text_input("Pacote (mm)", placeholder="—", key="demo_pac")
        with g3:
            carcaca = st.text_input("Carcaça", placeholder="—", key="demo_carc")
        render_form_block_close()

        topo_opts = {"(Inferir)": ""}
        topo_opts.update(
            {label_tipo(k): k for k in TIPOS_UI_ORDER if k in TIPOS_BOBINAGEM and k != "DESCONHECIDO"}
        )
        tipo_bob = topo_opts[
            st.selectbox("Bobinagem", list(topo_opts.keys()), key="demo_tipo_bob")
        ]

        render_form_block_open("BOBINAGEM · MECÂNICA")
        g4, g5 = st.columns(2)
        with g4:
            ranhuras = st.text_input("Ranhuras *", placeholder="—", key="demo_ranhuras")
        with g5:
            polos = st.text_input("Polos (vazio = auto)", placeholder="—", key="demo_polos")
        render_form_block_close()

        winding = render_motor_winding_form()

        imagens_upload: list = []
        if modo_op == "Caixa preta — estator vazio (FEM + visão)":
            panel_title("Fotos do estator")
            imagens_upload = st.file_uploader(
                "HEIC / JPG / PNG — inclua régua ou paquímetro",
                type=["jpg", "jpeg", "png", "webp", "heic", "heif"],
                accept_multiple_files=True,
                key="demo_stator_images",
            )

        corrente_nominal_a: str | float | None = None
        potencia_cv: str | float | None = None
        if modo_op == "Auditoria — cálculo suspeito":
            panel_title("Dados elétricos (auditoria)")
            st.caption(
                "Informe corrente ou potência reais da placa para J e B corretos "
                "(ex.: 1,5 CV ≈ 3,5–4 A em 220 V)."
            )
            e1, e2 = st.columns(2)
            with e1:
                corrente_nominal_a = st.text_input(
                    "Corrente nominal (A)",
                    placeholder="—",
                    key="demo_corrente_nom",
                    help="Deixe vazio para estimar pela potência ou pelo ferro.",
                )
            with e2:
                potencia_cv = st.text_input(
                    "Potência (CV)",
                    placeholder="—",
                    key="demo_potencia_cv",
                )

        btn_label = (
            "Gerar 3 cenários (A/B/C)"
            if modo_op == "Acervo proporcional (3 cenários A/B/C)"
            else "Executar gêmeo digital"
        )
        run_calc = st.button(btn_label, type="primary", use_container_width=True)
        render_input_panel_close()

        with st.expander("System prompt IA (PINN)", expanded=False):
            st.code(get_agent_system_prompt(), language=None)

    with col_out:
        _render_report_panel(twin_data=twin_data, opt_data=opt_data, res=res)

    if run_calc:
        d_mm = _optional_float(diametro) or 0.0
        p_mm = _optional_float(pacote) or 0.0
        ranh_i = parse_ranhuras_for_calc(ranhuras, default=0) or 0
        polos_i = _optional_int(polos) or 0
        tensao_raw = _read_tensao_raw(winding)
        tensoes, _ = parse_tensao_rede(tensao_raw)
        tensao_v = (
            primary_voltage_for_physics(tensoes, tipo_motor=winding.tipo_motor)
            if tensoes
            else _optional_float(tensao_raw)
        )

        val_errors = validate_demo_submit(
            modo_op=modo_op,
            diametro_mm=d_mm,
            pacote_mm=p_mm,
            ranhuras=int(ranh_i),
            tensao_raw=tensao_raw,
            tensao_v=tensao_v,
            esp_eng=winding.espiras_engenheiro,
            fio_eng=winding.fio_engenheiro,
            polos=int(polos_i),
            has_stator_images=bool(imagens_upload),
            tipo_motor=winding.tipo_motor,
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
            tipo_bob=tipo_bob,
            winding=winding,
        )
        if not parsed:
            return

        corrente_in = _optional_float(corrente_nominal_a)
        pot_cv_in = _optional_float(potencia_cv)
        if modo_op == "Auditoria — cálculo suspeito" and not corrente_in and not pot_cv_in:
            pot_cv_in = 1.5

        entrada_twin = _entrada_from_form(
            d=parsed["d"],
            p=parsed["p"],
            carcaca=parsed["carcaca"],
            tipo_bob=parsed["tipo_bob"],
            n_ranh=parsed["n_ranh"],
            n_polos=parsed["n_polos"],
            winding=parsed["winding"],
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

        st.session_state.pop("demo_digital_twin", None)
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
            tipo_bob=parsed["tipo_bob"],
            n_ranh=parsed["n_ranh"],
            n_polos=parsed["n_polos"],
            winding=parsed["winding"],
        )
        _persist_demo_results(opt_res=opt_res, entrada=entrada)
        st.session_state["demo_calculo_entrada"] = entrada
        st.session_state.pop("demo_digital_twin", None)
        st.session_state.pop("demo_ordem_servico_html", None)
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
                    tipo_bob=tipo_bob,
                    winding=winding,
                )
                if parsed and opt_data and res:
                    entrada = _entrada_from_form(
                        d=parsed["d"],
                        p=parsed["p"],
                        carcaca=parsed["carcaca"],
                        tipo_bob=parsed["tipo_bob"],
                        n_ranh=parsed["n_ranh"],
                        n_polos=parsed["n_polos"],
                        winding=parsed["winding"],
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
                            "tipo_motor": winding.tipo_motor,
                            "passo": winding.passo_principal,
                            "passo_principal": winding.passo_principal,
                            "passo_auxiliar": winding.passo_auxiliar,
                            "ligacao": winding.ligacao,
                            "fio_principal": winding.fio_principal,
                            "espiras_principal": winding.espiras_principal,
                            "fio_auxiliar": winding.fio_auxiliar,
                            "espiras_auxiliar": winding.espiras_auxiliar,
                            "capacitor_uf": winding.capacitor_uf,
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
