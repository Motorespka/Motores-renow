from __future__ import annotations

import html
import json
import os
import re
from typing import Any, Dict, List

import streamlit as st

from core.access_control import is_admin_user
from core.navigation import Route
from services.oficina_parser import build_normalized_from_motor_row
from services.supabase_data import fetch_motores_cached


def _is_empty(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip().lower() in {"", "none", "null", "nan"})


def _to_text(value: Any) -> str:
    if _is_empty(value):
        return ""
    if isinstance(value, list):
        return ", ".join(str(v) for v in value if str(v).strip())
    return str(value).strip()


def _safe(value: Any, fallback: str = "-") -> str:
    txt = _to_text(value)
    if not txt:
        txt = fallback
    return html.escape(txt)


def _is_path_like(value: str) -> bool:
    txt = value.strip()
    if not txt:
        return False
    if re.search(r"^[a-zA-Z]:\\", txt):
        return True
    if txt.startswith("/") or txt.startswith("\\\\"):
        return True
    return "/users/" in txt.lower() or "\\users\\" in txt.lower()


def _safe_file_label(value: Any) -> str:
    txt = _to_text(value)
    if not txt:
        return ""
    if _is_path_like(txt):
        return os.path.basename(txt.replace("\\", "/"))
    return txt


def _pick_first(row: Dict[str, Any], *keys: str) -> str:
    for key in keys:
        val = _to_text(row.get(key))
        if val:
            return val
    return ""


def _to_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip().startswith("{"):
        try:
            return json.loads(value)
        except Exception:
            return {}
    return {}


def _normalize_motor_record(row: Dict[str, Any]) -> Dict[str, Any]:
    data = _to_dict(row.get("dados_tecnicos_json") or row.get("leitura_gemini_json"))
    if not data:
        data = build_normalized_from_motor_row(row)
    motor = data.get("motor", {}) if isinstance(data, dict) else {}
    imagens = row.get("imagens_urls")
    if not imagens:
        imagens = _to_text(row.get("ImagemUrls") or row.get("ArquivoOrigem"))
    if isinstance(imagens, str):
        imagens = [v.strip() for v in imagens.replace(";", ",").split(",") if v.strip()]
    if not isinstance(imagens, list):
        imagens = []
    imagens = [_safe_file_label(v) for v in imagens if _safe_file_label(v)]

    motor_id = row.get("id")
    if motor_id in (None, ""):
        motor_id = row.get("Id")

    marca = _pick_first(row, "marca", "Marca") or _to_text(motor.get("marca"))
    modelo = _pick_first(row, "modelo_iec", "modelo_nema", "modelo", "Modelo") or _to_text(motor.get("modelo"))
    if not marca:
        marca = "Motor"
    if not modelo:
        modelo = f"Registro {motor_id}" if motor_id not in (None, "") else "Sem modelo"

    return {
        "id": motor_id,
        "marca": marca,
        "modelo": modelo,
        "potencia": _pick_first(row, "potencia", "potencia_cv", "Potencia") or _to_text(motor.get("potencia") or motor.get("cv")),
        "rpm": _pick_first(row, "rpm", "rpm_nominal", "Rpm") or _to_text(motor.get("rpm")),
        "tensao": _pick_first(row, "tensao", "tensao_v", "Tensao") or _to_text(motor.get("tensao")),
        "corrente": _pick_first(row, "corrente", "corrente_a", "Corrente") or _to_text(motor.get("corrente")),
        "polos": _pick_first(row, "polos", "Polos") or _to_text(motor.get("polos")),
        "tipo_motor": _pick_first(row, "tipo_motor", "TipoMotor") or _to_text(motor.get("tipo_motor")),
        "fases": _pick_first(row, "fases", "Fases") or _to_text(motor.get("fases")),
        "dados_tecnicos_json": data,
        "texto_bruto_extraido": _to_text(row.get("texto_bruto_extraido") or row.get("TextoBrutoExtraido") or data.get("texto_ocr")),
        "imagens_urls": imagens,
        "observacoes": _to_text(row.get("observacoes") or row.get("Observacoes") or data.get("observacoes_gerais")),
    }


def _search_blob(m: Dict[str, Any]) -> str:
    values = [
        m.get("marca"),
        m.get("modelo"),
        m.get("potencia"),
        m.get("rpm"),
        m.get("tensao"),
        m.get("corrente"),
        m.get("polos"),
        m.get("tipo_motor"),
        m.get("fases"),
        m.get("observacoes"),
    ]
    return " ".join(_to_text(v).lower() for v in values)


def _unique(rows: List[Dict[str, Any]], key: str) -> List[str]:
    return sorted({(_to_text(r.get(key))) for r in rows if _to_text(r.get(key))})


