from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st

from components.motor_card import render_motor_card
from core.navigation import Route
from services.supabase_data import fetch_motores_cached


def _is_empty(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip().lower() in {"", "none", "null", "nan"}:
        return True
    return False


def _to_text(value: Any) -> str:
    if _is_empty(value):
        return ""
    return str(value).strip()


def _pick_first(row: Dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = _to_text(row.get(key))
        if value:
            return value
    return ""


def _normalize_motor_record(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normaliza os dados vindos da view public.vw_consulta_motores
    para um formato mais previsível para a interface.
    """
    arquivo_nome = _to_text(row.get("arquivo_nome"))
    modelo = _pick_first(row, "modelo_iec", "modelo_nema", "modelo")
    marca = _to_text(row.get("marca"))

    potencia_cv = _to_text(row.get("potencia_cv"))
    frequencia_hz = _to_text(row.get("frequencia_hz"))
    rpm = _to_text(row.get("rpm"))
    polos = _to_text(row.get("polos"))
    tensao_v = _to_text(row.get("tensao_v"))
    corrente_a = _to_text(row.get("corrente_a"))
    grau_protecao_ip = _to_text(row.get("grau_protecao_ip"))
    ligacao = _to_text(row.get("ligacao"))
    tipo_bobinagem = _to_text(row.get("tipo_bobinagem"))
    bitola_fio = _to_text(row.get("bitola_fio"))
    capacitor = _to_text(row.get("capacitor"))
    aplicacao = _to_text(row.get("aplicacao"))

    return {
        "id": row.get("id"),
        "arquivo_id": row.get("id"),

        # principais para exibição
        "arquivo_nome": arquivo_nome,
        "nome": arquivo_nome,
        "marca": marca,
        "modelo": modelo,
        "potencia": potencia_cv,
        "potencia_cv": potencia_cv,
        "frequencia_hz": frequencia_hz,
        "rpm": rpm,
        "polos": polos,
        "tensao": tensao_v,
        "tensao_v": tensao_v,
        "corrente": corrente_a,
        "corrente_a": corrente_a,
        "grau_protecao_ip": grau_protecao_ip,
        "ip": grau_protecao_ip,
        "ligacao": ligacao,
        "tipo_bobinagem": tipo_bobinagem,
        "bitola_fio": bitola_fio,
        "capacitor": capacitor,
        "aplicacao": aplicacao,

        # metadados do arquivo
        "caminho_origem": _to_text(row.get("caminho_origem")),
        "caminho_local": _to_text(row.get("caminho_local")),
        "extensao": _to_text(row.get("extensao")),
        "tipo_arquivo": _to_text(row.get("tipo_arquivo")),
        "tipo_conteudo": _to_text(row.get("tipo_conteudo")),
        "extraido_de_zip": row.get("extraido_de_zip"),
        "zip_origem": _to_text(row.get("zip_origem")),
        "caminho_interno_zip": _to_text(row.get("caminho_interno_zip")),
        "tamanho_bytes": row.get("tamanho_bytes") or 0,
        "status_leitura": _to_text(row.get("status_leitura")),
        "erro": _to_text(row.get("erro")),
        "confianca_predominante": _to_text(row.get("confianca_predominante")),
        "total_variaveis": row.get("total_variaveis") or 0,
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
    }


def _search_blob(motor: Dict[str, Any]) -> str:
    fields = [
        "arquivo_nome",
        "nome",
        "marca",
        "modelo",
        "potencia",
        "potencia_cv",
        "frequencia_hz",
        "rpm",
        "polos",
        "tensao",
        "tensao_v",
        "corrente",
        "corrente_a",
        "grau_protecao_ip",
        "ip",
        "ligacao",
        "tipo_bobinagem",
        "bitola_fio",
        "capacitor",
        "aplicacao",
        "tipo_arquivo",
        "tipo_conteudo",
        "extensao",
        "status_leitura",
        "confianca_predominante",
        "caminho_origem",
        "zip_origem",
    ]
    return " ".join(_to_text(motor.get(field)) for field in fields).lower()


def _unique_values(rows: List[Dict[str, Any]], key: str) -> List[str]:
    values = set()
    for row in rows:
        val = _to_text(row.get(key))
        if val:
            values.add(val)
    return sorted(values)


def render(ctx) -> None:
    st.title("🔎 Central de Motores")

    try:
        motores_raw = fetch_motores_cached(ctx.supabase)
    except Exception as e:
        st.error(f"Erro ao carregar motores do banco: {e}")
        return

    if not motores_raw:
        st.info("Nenhum motor cadastrado no sistema.")
        return

    motores = [_normalize_motor_record(m) for m in motores_raw]

    busca = st.text_input(
        "Pesquisar",
        placeholder="Arquivo, modelo, potência, RPM, tensão, corrente..."
    ).strip().lower()

    filtrados = [m for m in motores if busca in _search_blob(m)] if busca else motores

    st.sidebar.markdown("### Filtros da consulta")

    marcas = _unique_values(motores, "marca")
    marca = st.sidebar.selectbox(
        "Marca",
        ["Todas"] + marcas,
        key="consulta_filtro_marca",
    )
    if marca != "Todas":
        filtrados = [m for m in filtrados if _to_text(m.get("marca")) == marca]

    tipos_arquivo = _unique_values(motores, "tipo_arquivo")
    tipo_arquivo = st.sidebar.selectbox(
        "Tipo de arquivo",
        ["Todos"] + tipos_arquivo,
        key="consulta_filtro_tipo_arquivo",
    )
    if tipo_arquivo != "Todos":
        filtrados = [m for m in filtrados if _to_text(m.get("tipo_arquivo")) == tipo_arquivo]

    status_list = _unique_values(motores, "status_leitura")
    status = st.sidebar.selectbox(
        "Status de leitura",
        ["Todos"] + status_list,
        key="consulta_filtro_status",
    )
    if status != "Todos":
        filtrados = [m for m in filtrados if _to_text(m.get("status_leitura")) == status]

    confiancas = _unique_values(motores, "confianca_predominante")
    confianca = st.sidebar.selectbox(
        "Confiança",
        ["Todas"] + confiancas,
        key="consulta_filtro_confianca",
    )
    if confianca != "Todas":
        filtrados = [m for m in filtrados if _to_text(m.get("confianca_predominante")) == confianca]

    if not filtrados:
        st.warning("Nenhum motor encontrado.")
        return

    st.caption(f"Resultados encontrados: {len(filtrados)}")

    for motor in filtrados:
        try:
            action = render_motor_card(motor)
        except Exception as e:
            st.error(
                f"Erro ao renderizar card do motor '{motor.get('arquivo_nome', 'sem nome')}': {e}"
            )
            continue

        if action == "detail":
            ctx.session.selected_motor_id = motor["id"]
            ctx.session.set_route(Route.DETALHE)
            st.rerun()

        elif action == "edit":
            ctx.session.selected_motor_id = motor["id"]
            ctx.session.set_route(Route.EDIT)
            st.rerun()
