from __future__ import annotations

import json
import math
from datetime import datetime
from typing import Any, Dict, List

import streamlit as st

from core.access_control import is_admin_user
from services.oficina_parser import normalize_extracted_data
from services.oficina_runtime import diagnostico_motor_oficina_readonly, resumir_diagnostico_oficina
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
    ctx.supabase.table("motores").update(payload).eq("id", motor_id).execute()
    clear_motores_cache()


def _render_real_diagnosis(ctx) -> None:
    admin_user = is_admin_user()
    st.markdown("### Motor da Oficina")
    try:
        motores = fetch_motores_cached(ctx.supabase)
    except Exception as exc:
        st.warning(f"Nao foi possivel carregar motores para diagnostico: {exc}")
        return

    if not motores:
        st.info("Nenhum motor cadastrado ainda para diagnostico real.")
        return

    options: List[tuple[str, Any]] = []
    for row in motores:
        label = f"#{row.get('id')} | {_to_text(row.get('marca')) or '-'} | {_to_text(row.get('modelo')) or '-'}"
        options.append((label, row.get("id")))

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


def render(ctx):
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