def _matches_range(v: str, r: tuple[float, float]) -> bool:
    if not v:
        return True
    num = "".join(ch for ch in v if ch.isdigit() or ch in ".,")
    if not num:
        return True
    try:
        val = float(num.replace(",", "."))
        return r[0] <= val <= r[1]
    except Exception:
        return True


def _section(data: Dict[str, Any], key: str) -> Dict[str, Any]:
    value = data.get(key) if isinstance(data, dict) else {}
    return value if isinstance(value, dict) else {}


def _join_values(value: Any) -> str:
    if isinstance(value, list):
        items = [str(v).strip() for v in value if str(v).strip()]
        return ", ".join(items) if items else "-"
    txt = _to_text(value)
    return txt if txt else "-"


def _render_data_panel(label: str, value: Any) -> None:
    st.markdown(
        f"""
        <div class="data-panel">
            <div class="data-label">{html.escape(label)}</div>
            <div class="data-value">{html.escape(_join_values(value))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _count_list_items(value: Any) -> int:
    if isinstance(value, list):
        return len([v for v in value if _to_text(v)])
    text = _to_text(value)
    if not text:
        return 0
    return len([p for p in re.split(r"\s*,\s*", text) if p.strip()])


def _render_technical_summary(motor: Dict[str, Any], data: Dict[str, Any]) -> None:
    motor_info = _section(data, "motor")
    principal = _section(data, "bobinagem_principal")
    auxiliar = _section(data, "bobinagem_auxiliar")
    mecanica = _section(data, "mecanica")
    esquema = _section(data, "esquema")
    oficina = _section(data, "oficina")
    diagnostico = oficina.get("diagnostico", {}) if isinstance(oficina, dict) else {}
    avisos = diagnostico.get("avisos", []) if isinstance(diagnostico, dict) else []
    if not isinstance(avisos, list):
        avisos = []

    resumo_id = (
        f"{_safe(motor.get('marca'))} {_safe(motor.get('modelo'))} | "
        f"{_safe(motor.get('tipo_motor'))} | {_safe(motor.get('fases'))} | {_safe(motor.get('polos'))}"
    )
    resumo_eletrico = (
        f"Potencia {_safe(motor.get('potencia'))} | RPM {_safe(motor.get('rpm'))} | "
        f"Tensao {_safe(motor.get('tensao'))} | Corrente {_safe(motor.get('corrente'))}"
    )
    resumo_bobinagem = (
        f"Principal: {_count_list_items(principal.get('passos'))} passos, "
        f"{_count_list_items(principal.get('espiras'))} espiras, "
        f"{_count_list_items(principal.get('fios'))} fios | "
        f"Auxiliar: {_count_list_items(auxiliar.get('passos'))} passos, "
        f"{_count_list_items(auxiliar.get('espiras'))} espiras, "
        f"{_count_list_items(auxiliar.get('fios'))} fios"
    )
    resumo_mecanica = (
        f"Carcaca {_safe(mecanica.get('carcaca') or motor_info.get('carcaca'))} | "
        f"Eixo {_safe(mecanica.get('eixo'))} | Rolamentos {_safe(mecanica.get('rolamentos'))} | "
        f"Ranhuras {_safe(esquema.get('ranhuras'))} | Camadas {_safe(esquema.get('camadas'))}"
    )
    resumo_ia = f"Alertas da IA: {len(avisos)}"

    st.markdown(
        f"""
        <div class="data-panel"><div class="data-label">Identificacao</div><div class="data-value">{resumo_id}</div></div>
        <div class="data-panel"><div class="data-label">Eletrica</div><div class="data-value">{resumo_eletrico}</div></div>
        <div class="data-panel"><div class="data-label">Bobinagem</div><div class="data-value">{resumo_bobinagem}</div></div>
        <div class="data-panel"><div class="data-label">Mecanica</div><div class="data-value">{resumo_mecanica}</div></div>
        <div class="data-panel"><div class="data-label">IA</div><div class="data-value">{resumo_ia}</div></div>
        """,
        unsafe_allow_html=True,
    )


def _render_consulta_header(total: int, filtrados: int, trifasicos: int, monofasicos: int) -> None:
    st.markdown(
        """
        <div class="consulta-hero">
            <div class="consulta-hero__tag">PAINEL TECNICO</div>
            <h1>Consulta de Motores</h1>
            <p>Dashboard tecnico para localizar, comparar e diagnosticar motores industriais.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f'<div class="dash-kpi"><span>Total</span><strong>{total}</strong></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="dash-kpi"><span>Filtrados</span><strong>{filtrados}</strong></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="dash-kpi"><span>Trifasicos</span><strong>{trifasicos}</strong></div>', unsafe_allow_html=True)
    c4.markdown(f'<div class="dash-kpi"><span>Monofasicos</span><strong>{monofasicos}</strong></div>', unsafe_allow_html=True)


