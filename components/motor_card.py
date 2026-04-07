from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple

import streamlit as st

NOT_INFORMED = "Não informado"

SUMMARY_KEYS = {
    "marca",
    "modelo",
    "potencia_hp_cv",
    "potencia_kw",
    "rpm_nominal",
    "corrente_nominal_a",
    "polos",
    "numero_polos",
    "fases",
}

BOBINAGEM_FIELDS: List[Tuple[str, str]] = [
    ("Passo principal", "passo_principal"),
    ("Bobina principal", "espiras_principal"),
    ("Fio principal", "bitola_fio_principal"),
    ("Ligação interna", "ligacao_interna"),
    ("Tipo de bobinagem", "tipo_enrolamento"),
    ("Fios em paralelo", "fios_paralelos"),
    ("Resistência por fase", "resistencia_ohm_fase"),
    ("Número de ranhuras", "numero_ranhuras"),
]

AUX_BOBINAGEM_FIELDS: List[Tuple[str, str]] = [
    ("Passo auxiliar", "passo_auxiliar"),
    ("Bobina auxiliar", "espiras_auxiliar"),
    ("Fio auxiliar", "bitola_fio_auxiliar"),
]

MECANICA_FIELDS: List[Tuple[str, str]] = [
    ("Rolamento dianteiro", "rolamento_dianteiro"),
    ("Rolamento traseiro", "rolamento_traseiro"),
    ("Tamanho do eixo", "tamanho_eixo"),
    ("Diâmetro do eixo (mm)", "diametro_eixo_mm"),
    ("Carcaça", "carcaca"),
    ("Comprimento pacote (mm)", "comprimento_pacote_mm"),
    ("Diâmetro interno estator (mm)", "diametro_interno_estator_mm"),
    ("Diâmetro externo estator (mm)", "diametro_externo_estator_mm"),
    ("Material do núcleo", "material_nucleo"),
    ("Tipo de graxa", "tipo_graxa"),
    ("Peso total (kg)", "peso_total_kg"),
]


