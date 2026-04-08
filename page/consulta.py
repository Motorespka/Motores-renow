from __future__ import annotations

import json
from typing import Any, Dict, List

import streamlit as st

from core.navigation import Route
from services.supabase_data import fetch_motores_cached


def _is_empty(value: Any) -> bool:
    return value is None or (isinstance(value, str) and value.strip().lower() in {"", "none", "null", "nan"})


def _to_text(value: Any) -> str:
    if _is_empty(value):
        return ""
    if isinstance(value, list):
        return ", ".join(str(v) for v in value if str(v).strip())
    return str(value).strip()


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
    motor = data.get("motor", {}) if isinstance(data, dict) else {}

    return {
        "id": row.get("id"),
        "marca": _pick_first(row, "marca") or _to_text(motor.get("marca")),
        "modelo": _pick_first(row, "modelo_iec", "modelo_nema", "modelo") or _to_text(motor.get("modelo")),
        "potencia": _pick_first(row, "potencia", "potencia_cv") or _to_text(motor.get("potencia") or motor.get("cv")),
        "rpm": _pick_first(row, "rpm", "rpm_nominal") or _to_text(motor.get("rpm")),
        "tensao": _pick_first(row, "tensao", "tensao_v") or _to_text(motor.get("tensao")),
        "corrente": _pick_first(row, "corrente", "corrente_a") or _to_text(motor.get("corrente")),
        "polos": _pick_first(row, "polos") or _to_text(motor.get("polos")),
        "tipo_motor": _pick_first(row, "tipo_motor") or _to_text(motor.get("tipo_motor")),
        "fases": _pick_first(row, "fases") or _to_text(motor.get("fases")),
        "dados_tecnicos_json": data,
        "texto_bruto_extraido": _to_text(row.get("texto_bruto_extraido") or data.get("texto_ocr")),
        "imagens_urls": row.get("imagens_urls") or [],
        "observacoes": _to_text(row.get("observacoes") or data.get("observacoes_gerais")),
    }


def _search_blob(m: Dict[str, Any]) -> str:
    values = [m.get("marca"), m.get("modelo"), m.get("potencia"), m.get("rpm"), m.get("tensao"), m.get("corrente"), m.get("polos"), m.get("tipo_motor"), m.get("fases"), m.get("observacoes")]
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


def _render_expanded_sections(motor: Dict[str, Any]) -> None:
    data = motor.get("dados_tecnicos_json", {})
    st.markdown("#### Identificação")
    st.json(data.get("motor", {}), expanded=False)
    st.markdown("#### Bobinagem principal")
    st.json(data.get("bobinagem_principal", {}), expanded=False)
    st.markdown("#### Bobinagem auxiliar")
    st.json(data.get("bobinagem_auxiliar", {}), expanded=False)
    st.markdown("#### Mecânica")
    st.json(data.get("mecanica", {}), expanded=False)
    st.markdown("#### Esquema técnico")
    st.json(data.get("esquema", {}), expanded=False)
    st.markdown("#### Observações")
    st.write(motor.get("observacoes") or "-")
    st.markdown("#### Texto bruto lido")
    st.text_area("", value=motor.get("texto_bruto_extraido") or "", height=120, key=f"ocr_{motor.get('id')}")
    urls = motor.get("imagens_urls") or []
    if urls:
        st.markdown("#### Imagens vinculadas")
        for u in urls:
            st.write(f"- {u}")


def render(ctx) -> None:
    st.title("🔎 Consulta Técnica de Motores")

    try:
        raw = fetch_motores_cached(ctx.supabase)
    except Exception as e:
        st.error(f"Erro ao carregar motores: {e}")
        return

    if not raw:
        st.info("Nenhum motor cadastrado.")
        return

    motores = [_normalize_motor_record(r) for r in raw]

    busca = st.text_input("Busca geral", placeholder="Marca, modelo, potência, rpm, tensão, corrente, polos...").strip().lower()
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

    st.caption(f"Resultados encontrados: {len(filtrados)}")
    if not filtrados:
        st.warning("Nenhum motor encontrado com os filtros atuais.")
        return

    for m in filtrados:
        with st.container(border=True):
            st.markdown(f"### {m.get('marca') or '-'} | {m.get('modelo') or '-'}")
            c1, c2, c3, c4 = st.columns(4)
            c1.write(f"**Potência:** {m.get('potencia') or '-'}")
            c2.write(f"**RPM:** {m.get('rpm') or '-'}")
            c3.write(f"**Tensão:** {m.get('tensao') or '-'}")
            c4.write(f"**Corrente:** {m.get('corrente') or '-'}")
            d1, d2 = st.columns(2)
            d1.write(f"**Polos:** {m.get('polos') or '-'}")
            d2.write(f"**Tipo:** {m.get('tipo_motor') or '-'}")

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

            with st.expander("Expandir dados técnicos"):
                _render_expanded_sections(m)
