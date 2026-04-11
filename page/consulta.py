from __future__ import annotations

import html
import json
import os
import re
from typing import Any, Dict, List
from urllib.parse import quote_plus

import streamlit as st

from core.access_control import can_access_paid_features, is_admin_user
from core.navigation import Route
from services.oficina_parser import build_normalized_from_motor_row
from services.supabase_data import clear_motores_cache, fetch_motores_cached


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


def _read_secret_or_env(*names: str) -> str:
    for name in names:
        try:
            value = st.secrets.get(name)
            if value:
                return str(value).strip()
        except Exception:
            pass
        value = os.environ.get(name)
        if value:
            return str(value).strip()
    return ""


def _resolve_upgrade_whatsapp() -> tuple[str, str]:
    raw_phone = _read_secret_or_env(
        "WHATSAPP_UPGRADE_NUMBER",
        "UPGRADE_WHATSAPP_NUMBER",
        "WHATSAPP_NUMBER",
    ) or "31 994211750"
    phone = re.sub(r"\D+", "", raw_phone)
    if phone.startswith("00"):
        phone = phone[2:]
    # Conveniencia para numero BR informado sem DDI.
    if len(phone) == 11 and not phone.startswith("55"):
        phone = f"55{phone}"
    if len(phone) < 10:
        return "", ""

    default_msg = "Oi! Quero ativar o plano pago do Moto-Renow."
    message = _read_secret_or_env(
        "WHATSAPP_UPGRADE_MESSAGE",
        "UPGRADE_WHATSAPP_MESSAGE",
    ) or default_msg
    url = f"https://wa.me/{phone}?text={quote_plus(message)}"
    return url, message


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


def _extract_feito_por(row: Dict[str, Any], data: Dict[str, Any]) -> str:
    direct = _pick_first(
        row,
        "cadastrado_por_nome",
        "cadastrado_por_username",
        "cadastrado_por_email",
        "created_by_name",
        "created_by",
        "usuario",
        "autor",
        "Usuario",
    )
    if direct:
        return direct

    meta = data.get("meta", {}) if isinstance(data, dict) else {}
    if isinstance(meta, dict):
        meta_value = (
            _to_text(meta.get("cadastrado_por_display"))
            or _to_text(meta.get("cadastrado_por_nome"))
            or _to_text(meta.get("cadastrado_por_username"))
            or _to_text(meta.get("cadastrado_por_email"))
        )
        if meta_value:
            return meta_value

    oficina = data.get("oficina", {}) if isinstance(data, dict) else {}
    servico = oficina.get("servico_executado", {}) if isinstance(oficina, dict) else {}
    if isinstance(servico, dict):
        responsavel = _to_text(servico.get("responsavel"))
        if responsavel:
            return responsavel

    obs = _to_text(row.get("observacoes") or row.get("Observacoes"))
    match = re.search(r"feito por\s*:\s*([^\|]+)", obs, flags=re.IGNORECASE)
    if match:
        return _to_text(match.group(1))

    return ""


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

    feito_por = _extract_feito_por(row, data)

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
        "feito_por": feito_por,
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


def _compact_preview(value: Any, max_len: int = 56) -> str:
    txt = _to_text(value)
    if not txt:
        return "-"
    if len(txt) <= max_len:
        return txt
    return txt[: max_len - 3].rstrip() + "..."


def _delete_motor(ctx, motor_id: Any) -> None:
    motor_id_txt = _to_text(motor_id)
    if not motor_id_txt:
        raise RuntimeError("ID do motor invalido para exclusao.")

    last_error: Exception | None = None
    for id_col in ("id", "Id"):
        try:
            ctx.supabase.table("motores").delete().eq(id_col, motor_id_txt).execute()
            clear_motores_cache()
            return
        except Exception as exc:
            last_error = exc

    raise RuntimeError(f"Nao foi possivel excluir o motor {motor_id_txt}: {last_error}")


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