def render(ctx) -> None:
    admin_user = is_admin_user()

    try:
        raw = fetch_motores_cached(ctx.supabase)
    except Exception as e:
        st.error(f"Erro ao carregar motores: {e}")
        return

    if not raw:
        st.info("Nenhum motor cadastrado.")
        return

    motores = [_normalize_motor_record(r) for r in raw]

    busca = st.text_input(
        "Busca geral",
        placeholder="Marca, modelo, potencia, rpm, tensao, corrente, polos...",
    ).strip().lower()
    filtrados = [m for m in motores if busca in _search_blob(m)] if busca else motores

    st.sidebar.markdown("### Filtros")
    marca = st.sidebar.selectbox("Marca", ["Todas"] + _unique(motores, "marca"))
    polos = st.sidebar.selectbox("Polos", ["Todos"] + _unique(motores, "polos"))
    tipo = st.sidebar.selectbox("Tipo do motor", ["Todos"] + _unique(motores, "tipo_motor"))
    fases = st.sidebar.selectbox("Fases", ["Todos"] + _unique(motores, "fases"))
    rpm_range = st.sidebar.slider("Faixa RPM", 0, 5000, (0, 5000), step=50)

    if marca != "Todas":
        filtrados = [m for m in filtrados if _to_text(m.get("marca")) == marca]
    if polos != "Todos":
        filtrados = [m for m in filtrados if _to_text(m.get("polos")) == polos]
    if tipo != "Todos":
        filtrados = [m for m in filtrados if _to_text(m.get("tipo_motor")) == tipo]
    if fases != "Todos":
        filtrados = [m for m in filtrados if _to_text(m.get("fases")) == fases]
    filtrados = [m for m in filtrados if _matches_range(_to_text(m.get("rpm")), rpm_range)]

    tri_count = sum(1 for m in filtrados if "tri" in _to_text(m.get("fases")).lower())
    mono_count = sum(1 for m in filtrados if "mono" in _to_text(m.get("fases")).lower())
    _render_consulta_header(len(motores), len(filtrados), tri_count, mono_count)

    if not filtrados:
        st.warning("Nenhum motor encontrado com os filtros atuais.")
        return

    for m in filtrados:
        with st.container(border=True):
            st.markdown(
                f"""
                <div class="motor-headline">
                    <div>
                        <div class="motor-id">#{_safe(m.get('id'))}</div>
                        <div class="motor-title">{_safe(m.get('marca'))} <span>{_safe(m.get('modelo'))}</span></div>
                    </div>
                    <div class="motor-chip">{_safe(m.get('tipo_motor'), fallback='Tipo nao informado')}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            left, right = st.columns([1.45, 1.0], gap="large")
            with left:
                k1, k2, k3, k4 = st.columns(4)
                k1.markdown(f'<div class="metric-tile"><span>Potencia</span><strong>{_safe(m.get("potencia"))}</strong></div>', unsafe_allow_html=True)
                k2.markdown(f'<div class="metric-tile"><span>RPM</span><strong>{_safe(m.get("rpm"))}</strong></div>', unsafe_allow_html=True)
                k3.markdown(f'<div class="metric-tile"><span>Tensao</span><strong>{_safe(m.get("tensao"))}</strong></div>', unsafe_allow_html=True)
                k4.markdown(f'<div class="metric-tile"><span>Corrente</span><strong>{_safe(m.get("corrente"))}</strong></div>', unsafe_allow_html=True)

                d1, d2 = st.columns(2)
                d1.markdown(f'<div class="inline-pill">Polos: <b>{_safe(m.get("polos"))}</b></div>', unsafe_allow_html=True)
                d2.markdown(f'<div class="inline-pill">Fases: <b>{_safe(m.get("fases"))}</b></div>', unsafe_allow_html=True)

            with right:
                st.markdown(
                    f"""
                    <div class="motor-visual">
                        <div class="motor-visual__label">Engine Hologram</div>
                        <div class="holo-stage">
                            <div class="holo-core"></div>
                            <div class="holo-ring"></div>
                            <div class="holo-ring ring-2"></div>
                            <div class="holo-ring ring-3"></div>
                            <div class="holo-stat stat-a">RPM {_safe(m.get("rpm"))}</div>
                            <div class="holo-stat stat-b">V {_safe(m.get("tensao"))}</div>
                            <div class="holo-stat stat-c">A {_safe(m.get("corrente"))}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            if admin_user:
                b1, b2 = st.columns(2)
                with b1:
                    if st.button("Editar", key=f"edit_{m['id']}", use_container_width=True):
                        ctx.session.selected_motor_id = m["id"]
                        ctx.session.set_route(Route.EDIT)
                        st.rerun()
                with b2:
                    if st.button("Detalhes", key=f"detail_{m['id']}", use_container_width=True):
                        ctx.session.selected_motor_id = m["id"]
                        ctx.session.set_route(Route.DETALHE)
                        st.rerun()
            else:
                if st.button("Detalhes", key=f"detail_{m['id']}", use_container_width=True):
                    ctx.session.selected_motor_id = m["id"]
                    ctx.session.set_route(Route.DETALHE)
                    st.rerun()

            data = m.get("dados_tecnicos_json", {})
            motor_info = _section(data, "motor")
            bob_principal = _section(data, "bobinagem_principal")
            bob_auxiliar = _section(data, "bobinagem_auxiliar")
            mecanica = _section(data, "mecanica")
            esquema = _section(data, "esquema")

            tab1, tab2, tab3, tab4 = st.tabs(["Identificacao", "Bobinagem", "Mecanica", "Leitura IA"])
            with tab1:
                c1, c2, c3 = st.columns(3)
                with c1:
                    _render_data_panel("Marca", m.get("marca"))
                    _render_data_panel("Modelo", m.get("modelo"))
                    _render_data_panel("Tipo", m.get("tipo_motor"))
                with c2:
                    _render_data_panel("Fases", m.get("fases"))
                    _render_data_panel("Polos", m.get("polos"))
                    _render_data_panel("Frequencia", motor_info.get("frequencia"))
                with c3:
                    _render_data_panel("Numero de serie", motor_info.get("numero_serie"))
                    _render_data_panel("IP", motor_info.get("ip"))
                    _render_data_panel("Isolacao", motor_info.get("isolacao"))

            with tab2:
                bb1, bb2 = st.columns(2)
                with bb1:
                    _render_data_panel("Passos principais", bob_principal.get("passos"))
                    _render_data_panel("Espiras principais", bob_principal.get("espiras"))
                    _render_data_panel("Fio principal", bob_principal.get("fios"))
                    _render_data_panel("Ligacao principal", bob_principal.get("ligacao"))
                    _render_data_panel("Qtd. grupos", bob_principal.get("quantidade_grupos"))
                    _render_data_panel("Qtd. bobinas", bob_principal.get("quantidade_bobinas"))
                with bb2:
                    _render_data_panel("Passos auxiliares", bob_auxiliar.get("passos"))
                    _render_data_panel("Espiras auxiliares", bob_auxiliar.get("espiras"))
                    _render_data_panel("Fio auxiliar", bob_auxiliar.get("fios"))
                    _render_data_panel("Ligacao auxiliar", bob_auxiliar.get("ligacao"))
                    _render_data_panel("Capacitor", bob_auxiliar.get("capacitor"))
                    _render_data_panel("Obs. bobinagem", bob_principal.get("observacoes") or bob_auxiliar.get("observacoes"))

            with tab3:
                mc1, mc2 = st.columns(2)
                with mc1:
                    _render_data_panel("Rolamentos", mecanica.get("rolamentos"))
                    _render_data_panel("Eixo", mecanica.get("eixo"))
                    _render_data_panel("Carcaca", mecanica.get("carcaca"))
                    _render_data_panel("Comprimento ponta", mecanica.get("comprimento_ponta"))
                    _render_data_panel("Obs. mecanica", mecanica.get("observacoes"))
                with mc2:
                    _render_data_panel("Medidas", mecanica.get("medidas"))
                    _render_data_panel("Esquema de ligacao", esquema.get("ligacao"))
                    _render_data_panel("Ranhuras", esquema.get("ranhuras"))
                    _render_data_panel("Camadas", esquema.get("camadas"))
                    _render_data_panel("Distribuicao bobinas", esquema.get("distribuicao_bobinas"))

            with tab4:
                _render_data_panel("Observacoes", m.get("observacoes"))
                oficina = _section(data, "oficina")
                diagnostico = oficina.get("diagnostico", {}) if isinstance(oficina, dict) else {}
                avisos = diagnostico.get("avisos", []) if isinstance(diagnostico, dict) else []
                if isinstance(avisos, list) and avisos:
                    st.markdown("Diagnostico da oficina")
                    for aviso in avisos[:4]:
                        st.write(f"- {aviso}")
                else:
                    st.caption("Sem alertas tecnicos registrados pela IA para este motor.")
                if admin_user:
                    _render_data_panel("Texto OCR", m.get("texto_bruto_extraido"))
                _render_data_panel("Esquema (observacoes)", esquema.get("observacoes"))

            with st.expander("Resumo tecnico", expanded=False):
                _render_technical_summary(m, data)


def show(ctx) -> None:
    return render(ctx)