def _inject_styles() -> None:
    if st.session_state.get("_motor_card_styles_loaded"):
        return
    st.markdown(
        """
        <style>
        .motor-card-btn div[data-testid="stButton"] > button[kind="primary"] {
            width: 100%;
            min-height: 190px;
            border-radius: 16px;
            border: 1px solid rgba(0, 242, 255, 0.45);
            background: linear-gradient(145deg, #071320, #03070f);
            color: #f4fbff;
            box-shadow: 0 10px 32px rgba(0, 242, 255, 0.16);
            padding: 1.2rem 1.3rem;
            text-align: left;
            white-space: pre-line;
            line-height: 1.45;
            font-size: 1rem;
            transition: all 180ms ease-in-out;
        }
        .motor-card-btn div[data-testid="stButton"] > button[kind="primary"]:hover {
            border-color: rgba(0, 242, 255, 0.85);
            box-shadow: 0 12px 34px rgba(0, 242, 255, 0.28);
            transform: translateY(-1px);
        }
        .motor-card-open div[data-testid="stButton"] > button[kind="primary"] {
            border-color: #00f2ff;
            box-shadow: 0 12px 38px rgba(0, 242, 255, 0.34);
        }
        .motor-details-shell {
            margin-top: -0.2rem;
            margin-bottom: 1.1rem;
            border-radius: 14px;
            border: 1px solid rgba(0, 242, 255, 0.35);
            background: linear-gradient(155deg, rgba(6, 15, 26, 0.95), rgba(2, 7, 14, 0.95));
            padding: 14px;
        }
        .motor-kv {
            border-radius: 10px;
            border: 1px solid rgba(0, 242, 255, 0.18);
            background: rgba(0, 242, 255, 0.04);
            padding: 0.55rem 0.65rem;
            margin-bottom: 0.5rem;
        }
        .motor-kv-label {
            font-size: 0.73rem;
            color: #7aa5b7;
            text-transform: uppercase;
            letter-spacing: 0.04em;
            margin-bottom: 0.2rem;
        }
        .motor-kv-value {
            font-size: 0.95rem;
            color: #f4fbff;
            font-weight: 600;
            word-break: break-word;
        }
        @media (max-width: 768px) {
            .motor-card-btn div[data-testid="stButton"] > button[kind="primary"] {
                min-height: 168px;
                font-size: 0.95rem;
            }
            .motor-details-shell {
                padding: 11px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.session_state["_motor_card_styles_loaded"] = True


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        v = value.strip().lower()
        return v in {"", "none", "nan", "null"}
    return False


def _friendly(value: Any) -> str:
    if _is_empty(value):
        return NOT_INFORMED
    return str(value).strip()


def _format_label(raw_key: str) -> str:
    return raw_key.replace("_", " ").strip().title()


def _tipo_fase(motor: Dict[str, Any]) -> str:
    fase = str(motor.get("fases", "")).strip().lower()
    if not fase:
        return NOT_INFORMED

    if "mono" in fase:
        return "Monofásico"
    if "tri" in fase:
        return "Trifásico"

    try:
        fase_num = int(float(fase.replace(",", ".")))
        if fase_num == 1:
            return "Monofásico"
        if fase_num == 3:
            return "Trifásico"
    except Exception:
        pass

    return _friendly(motor.get("fases"))


def _is_monofasico(motor: Dict[str, Any]) -> bool:
    return _tipo_fase(motor) == "Monofásico"


def _field_pairs(motor: Dict[str, Any], fields: Iterable[Tuple[str, str]]) -> List[Tuple[str, str]]:
    pairs: List[Tuple[str, str]] = []
    for label, key in fields:
        pairs.append((label, _friendly(motor.get(key))))
    return pairs


def _general_pairs(motor: Dict[str, Any]) -> List[Tuple[str, str]]:
    excluded = set(SUMMARY_KEYS)
    excluded.update({key for _, key in BOBINAGEM_FIELDS})
    excluded.update({key for _, key in AUX_BOBINAGEM_FIELDS})
    excluded.update({key for _, key in MECANICA_FIELDS})

    pairs: List[Tuple[str, str]] = []
    for key in sorted(motor.keys()):
        if key in excluded:
            continue
        pairs.append((_format_label(key), _friendly(motor.get(key))))
    return pairs


def _render_pairs_grid(pairs: List[Tuple[str, str]], columns: int = 3) -> None:
    if not pairs:
        st.info("Nenhum dado disponível.")
        return

    cols = st.columns(columns)
    for idx, (label, value) in enumerate(pairs):
        with cols[idx % columns]:
            st.markdown(
                f"""
                <div class="motor-kv">
                    <div class="motor-kv-label">{label}</div>
                    <div class="motor-kv-value">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def motor_card(motor: Dict[str, Any], card_id: str, is_expanded: bool) -> bool:
    _inject_styles()

    marca = _friendly(motor.get("marca"))
    modelo = _friendly(motor.get("modelo"))
    potencia = _friendly(motor.get("potencia_hp_cv") or motor.get("potencia_kw"))
    rpm = _friendly(motor.get("rpm_nominal"))
    amperagem = _friendly(motor.get("corrente_nominal_a"))
    polos = _friendly(motor.get("polos") or motor.get("numero_polos"))
    tipo_fase = _tipo_fase(motor)
    registro = _friendly(motor.get("id"))

    label = (
        f"{marca} | {modelo}\n"
        f"Potência/CV: {potencia}    |    RPM: {rpm}\n"
        f"Amperagem: {amperagem}    |    Polos: {polos}    |    Tipo: {tipo_fase}\n"
        f"Registro: {registro}"
    )

    wrapper_class = "motor-card-btn motor-card-open" if is_expanded else "motor-card-btn"
    st.markdown(f'<div class="{wrapper_class}">', unsafe_allow_html=True)
    clicked = st.button(
        label,
        key=f"motor_btn_{card_id}",
        use_container_width=True,
        type="primary",
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if is_expanded:
        st.markdown('<div class="motor-details-shell">', unsafe_allow_html=True)
        tab_geral, tab_bob, tab_mec = st.tabs(["Dados gerais", "Bobinagem", "Mecânica"])

        with tab_geral:
            _render_pairs_grid(_general_pairs(motor), columns=3)

        with tab_bob:
            _render_pairs_grid(_field_pairs(motor, BOBINAGEM_FIELDS), columns=2)
            if _is_monofasico(motor):
                st.markdown("##### Enrolamento auxiliar (monofásico)")
                _render_pairs_grid(_field_pairs(motor, AUX_BOBINAGEM_FIELDS), columns=2)

        with tab_mec:
            _render_pairs_grid(_field_pairs(motor, MECANICA_FIELDS), columns=2)

        st.markdown("</div>", unsafe_allow_html=True)

    return clicked
