from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple

import streamlit as st

NOT_INFORMED = "Não informado"

try:
    from utils.configuracoes_motor import obter_configuracoes_ligacao
except Exception:
    def obter_configuracoes_ligacao(_motor_data: Dict[str, Any]) -> str:
        return "Sugestao tecnica indisponivel."

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
    ("Ligacao interna", "ligacao_interna"),
    ("Tipo de bobinagem", "tipo_enrolamento"),
    ("Fios em paralelo", "fios_paralelos"),
    ("Resistencia por fase", "resistencia_ohm_fase"),
    ("Numero de ranhuras", "numero_ranhuras"),
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
    ("Diametro do eixo (mm)", "diametro_eixo_mm"),
    ("Carcaca", "carcaca"),
    ("Comprimento pacote (mm)", "comprimento_pacote_mm"),
    ("Diametro interno estator (mm)", "diametro_interno_estator_mm"),
    ("Diametro externo estator (mm)", "diametro_externo_estator_mm"),
    ("Material do nucleo", "material_nucleo"),
    ("Tipo de graxa", "tipo_graxa"),
    ("Peso total (kg)", "peso_total_kg"),
]


def _inject_styles() -> None:
    if st.session_state.get("_motor_card_styles_loaded"):
        return

    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700&family=Rajdhani:wght@500;700&display=swap');

        .motor-card-btn div[data-testid="stButton"] > button {
            width: 100%;
            min-height: 230px;
            border-radius: 18px;
            border: 1px solid rgba(0, 242, 255, 0.55);
            background: linear-gradient(145deg, rgba(5, 18, 29, 0.98), rgba(2, 6, 12, 0.98));
            color: #f4fbff;
            box-shadow: 0 16px 42px rgba(0, 242, 255, 0.2);
            padding: 1.4rem 1.45rem;
            text-align: left;
            white-space: pre-line;
            line-height: 1.6;
            font-size: 1.12rem;
            font-family: "Rajdhani", "Orbitron", "Consolas", monospace;
            letter-spacing: 0.02em;
            text-shadow: 0 0 10px rgba(0, 242, 255, 0.2);
            transition: all 180ms ease-in-out;
        }
        .motor-card-btn div[data-testid="stButton"] > button:hover {
            border-color: rgba(0, 242, 255, 0.85);
            box-shadow: 0 20px 52px rgba(0, 242, 255, 0.35);
            transform: translateY(-2px);
        }
        .motor-card-open div[data-testid="stButton"] > button {
            border-color: #00f2ff;
            box-shadow: 0 20px 56px rgba(0, 242, 255, 0.4);
        }
        .motor-details-shell {
            margin-top: -0.2rem;
            margin-bottom: 1.3rem;
            border-radius: 14px;
            border: 1px solid rgba(0, 242, 255, 0.35);
            background: linear-gradient(155deg, rgba(6, 15, 26, 0.95), rgba(2, 7, 14, 0.95));
            padding: 16px;
            font-family: "Rajdhani", "Consolas", monospace;
        }
        .motor-kv {
            border-radius: 10px;
            border: 1px solid rgba(0, 242, 255, 0.18);
            background: rgba(0, 242, 255, 0.04);
            padding: 0.6rem 0.72rem;
            margin-bottom: 0.55rem;
        }
        .motor-kv-label {
            font-size: 0.76rem;
            color: #7aa5b7;
            text-transform: uppercase;
            letter-spacing: 0.07em;
            margin-bottom: 0.22rem;
        }
        .motor-kv-value {
            font-size: 1rem;
            color: #f4fbff;
            font-weight: 600;
            word-break: break-word;
        }
        @media (max-width: 768px) {
            .motor-card-btn div[data-testid="stButton"] > button {
                min-height: 205px;
                font-size: 1rem;
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


def _coalesce(motor: Dict[str, Any], keys: Iterable[str]) -> Any:
    for key in keys:
        if key in motor and not _is_empty(motor.get(key)):
            return motor.get(key)
    return None


def _format_label(raw_key: str) -> str:
    return raw_key.replace("_", " ").strip().title()


def _tipo_fase(motor: Dict[str, Any]) -> str:
    fase = str(_coalesce(motor, ["fases", "fase", "tipo_fase", "tipo_enrolamento"]) or "").strip().lower()
    if not fase:
        return NOT_INFORMED

    if "mono" in fase:
        return "Monofasico"
    if "tri" in fase:
        return "Trifasico"

    try:
        fase_num = int(float(fase.replace(",", ".")))
        if fase_num == 1:
            return "Monofasico"
        if fase_num == 3:
            return "Trifasico"
    except Exception:
        pass

    return _friendly(_coalesce(motor, ["fases", "fase"]))


def _is_monofasico(motor: Dict[str, Any]) -> bool:
    return _tipo_fase(motor) == "Monofasico"


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
        st.info("Nenhum dado disponivel.")
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

    marca = _friendly(_coalesce(motor, ["marca", "fabricante", "brand"]))
    modelo_raw = _coalesce(motor, ["modelo", "num_serie", "modelo_motor", "nome", "linha"])
    if _is_empty(modelo_raw):
        modelo_raw = f"Registro #{_friendly(motor.get('id'))}"
    modelo = _friendly(modelo_raw)
    potencia = _friendly(_coalesce(motor, ["potencia_hp_cv", "potencia", "potencia_kw", "potencia_cv", "potencia_hp"]))
    rpm = _friendly(_coalesce(motor, ["rpm_nominal", "rpm", "rotacao"]))
    amperagem = _friendly(_coalesce(motor, ["corrente_nominal_a", "corrente", "amperagem"]))
    polos = _friendly(_coalesce(motor, ["polos", "numero_polos", "poles"]))
    tipo_fase = _tipo_fase(motor)
    registro = _friendly(motor.get("id"))

    label = (
        f"{marca} | {modelo}\n"
        f"Potencia/CV: {potencia}    |    RPM: {rpm}\n"
        f"Amperagem: {amperagem}    |    Polos: {polos}    |    Tipo: {tipo_fase}\n"
        f"Registro: {registro}"
    )

    wrapper_class = "motor-card-btn motor-card-open" if is_expanded else "motor-card-btn"
    st.markdown(f'<div class="{wrapper_class}">', unsafe_allow_html=True)
    clicked = st.button(
        label,
        key=f"motor_btn_{card_id}",
        use_container_width=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if is_expanded:
        st.markdown('<div class="motor-details-shell">', unsafe_allow_html=True)
        tab_geral, tab_bob, tab_mec = st.tabs(["Dados gerais", "Bobinagem", "Mecanica"])

        with tab_geral:
            st.markdown("##### Ligacao tecnica sugerida")
            st.info(obter_configuracoes_ligacao(motor))
            _render_pairs_grid(_general_pairs(motor), columns=3)

        with tab_bob:
            _render_pairs_grid(_field_pairs(motor, BOBINAGEM_FIELDS), columns=2)
            if _is_monofasico(motor):
                st.markdown("##### Enrolamento auxiliar (monofasico)")
                _render_pairs_grid(_field_pairs(motor, AUX_BOBINAGEM_FIELDS), columns=2)

        with tab_mec:
            _render_pairs_grid(_field_pairs(motor, MECANICA_FIELDS), columns=2)

        st.markdown("</div>", unsafe_allow_html=True)

    return clicked
