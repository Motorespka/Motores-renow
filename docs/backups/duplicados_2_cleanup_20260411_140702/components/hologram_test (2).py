from __future__ import annotations

import html
from typing import Any, Dict

import streamlit as st


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _first_nonempty(*values: Any) -> str:
    for value in values:
        text = _to_text(value)
        if text:
            return text
    return "-"


def _has_capacitor(motor: Dict[str, Any]) -> bool:
    fases = _to_text(motor.get("fases")).lower()
    tipo = _to_text(motor.get("tipo_motor")).lower()
    data = motor.get("dados_tecnicos_json", {})
    aux = data.get("bobinagem_auxiliar", {}) if isinstance(data, dict) else {}
    capacitor = aux.get("capacitor") if isinstance(aux, dict) else ""
    return "mono" in fases or "capacitor" in tipo or bool(_to_text(capacitor))


def _inject_css_once() -> None:
    if st.session_state.get("_hologram_test_css_loaded"):
        return

    st.markdown(
        """
        <style>
        .holo-test-wrap {
            position: relative;
            min-height: 230px;
            border: 1px solid rgba(34, 211, 238, 0.40);
            border-radius: 16px;
            overflow: hidden;
            padding: 12px 12px 6px 12px;
            background:
                radial-gradient(circle at 18% 15%, rgba(34, 211, 238, 0.18), transparent 44%),
                radial-gradient(circle at 80% 0%, rgba(6, 182, 212, 0.14), transparent 48%),
                linear-gradient(160deg, rgba(2, 6, 23, 0.97), rgba(3, 15, 28, 0.92));
            box-shadow:
                inset 0 0 30px rgba(34, 211, 238, 0.12),
                0 0 22px rgba(34, 211, 238, 0.12);
        }
        .holo-test-head {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 11px;
            letter-spacing: 0.12em;
            color: #67e8f9;
            opacity: 0.88;
            margin-bottom: 6px;
        }
        .holo-test-stage {
            position: relative;
            height: 175px;
            border-radius: 12px;
            overflow: hidden;
            background:
                linear-gradient(180deg, rgba(14, 116, 144, 0.15), rgba(6, 78, 95, 0.05)),
                repeating-linear-gradient(
                    to bottom,
                    rgba(34, 211, 238, 0.06) 0px,
                    rgba(34, 211, 238, 0.06) 1px,
                    transparent 1px,
                    transparent 7px
                );
        }
        .holo-test-grid {
            position: absolute;
            inset: 0;
            background:
                linear-gradient(90deg, rgba(34, 211, 238, 0.06) 1px, transparent 1px),
                linear-gradient(rgba(34, 211, 238, 0.05) 1px, transparent 1px);
            background-size: 28px 28px;
            opacity: 0.25;
        }
        .holo-test-shadow {
            position: absolute;
            left: 46px;
            bottom: 21px;
            width: 178px;
            height: 20px;
            border-radius: 50%;
            background: radial-gradient(ellipse at center, rgba(6, 182, 212, 0.50), transparent 72%);
            filter: blur(3px);
            animation: holoPulse 4.4s ease-in-out infinite;
        }
        .holo-test-motor {
            position: absolute;
            left: 34px;
            top: 56px;
            width: 195px;
            height: 72px;
            transform: perspective(600px) rotateY(-16deg);
        }
        .holo-test-body {
            position: absolute;
            left: 28px;
            top: 10px;
            width: 138px;
            height: 52px;
            border-radius: 26px;
            border: 1px solid rgba(103, 232, 249, 0.86);
            background:
                linear-gradient(180deg, rgba(34, 211, 238, 0.34), rgba(8, 145, 178, 0.10)),
                radial-gradient(circle at 35% 30%, rgba(125, 252, 255, 0.32), transparent 46%);
            box-shadow:
                inset 0 0 12px rgba(125, 252, 255, 0.28),
                0 0 16px rgba(34, 211, 238, 0.33);
        }
        .holo-test-fins {
            position: absolute;
            inset: 8px 10px;
            display: flex;
            gap: 5px;
        }
        .holo-test-fins i {
            flex: 1;
            border-radius: 999px;
            background: linear-gradient(180deg, rgba(103, 232, 249, 0.6), rgba(12, 74, 110, 0.08));
            box-shadow: 0 0 6px rgba(34, 211, 238, 0.3);
            opacity: 0.75;
        }
        .holo-test-endcap-front,
        .holo-test-endcap-back {
            position: absolute;
            top: 13px;
            width: 42px;
            height: 46px;
            border-radius: 50%;
            border: 1px solid rgba(103, 232, 249, 0.92);
            background: radial-gradient(circle at 35% 35%, rgba(125, 252, 255, 0.38), rgba(8, 47, 73, 0.22));
            box-shadow: inset 0 0 10px rgba(34, 211, 238, 0.28), 0 0 13px rgba(34, 211, 238, 0.35);
        }
        .holo-test-endcap-front { left: 6px; }
        .holo-test-endcap-back { left: 153px; opacity: 0.9; }
        .holo-test-shaft {
            position: absolute;
            left: -18px;
            top: 29px;
            width: 38px;
            height: 13px;
            border-radius: 7px;
            border: 1px solid rgba(125, 252, 255, 0.9);
            background: linear-gradient(90deg, rgba(125, 252, 255, 0.66), rgba(8, 145, 178, 0.14));
            box-shadow: 0 0 11px rgba(34, 211, 238, 0.45);
        }
        .holo-test-jbox {
            position: absolute;
            left: 84px;
            top: -11px;
            width: 56px;
            height: 23px;
            border-radius: 6px;
            border: 1px solid rgba(103, 232, 249, 0.9);
            background: linear-gradient(180deg, rgba(125, 252, 255, 0.35), rgba(6, 78, 95, 0.18));
            box-shadow: 0 0 10px rgba(34, 211, 238, 0.36);
        }
        .holo-test-cap {
            position: absolute;
            left: 147px;
            top: -8px;
            width: 29px;
            height: 19px;
            border-radius: 10px;
            border: 1px solid rgba(165, 243, 252, 0.92);
            background: linear-gradient(180deg, rgba(165, 243, 252, 0.34), rgba(8, 145, 178, 0.1));
            box-shadow: 0 0 10px rgba(103, 232, 249, 0.42);
        }
        .holo-test-foot {
            position: absolute;
            top: 64px;
            width: 26px;
            height: 10px;
            border-radius: 3px;
            border: 1px solid rgba(103, 232, 249, 0.74);
            background: rgba(34, 211, 238, 0.25);
        }
        .holo-test-foot.f1 { left: 64px; }
        .holo-test-foot.f2 { left: 124px; }
        .holo-test-callout {
            position: absolute;
            color: #cffafe;
            font-size: 10px;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            white-space: nowrap;
        }
        .holo-test-callout .line {
            position: absolute;
            background: linear-gradient(90deg, rgba(34, 211, 238, 0.94), rgba(103, 232, 249, 0.26));
            box-shadow: 0 0 7px rgba(34, 211, 238, 0.58);
        }
        .holo-test-callout.eixo { left: 250px; top: 36px; }
        .holo-test-callout.eixo .line { left: -95px; top: 7px; width: 88px; height: 1px; }
        .holo-test-callout.rolamento { left: 248px; top: 60px; }
        .holo-test-callout.rolamento .line { left: -86px; top: 7px; width: 78px; height: 1px; }
        .holo-test-callout.flange { left: 244px; top: 84px; }
        .holo-test-callout.flange .line { left: -123px; top: 7px; width: 112px; height: 1px; }
        .holo-test-callout.caixa { left: 236px; top: 108px; }
        .holo-test-callout.caixa .line { left: -96px; top: 7px; width: 87px; height: 1px; }
        .holo-test-callout.capacitor { left: 214px; top: 130px; }
        .holo-test-callout.capacitor .line { left: -72px; top: 7px; width: 64px; height: 1px; }
        .holo-test-kpis {
            display: grid;
            margin-top: 8px;
            gap: 6px;
            grid-template-columns: repeat(3, minmax(0, 1fr));
        }
        .holo-test-kpi {
            font-size: 10px;
            border-radius: 8px;
            border: 1px solid rgba(34, 211, 238, 0.35);
            background: rgba(6, 78, 95, 0.30);
            color: #a5f3fc;
            padding: 4px 8px;
        }
        .holo-test-kpi b {
            color: #ecfeff;
            font-weight: 700;
        }
        @keyframes holoPulse {
            0% { transform: scale(0.98); opacity: 0.62; }
            50% { transform: scale(1.03); opacity: 1; }
            100% { transform: scale(0.98); opacity: 0.62; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.session_state["_hologram_test_css_loaded"] = True


def render_hologram_test(motor: Dict[str, Any], key: str = "") -> None:
    _inject_css_once()

    data = motor.get("dados_tecnicos_json", {}) if isinstance(motor, dict) else {}
    mecanica = data.get("mecanica", {}) if isinstance(data, dict) else {}

    eixo = _first_nonempty(mecanica.get("eixo"), "-")
    rolamento = _first_nonempty(mecanica.get("rolamentos"), "-")
    flange = _first_nonempty(mecanica.get("carcaca"), "padrao")
    caixa = _first_nonempty(motor.get("tipo_motor"), "nao informado")
    mostrar_capacitor = _has_capacitor(motor)

    rpm = html.escape(_first_nonempty(motor.get("rpm"), "-"))
    tensao = html.escape(_first_nonempty(motor.get("tensao"), "-"))
    corrente = html.escape(_first_nonempty(motor.get("corrente"), "-"))

    key_attr = html.escape(key or _first_nonempty(motor.get("id"), "motor"))
    callout_cap = ""
    cap_shape = ""
    if mostrar_capacitor:
        cap_shape = '<div class="holo-test-cap"></div>'
        callout_cap = f"""
            <div class="holo-test-callout capacitor">
                <div class="line"></div>
                CAPACITOR: {html.escape(_first_nonempty(data.get("bobinagem_auxiliar", {}).get("capacitor") if isinstance(data.get("bobinagem_auxiliar"), dict) else "-", "-"))}
            </div>
        """

    st.markdown(
        f"""
        <div class="holo-test-wrap" data-key="{key_attr}">
            <div class="holo-test-head">
                <span>MODO TESTE HOLOGRAFICO</span>
                <span>ASSINATURA VISUAL 3D</span>
            </div>
            <div class="holo-test-stage">
                <div class="holo-test-grid"></div>
                <div class="holo-test-shadow"></div>
                <div class="holo-test-motor">
                    <div class="holo-test-endcap-front"></div>
                    <div class="holo-test-shaft"></div>
                    <div class="holo-test-body">
                        <div class="holo-test-fins">
                            <i></i><i></i><i></i><i></i><i></i><i></i><i></i>
                        </div>
                    </div>
                    <div class="holo-test-endcap-back"></div>
                    <div class="holo-test-jbox"></div>
                    {cap_shape}
                    <div class="holo-test-foot f1"></div>
                    <div class="holo-test-foot f2"></div>
                </div>
                <div class="holo-test-callout eixo">
                    <div class="line"></div>
                    EIXO: {html.escape(eixo)}
                </div>
                <div class="holo-test-callout rolamento">
                    <div class="line"></div>
                    ROLAMENTO: {html.escape(rolamento)}
                </div>
                <div class="holo-test-callout flange">
                    <div class="line"></div>
                    FLANGE: {html.escape(flange)}
                </div>
                <div class="holo-test-callout caixa">
                    <div class="line"></div>
                    CAIXA DE LIGACAO: {html.escape(caixa)}
                </div>
                {callout_cap}
            </div>
            <div class="holo-test-kpis">
                <div class="holo-test-kpi">RPM: <b>{rpm}</b></div>
                <div class="holo-test-kpi">TENSAO: <b>{tensao}</b></div>
                <div class="holo-test-kpi">CORRENTE: <b>{corrente}</b></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
