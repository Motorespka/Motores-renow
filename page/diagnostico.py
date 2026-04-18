from __future__ import annotations

import json
import math
from datetime import datetime
from typing import Any, Dict, List

import streamlit as st

from components.laudo_pro import render_laudo_tecnico
from core.access_control import is_admin_user, require_paid_access
from core.development_mode import is_dev_mode
from core.feature_flags import get_feature_flags
from core.user_identity import resolve_current_user_identity
from services.laudo_pro import build_laudo_tecnico, build_wa_link, format_whatsapp_full, format_whatsapp_summary
from services.oficina_parser import (
    build_normalized_from_motor_row,
    normalize_extracted_data,
    to_motores_schema_payload,
)
from services.oficina_runtime import diagnostico_motor_oficina_readonly, resumir_diagnostico_oficina
from services.motor_inteligencia.batch_review import build_batch_review_report
from services.motor_inteligencia.serialization import prepare_fastapi_batch_payload
from services.supabase_data import clear_motores_cache, fetch_motor_by_id_cached, fetch_motores_cached


def _estimate_current(cv: float, tensao: float, rendimento: float, fp: float, fases: str) -> float:
    if cv <= 0 or tensao <= 0:
        return 0.0

    watts = cv * 735.5
    rendimento = max(0.1, min(rendimento, 1.0))
    fp = max(0.1, min(fp, 1.0))

    if fases == "Monofasico":
        return watts / (tensao * rendimento * fp)
    return watts / (math.sqrt(3) * tensao * rendimento * fp)


def _to_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip().startswith("{"):
        try:
            return json.loads(value)
        except Exception:
            return {}
    return {}


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _load_motor_technical_payload(motor_row: Dict[str, Any]) -> Dict[str, Any]:
    data = _to_dict(motor_row.get("dados_tecnicos_json") or motor_row.get("leitura_gemini_json"))
    if not data:
        data = build_normalized_from_motor_row(motor_row)
    return normalize_extracted_data(data)


def _build_diag_snapshot(motor_id: Any, dados_placa: Dict[str, Any], avisos: List[str], alertas: List[str], calculos: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "data": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "motor_id": motor_id,
        "usuario": _to_text(st.session_state.get("auth_user_email") or st.session_state.get("auth_user_id")),
        "dados_placa": dados_placa or {},
        "avisos": avisos or [],
        "alertas_validacao": alertas or [],
        "calculos_aplicados": calculos or {},
        "modo": "copia",
    }


def _save_snapshot_copy(snapshot: Dict[str, Any]) -> None:
    key = "diagnostico_copias"
    copies = st.session_state.get(key)
    if not isinstance(copies, list):
        copies = []
    copies.append(snapshot)
    st.session_state[key] = copies[-60:]


