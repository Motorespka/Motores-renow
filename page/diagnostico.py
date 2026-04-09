from __future__ import annotations

import json
import math
from typing import Any, Dict, List

import streamlit as st

from services.oficina_parser import normalize_extracted_data
from services.oficina_runtime import diagnostico_motor_oficina_readonly, resumir_diagnostico_oficina
from services.supabase_data import fetch_motor_by_id_cached, fetch_motores_cached


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


def _render_real_diagnosis(ctx) -> None:
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
    ctx.session.selected_motor_id = selected_id

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