def _render_teaser_consulta(motores: List[Dict[str, Any]], admin_user: bool = False) -> None:
    st.markdown(
        """
        <div class="consulta-hero">
            <div class="consulta-hero__tag">MODO TEASER</div>
            <h1>Catalogo Tecnico (Visualizacao)</h1>
            <p>Voce esta vendo uma previa. Para liberar todos os recursos, ative o plano pago.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.info("Plano gratuito: visualizacao limitada. Fale com o admin para ativar seu acesso completo.")
    st.markdown(
        """
**Plano pago libera:**
- Consulta completa com filtros e detalhes tecnicos.
- Diagnostico tecnico no painel dedicado.
- Acesso ao cadastro tecnico de motores.
        """
    )

    wa_url, wa_message = _resolve_upgrade_whatsapp()
    if wa_url:
        c1, c2 = st.columns([1.6, 1.2], gap="small")
        with c1:
            try:
                st.link_button(
                    "Falar no WhatsApp para liberar plano",
                    wa_url,
                    use_container_width=True,
                )
            except Exception:
                st.markdown(f"[Falar no WhatsApp para liberar plano]({wa_url})")
        with c2:
            if st.button("Mostrar link para copiar", use_container_width=True, key="teaser_whatsapp_copy_btn"):
                st.session_state["teaser_whatsapp_show_link"] = True
        if st.session_state.get("teaser_whatsapp_show_link"):
            st.text_input("Link de upgrade (copiar e enviar)", value=wa_url, key="teaser_whatsapp_link_field")
            st.text_area("Mensagem padrao", value=wa_message, key="teaser_whatsapp_message_field", height=80)
    elif admin_user:
        st.caption(
            "Configure WHATSAPP_UPGRADE_NUMBER (com DDI, ex: 5511999999999) em secrets/env para mostrar CTA de upgrade."
        )

    amostra = motores[:8]
    for m in amostra:
        with st.container(border=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.caption("Marca")
                st.write(_to_text(m.get("marca")) or "-")
            with c2:
                st.caption("Modelo")
                st.write(_to_text(m.get("modelo")) or "-")
            with c3:
                st.caption("Potencia")
                st.write(_to_text(m.get("potencia")) or "-")
    if len(motores) > len(amostra):
        st.caption(f"Mostrando {len(amostra)} de {len(motores)} motores no teaser.")


def render(ctx) -> None:
    admin_user = is_admin_user()
    paid_user = can_access_paid_features(ctx.supabase)

    try:
        raw = fetch_motores_cached(ctx.supabase)
    except Exception as e:
        st.error(f"Erro ao carregar motores: {e}")
        return

    if not raw:
        st.info("Nenhum motor cadastrado.")
        return

    motores = [_normalize_motor_record(r) for r in raw]

    if not paid_user:
        _render_teaser_consulta(motores, admin_user=admin_user)
        return

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

    pg1, pg2, pg3 = st.columns([1.2, 1.0, 3.0], gap="small")
    with pg1:
        page_size = st.selectbox("Itens por pagina", [10, 20, 50, 100], index=1, key="consulta_page_size")
    total_pages = max(1, (len(filtrados) + int(page_size) - 1) // int(page_size))
    current_page = int(st.session_state.get("consulta_page_num", 1) or 1)
    if current_page > total_pages:
        current_page = total_pages
        st.session_state["consulta_page_num"] = current_page
    with pg2:
        page_num = int(
            st.number_input(
                "Pagina",
                min_value=1,
                max_value=total_pages,
                value=current_page,
                step=1,
                key="consulta_page_num",
            )
        )
    with pg3:
        start = (page_num - 1) * int(page_size)
        end = start + int(page_size)
        st.caption(f"Mostrando {start + 1}-{min(end, len(filtrados))} de {len(filtrados)} motores.")

    motores_visiveis = filtrados[start:end]

    for m in motores_visiveis:
        with st.container(border=True):
            data = m.get("dados_tecnicos_json", {})
            motor_info = _section(data, "motor")
            bob_principal = _section(data, "bobinagem_principal")
            bob_auxiliar = _section(data, "bobinagem_auxiliar")
            mecanica = _section(data, "mecanica")
            esquema = _section(data, "esquema")

            motor_id_txt = _to_text(m.get("id")) or "sem_id"
            motor_key = re.sub(r"[^a-zA-Z0-9_-]", "_", motor_id_txt)
            principal_preview = _compact_preview(
                bob_principal.get("fios") or bob_principal.get("espiras") or bob_principal.get("passos")
            )
            auxiliar_preview = _compact_preview(
                bob_auxiliar.get("fios") or bob_auxiliar.get("espiras") or bob_auxiliar.get("passos")
            )
            rolamentos_preview = _compact_preview(mecanica.get("rolamentos"))
            eixo_carcaca_preview = _compact_preview(
                f"Eixo: {_to_text(mecanica.get('eixo')) or '-'} | Carcaca: {_to_text(mecanica.get('carcaca')) or '-'}"
            )

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
                if _to_text(m.get("feito_por")):
                    st.caption(f"Feito por: {_to_text(m.get('feito_por'))}")

                pv1, pv2 = st.columns(2)
                with pv1:
                    _render_data_panel("Rebobinagem principal (previa)", principal_preview)
                    _render_data_panel("Rebobinagem auxiliar (previa)", auxiliar_preview)
                with pv2:
                    _render_data_panel("Mecanica (rolamentos)", rolamentos_preview)
                    _render_data_panel("Mecanica (eixo/carcaca)", eixo_carcaca_preview)

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
                b1, b2, b3 = st.columns(3)
                with b1:
                    if st.button("Editar", key=f"edit_{motor_key}", use_container_width=True):
                        ctx.session.selected_motor_id = m["id"]
                        ctx.session.set_route(Route.EDIT)
                        st.rerun()
                with b2:
                    if st.button("Detalhes", key=f"detail_{motor_key}", use_container_width=True):
                        ctx.session.selected_motor_id = m["id"]
                        ctx.session.set_route(Route.DETALHE)
                        st.rerun()
                with b3:
                    if st.button("Excluir", key=f"delete_{motor_key}", use_container_width=True):
                        st.session_state[f"confirm_delete_{motor_key}"] = True

                if st.session_state.get(f"confirm_delete_{motor_key}"):
                    st.warning("Exclusao definitiva. Confirme abaixo para remover este motor do cadastro.")
                    c_confirm, c_cancel = st.columns(2)
                    with c_confirm:
                        if st.button("Confirmar exclusao", key=f"confirm_delete_btn_{motor_key}", use_container_width=True):
                            try:
                                _delete_motor(ctx, m.get("id"))
                                st.session_state.pop(f"confirm_delete_{motor_key}", None)
                                st.success("Motor excluido com sucesso.")
                                st.rerun()
                            except Exception as exc:
                                st.error(f"Falha ao excluir motor: {exc}")
                    with c_cancel:
                        if st.button("Cancelar", key=f"cancel_delete_btn_{motor_key}", use_container_width=True):
                            st.session_state.pop(f"confirm_delete_{motor_key}", None)
                            st.rerun()
            else:
                if st.button("Detalhes", key=f"detail_{motor_key}", use_container_width=True):
                    ctx.session.selected_motor_id = m["id"]
                    ctx.session.set_route(Route.DETALHE)
                    st.rerun()

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


def show(ctx) -> None:
    return render(ctx)