def _build_laudo_raw_payload(
    *,
    normalized: Dict[str, Any],
    dados_placa: Dict[str, Any],
    avisos: List[str],
    alertas_validacao: List[str],
    resultado_pos: Dict[str, Any],
) -> Dict[str, Any]:
    motor = normalized.get("motor") if isinstance(normalized.get("motor"), dict) else {}
    mecanica = normalized.get("mecanica") if isinstance(normalized.get("mecanica"), dict) else {}
    principal = normalized.get("bobinagem_principal") if isinstance(normalized.get("bobinagem_principal"), dict) else {}

    resumo = "Diagnostico preliminar sem alertas criticos."
    if avisos or alertas_validacao:
        resumo = " / ".join((avisos + alertas_validacao)[:4])

    acoes: List[str] = []
    for aviso in avisos:
        txt = _to_text(aviso)
        if txt:
            acoes.append(f"Revisar: {txt}")
    if not acoes:
        acoes.append("Validar em bancada antes de liberar para operacao final.")

    return {
        "fabricante": dados_placa.get("marca") or motor.get("marca"),
        "modelo": dados_placa.get("modelo") or motor.get("modelo"),
        "potencia": dados_placa.get("potencia") or motor.get("potencia"),
        "rpm": dados_placa.get("rpm") or motor.get("rpm"),
        "tensao": dados_placa.get("tensao") or motor.get("tensao"),
        "corrente": dados_placa.get("corrente") or motor.get("corrente"),
        "polos": dados_placa.get("polos") or motor.get("polos"),
        "frequencia": dados_placa.get("frequencia") or motor.get("frequencia"),
        "fase": dados_placa.get("fases") or motor.get("fases"),
        "carcaca": mecanica.get("carcaca"),
        "status_geral": _to_text(resultado_pos.get("status")) or "Diagnostico preliminar",
        "nivel_confianca": "Conferencia recomendada",
        "resumo_executivo": resumo,
        "pontos_atencao": (avisos + alertas_validacao)[:8],
        "analise_bobinagem": _to_text(principal.get("observacoes") or principal.get("ligacao")),
        "analise_tensao_corrente": (
            f"Tensao: {_to_text(dados_placa.get('tensao') or motor.get('tensao'))} | "
            f"Corrente: {_to_text(dados_placa.get('corrente') or motor.get('corrente'))}"
        ),
        "analise_compatibilidade": "Compatibilidade depende de conferencia final em bancada.",
        "analise_incoerencias": ", ".join(alertas_validacao[:4]) if alertas_validacao else "Sem incoerencias adicionais.",
        "acoes_recomendadas": acoes[:5],
    }


def _render_laudo_whatsapp_panel(laudo) -> None:
    flags = get_feature_flags()
    dev_mode = is_dev_mode()
    if not (flags.enable_whatsapp_send or dev_mode):
        return

    st.markdown("### Envio via WhatsApp (sem armazenamento de numero)")
    st.info("O numero informado para envio via WhatsApp nao sera armazenado na plataforma.")

    with st.form("diagnostico_wa_tmp_form", clear_on_submit=True):
        numero_tmp = st.text_input("Digite o numero de WhatsApp", value="", key="diagnostico_wa_tmp_numero")
        formato = st.radio("Formato da mensagem", ["Resumo", "Completo"], horizontal=True, key="diagnostico_wa_tmp_format")
        gerar = st.form_submit_button("Gerar link de envio", use_container_width=True)
        if gerar:
            if not numero_tmp.strip():
                st.warning("Informe um numero para gerar o link.")
            else:
                msg = format_whatsapp_summary(laudo) if formato == "Resumo" else format_whatsapp_full(laudo)
                wa_link = build_wa_link(numero_tmp, msg)
                st.link_button("Abrir WhatsApp", wa_link, use_container_width=True)
                st.code(msg, language="text")
                st.caption("Numero de contato nao e salvo em banco, cache persistente ou analytics do sistema.")
        st.session_state.pop("diagnostico_wa_tmp_numero", None)


def _apply_diagnostico_to_motor(ctx, motor_id: Any, normalized: Dict[str, Any], snapshot: Dict[str, Any]) -> None:
    data = normalize_extracted_data(normalized or {})
    oficina = data.get("oficina")
    if not isinstance(oficina, dict):
        oficina = {}

    oficina["dados_placa"] = snapshot.get("dados_placa") or {}
    oficina["diagnostico"] = {
        "avisos": snapshot.get("avisos") or [],
        "alertas_validacao": snapshot.get("alertas_validacao") or [],
        "fonte": "diagnostico_manual_admin",
        "data": snapshot.get("data") or datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    }
    oficina["calculos_aplicados"] = snapshot.get("calculos_aplicados") or {}

    historico = oficina.get("historico_tecnico")
    if not isinstance(historico, list):
        historico = []
    historico.append(
        {
            "data": snapshot.get("data") or datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            "evento": "diagnostico_admin_aplicado",
            "resumo": "Diagnostico aplicado ao motor pelo painel de diagnostico",
            "payload": {
                "avisos": snapshot.get("avisos") or [],
                "alertas_validacao": snapshot.get("alertas_validacao") or [],
            },
        }
    )
    oficina["historico_tecnico"] = historico[-60:]
    data["oficina"] = oficina

    payload = {
        "dados_tecnicos_json": data,
        "leitura_gemini_json": data,
    }
    try:
        ctx.supabase.table("motores").update(payload).eq("id", motor_id).execute()
    except Exception:
        schema_payload = to_motores_schema_payload(data, image_paths=[], image_names=[])
        ctx.supabase.table("motores").update(schema_payload).eq("id", motor_id).execute()
    clear_motores_cache()


def _render_real_diagnosis(ctx) -> None:
    admin_user = is_admin_user()
    st.markdown("### Motor da Oficina")
    with st.expander("Ferramentas", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Recarregar lista (limpar cache)", use_container_width=True, key="diag_refresh_motores"):
                clear_motores_cache()
                st.rerun()
        with c2:
            st.caption("Dica: use o filtro abaixo para achar o motor mais rápido.")
    try:
        motores = fetch_motores_cached(ctx.supabase)
    except Exception as exc:
        st.warning(f"Nao foi possivel carregar motores para diagnostico: {exc}")
        return

    if not motores:
        st.info("Nenhum motor cadastrado ainda para diagnostico real.")
        return

    busca = st.text_input(
        "Buscar motor (ID, marca, modelo)",
        value="",
        key="diag_busca_motor",
        help="Filtra a lista local carregada para facilitar a selecao.",
    ).strip().lower()

    options: List[tuple[str, Any]] = []
    for row in motores:
        motor_id = row.get("id") if row.get("id") not in (None, "") else row.get("Id")
        if motor_id in (None, ""):
            continue
        marca = _to_text(row.get("marca") or row.get("Marca")) or "-"
        modelo = _to_text(row.get("modelo") or row.get("Modelo")) or "-"
        label = f"{marca} | {modelo} | #{motor_id}"
        if busca:
            hay = f"{marca} {modelo} {motor_id}".lower()
            if busca not in hay:
                continue
        options.append((label, motor_id))

    if not options:
        st.info("Nenhum motor encontrado com o filtro atual.")
        return

    current_id = ctx.session.selected_motor_id
    option_ids = [oid for _, oid in options]
    default_idx = option_ids.index(current_id) if current_id in option_ids else 0
    selected_label = st.selectbox("Selecione o motor para diagnostico", [lbl for lbl, _ in options], index=default_idx)
    selected_id = next(oid for lbl, oid in options if lbl == selected_label)

    motor = fetch_motor_by_id_cached(ctx.supabase, selected_id)
    if not motor:
        st.warning("Motor selecionado nao encontrado.")
        return

    normalized = _load_motor_technical_payload(motor)
    resumo = resumir_diagnostico_oficina(normalized)
    fallback = diagnostico_motor_oficina_readonly(normalized)

    dados_placa = resumo.get("dados_placa") or fallback.get("dados_placa") or {}
    avisos = resumo.get("avisos") or fallback.get("avisos") or []
    alertas_validacao = resumo.get("alertas_validacao") or fallback.get("alertas_validacao") or []
    calculos = normalized.get("oficina", {}).get("calculos_aplicados") if isinstance(normalized.get("oficina"), dict) else {}
    if not calculos:
        calculos = fallback.get("calculos_aplicados") or {}
    resultado_pos = resumo.get("resultado_pos_servico") or {}
    historico = resumo.get("historico_tecnico") or []

    c1, c2, c3 = st.columns(3)
    c1.metric("Marca", _to_text(dados_placa.get("marca")) or "-")
    c2.metric("Modelo", _to_text(dados_placa.get("modelo")) or "-")
    c3.metric("Status pos-servico", _to_text(resultado_pos.get("status")) or "Em acompanhamento")

    with st.expander("Camada técnica Moto-Renow (read-only)", expanded=False):
        from components.motor_inteligencia_panel import render_motor_inteligencia_panel

        render_motor_inteligencia_panel(motor, key_prefix=f"diag_intel_{selected_id}")

    st.markdown("#### Diagnostico atual")
    if avisos:
        for aviso in avisos:
            st.write(f"- {aviso}")
    else:
        st.write("- Sem avisos registrados.")

    st.markdown("#### Alertas de validacao")
    if alertas_validacao:
        for alerta in alertas_validacao:
            st.write(f"- {alerta}")
    else:
        st.write("- Sem alertas adicionais.")

    with st.expander("Calculos aplicados"):
        st.json(calculos or {}, expanded=False)

    with st.expander("Historico tecnico acumulado"):
        if historico:
            for item in reversed(historico[-12:]):
                data = _to_text(item.get("data")) or "-"
                evento = _to_text(item.get("evento")) or "-"
                resumo_item = _to_text(item.get("resumo")) or "-"
                st.write(f"- {data} | {evento} | {resumo_item}")
        else:
            st.write("Sem historico tecnico registrado.")

    snapshot = _build_diag_snapshot(
        motor_id=selected_id,
        dados_placa=dados_placa,
        avisos=avisos,
        alertas=alertas_validacao,
        calculos=calculos,
    )

    st.divider()
    if admin_user:
        st.caption("Modo completo: voce pode salvar copia e aplicar diagnostico no motor.")
    else:
        st.caption("Modo copia: o diagnostico nao altera motores.")

    if admin_user:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Salvar copia do diagnostico", use_container_width=True, key=f"diag_copy_{selected_id}"):
                _save_snapshot_copy(snapshot)
                st.success("Copia salva apenas para consulta.")
        with c2:
            if st.button("Aplicar diagnostico ao motor", use_container_width=True, key=f"diag_apply_{selected_id}"):
                try:
                    _apply_diagnostico_to_motor(ctx, selected_id, normalized, snapshot)
                    st.success("Diagnostico aplicado ao motor com sucesso.")
                except Exception as exc:
                    st.error(f"Nao foi possivel aplicar diagnostico ao motor: {exc}")
    else:
        if st.button("Salvar copia do diagnostico", use_container_width=True, key=f"diag_copy_{selected_id}"):
            _save_snapshot_copy(snapshot)
            st.success("Copia salva apenas para consulta.")

    with st.expander("Json da copia gerada"):
        st.json(snapshot, expanded=False)
        st.download_button(
            "Baixar copia (JSON)",
            data=json.dumps(snapshot, ensure_ascii=False, indent=2),
            file_name=f"diagnostico_copia_motor_{selected_id}.json",
            mime="application/json",
            use_container_width=True,
            key=f"diag_download_{selected_id}",
        )

    if admin_user:
        st.divider()
        st.markdown("### Revisao em lote — motor_inteligencia (read-only)")
        st.caption("Nao grava no Supabase. Usa a lista de motores ja carregada nesta pagina.")
        cap = max(10, min(len(motores), 2000))
        lim = int(
            st.number_input(
                "Max motores na amostra",
                min_value=10,
                max_value=cap,
                value=min(200, cap),
                step=10,
                key="intel_batch_limit",
            )
        )
        if st.button("Gerar relatorio read-only", use_container_width=True, key="intel_batch_btn"):
            st.session_state["intel_batch_last"] = build_batch_review_report(motores, limit=lim)
        rep_batch = st.session_state.get("intel_batch_last")
        if isinstance(rep_batch, dict) and rep_batch.get("meta"):
            ps = rep_batch.get("por_status") or {}
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Analisados", rep_batch["meta"].get("total_analisado", 0))
            c2.metric("OK", ps.get("ok", 0))
            c3.metric("Alerta", ps.get("alerta", 0))
            c4.metric("Critico", ps.get("critico", 0))
            c5.metric("Insuficiente", ps.get("insuficiente", 0))
            st.markdown("**Top issues**")
            st.write(rep_batch.get("top_issues") or [])
            st.markdown("**Top warnings**")
            st.write(rep_batch.get("top_warnings") or [])
            with st.expander("Exemplos por status", expanded=False):
                st.json(rep_batch.get("exemplos_por_status") or {}, expanded=False)
            with st.expander("Quase desbloqueados (poucos campos em falta)", expanded=False):
                st.json(rep_batch.get("quase_desbloqueados") or [], expanded=False)
            st.download_button(
                "Baixar relatorio motor_inteligencia (JSON)",
                data=json.dumps(prepare_fastapi_batch_payload(rep_batch), ensure_ascii=False, indent=2),
                file_name="motor_inteligencia_batch_review.json",
                mime="application/json",
                use_container_width=True,
                key="intel_batch_download",
            )

    flags = get_feature_flags()
    dev_mode = is_dev_mode()
    if flags.enable_laudo_pro or dev_mode:
        st.divider()
        st.markdown("## Laudo tecnico profissional")
        identidade = resolve_current_user_identity()
        raw_payload = _build_laudo_raw_payload(
            normalized=normalized,
            dados_placa=dados_placa,
            avisos=avisos,
            alertas_validacao=alertas_validacao,
            resultado_pos=resultado_pos if isinstance(resultado_pos, dict) else {},
        )
        laudo = build_laudo_tecnico(raw_payload, empresa_nome=identidade.get("display_name"))
        render_laudo_tecnico(laudo)
        _render_laudo_whatsapp_panel(laudo)


def render(ctx):
    # Diagnostico e um recurso pago; em development mode, permite abrir para validação.
    if not require_paid_access("Diagnostico tecnico", client=ctx.supabase):
        if not is_dev_mode():
            return
        st.warning("Acesso liberado por development mode (recurso pago em producao).")

    st.markdown(
        """
        <div class="diag-hero">
            <div class="diag-hero__tag">LAB TECNICO</div>
            <h1>Diagnostico de Motor</h1>
            <p>Painel da oficina para triagem real com base no historico tecnico salvo.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tabs = st.tabs(["Motor da oficina", "Simulador", "Checklist", "Alertas"])

    with tabs[0]:
        _render_real_diagnosis(ctx)

    with tabs[1]:
        st.markdown("### Simulador de carga")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            tensao = st.number_input("Tensao (V)", min_value=1.0, value=380.0, step=10.0)
        with c2:
            potencia_cv = st.number_input("Potencia (CV)", min_value=0.1, value=10.0, step=0.5)
        with c3:
            rendimento = st.number_input("Rendimento", min_value=0.1, max_value=1.0, value=0.90, step=0.01)
        with c4:
            fp = st.number_input("Fator de potencia", min_value=0.1, max_value=1.0, value=0.86, step=0.01)

        fases = st.radio("Tipo de alimentacao", ["Trifasico", "Monofasico"], horizontal=True)

        if st.button("Analisar corrente esperada", use_container_width=True):
            corrente = _estimate_current(potencia_cv, tensao, rendimento, fp, fases)
            faixa_min = corrente * 0.9
            faixa_max = corrente * 1.1
            st.markdown(
                f"""
                <div class="result-box">
                    <h3>Resultado previsto</h3>
                    <div class="result-big">{corrente:.2f} A</div>
                    <p>Faixa recomendada para comparacao: {faixa_min:.2f} A ate {faixa_max:.2f} A</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with tabs[2]:
        st.markdown("### Checklist de bancada")
        st.checkbox("Inspecao visual de terminais e isolacao")
        st.checkbox("Medicao de resistencia entre fases")
        st.checkbox("Megger para isolamento")
        st.checkbox("Conferencia de rolamentos e alinhamento")
        st.checkbox("Teste com carga progressiva")

    with tabs[3]:
        st.markdown("### Alertas criticos")
        st.markdown(
            """
            <div class="diag-alert">Corrente alta com RPM baixa pode indicar enrolamento errado ou tensao incorreta.</div>
            <div class="diag-alert">Aquecimento rapido no teste sem carga pode indicar curto entre espiras.</div>
            <div class="diag-alert">Vibracao com corrente normal pode ser causa mecanica (rolamento, eixo ou balanceamento).</div>
            """,
            unsafe_allow_html=True,
        )


def show(ctx):
    return render(ctx)
