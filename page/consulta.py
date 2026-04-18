from __future__ import annotations

import html
import json
import math
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


def _extract_eixo_xy(mecanica: Dict[str, Any]) -> tuple[str, str]:
    eixo_raw = _to_text(mecanica.get("eixo"))
    medidas_raw = _join_values(mecanica.get("medidas"))
    combined = " | ".join(v for v in [eixo_raw, medidas_raw] if _to_text(v))
    if not combined:
        return "-", "-"

    match = re.search(r"(\d+(?:[.,]\d+)?)\s*[xX×/]\s*(\d+(?:[.,]\d+)?)", combined)
    if match:
        return match.group(1).replace(",", "."), match.group(2).replace(",", ".")

    numbers = re.findall(r"\d+(?:[.,]\d+)?", combined)
    if len(numbers) >= 2:
        return numbers[0].replace(",", "."), numbers[1].replace(",", ".")
    if numbers:
        return numbers[0].replace(",", "."), "-"
    return "-", "-"


def _parse_float_token(token: str) -> float | None:
    txt = str(token or "").strip().replace(",", ".")
    if not txt:
        return None
    if "/" in txt:
        parts = [p.strip() for p in txt.split("/") if p.strip()]
        if len(parts) == 2:
            try:
                num = float(parts[0])
                den = float(parts[1])
                if den != 0:
                    return num / den
            except Exception:
                pass
    try:
        return float(txt)
    except Exception:
        return None


def _parse_power_kw(potencia: Any) -> float | None:
    txt = _to_text(potencia).lower()
    if not txt:
        return None
    number_match = re.search(r"(\d+(?:[.,]\d+)?(?:\s*/\s*\d+(?:[.,]\d+)?)?)", txt)
    if not number_match:
        return None
    raw_value = number_match.group(1).replace(" ", "")
    base = _parse_float_token(raw_value)
    if base is None or base <= 0:
        return None

    if "kw" in txt:
        return base
    if "hp" in txt:
        return base * 0.746
    # Base principal da plataforma costuma estar em CV/cavalaria.
    return base * 0.7355


def _parse_numeric_list(value: Any) -> List[float]:
    txt = _to_text(value)
    if not txt:
        return []
    tokens = re.findall(r"\d+(?:[.,]\d+)?", txt)
    out: List[float] = []
    for token in tokens:
        try:
            n = float(token.replace(",", "."))
        except Exception:
            continue
        out.append(n)
    return out


def _parse_voltage_options(value: Any) -> List[float]:
    vals = [v for v in _parse_numeric_list(value) if 24 <= v <= 15000]
    if not vals:
        return []
    dedup = sorted(set(vals))
    return dedup[:4]


def _parse_poles(polos: Any) -> int | None:
    txt = _to_text(polos).upper()
    if not txt:
        return None
    match = re.search(r"(\d{1,2})", txt)
    if not match:
        return None
    try:
        n = int(match.group(1))
    except Exception:
        return None
    return n if n > 0 else None


def _phase_kind(fases: Any) -> str:
    txt = _to_text(fases).lower()
    if not txt:
        return "unknown"
    if "tri" in txt or "3" in txt:
        return "trifasico"
    if "mono" in txt or "1" in txt:
        return "monofasico"
    return "unknown"


def _estimate_nominal_current(power_kw: float, voltage: float, phase_kind: str) -> float:
    # Estimativa prática para triagem em campo (faixas amplas por falta de η e cosφ reais).
    if phase_kind == "trifasico":
        eff_pf = 0.72
        return (power_kw * 1000.0) / (math.sqrt(3.0) * voltage * eff_pf)
    eff_pf = 0.62
    return (power_kw * 1000.0) / (voltage * eff_pf)


def _evaluate_motor_consistency(m: Dict[str, Any]) -> Dict[str, Any]:
    data = m.get("dados_tecnicos_json", {})
    motor_info = _section(data, "motor")
    mecanica = _section(data, "mecanica")
    eixo_x, eixo_y = _extract_eixo_xy(mecanica)

    fase_txt = _to_text(m.get("fases")) or _to_text(motor_info.get("fases"))
    polos_txt = _to_text(m.get("polos")) or _to_text(motor_info.get("polos"))
    rpm_txt = _to_text(m.get("rpm")) or _to_text(motor_info.get("rpm"))
    pot_txt = _to_text(m.get("potencia")) or _to_text(motor_info.get("potencia") or motor_info.get("cv"))
    corrente_txt = _to_text(m.get("corrente")) or _to_text(motor_info.get("corrente"))
    tensao_txt = _to_text(m.get("tensao")) or _to_text(motor_info.get("tensao"))

    missing: List[str] = []
    essentials = {
        "rpm": rpm_txt,
        "cavalaria": pot_txt,
        "amperagem": corrente_txt,
        "polaridade": polos_txt,
        "fase (mono/trifásico)": fase_txt,
        "eixo x": eixo_x if eixo_x != "-" else "",
        "eixo y": eixo_y if eixo_y != "-" else "",
    }
    for label, value in essentials.items():
        if not _to_text(value):
            missing.append(label)

    warnings: List[str] = []
    severe: List[str] = []

    phase_kind = _phase_kind(fase_txt)
    if phase_kind == "unknown":
        warnings.append("Tipo de fase não identificado com clareza (mono/trifásico).")

    poles = _parse_poles(polos_txt)
    if poles is not None and poles not in {2, 4, 6, 8, 10, 12}:
        severe.append(f"Polaridade fora do padrão industrial comum: {poles}.")

    rpm_values = [v for v in _parse_numeric_list(rpm_txt) if 100 <= v <= 10000]
    rpm = rpm_values[0] if rpm_values else None
    freq_values = [v for v in _parse_numeric_list(motor_info.get("frequencia")) if 40 <= v <= 70]
    freq = freq_values[0] if freq_values else 60.0

    if rpm is not None and poles is not None and poles > 0:
        ns = (120.0 * freq) / poles
        ratio = rpm / ns if ns > 0 else 0.0
        if ratio > 1.04 or ratio < 0.45:
            severe.append(
                f"RPM ({rpm:.0f}) muito incompatível com {poles} polos @ {freq:.0f}Hz (síncrona ~{ns:.0f})."
            )
        elif ratio > 1.00 or ratio < 0.70:
            warnings.append(
                f"RPM ({rpm:.0f}) fora da faixa típica para {poles} polos @ {freq:.0f}Hz."
            )

    power_kw = _parse_power_kw(pot_txt)
    currents = [v for v in _parse_numeric_list(corrente_txt) if v > 0]
    voltages = _parse_voltage_options(tensao_txt)
    if power_kw and currents and voltages and phase_kind in {"trifasico", "monofasico"}:
        estimated = [_estimate_nominal_current(power_kw, v, phase_kind) for v in voltages if v > 0]
        if estimated:
            best_rel = min(abs(i_m - i_e) / max(i_e, 0.1) for i_m in currents for i_e in estimated)
            if best_rel > 1.8:
                severe.append("Amperagem muito fora do esperado para potência/tensão/fase informadas.")
            elif best_rel > 0.9:
                warnings.append("Amperagem com desvio alto em relação ao esperado para potência/tensão/fase.")
    elif power_kw and phase_kind in {"trifasico", "monofasico"} and not voltages:
        warnings.append("Sem tensão válida para conferir coerência da amperagem.")

    if power_kw is None and pot_txt:
        warnings.append("Potência/CV informada em formato não interpretável para validação.")

    if len(missing) >= 4 and (warnings or severe):
        severe.append("Dados essenciais insuficientes para confiança técnica no cadastro.")

    if severe:
        categoria = "desnivelados"
    elif missing:
        categoria = "faltando_essencial"
    else:
        categoria = "aparentemente_certos"

    score = max(0, min(100, 100 - (30 * len(severe)) - (12 * len(warnings)) - (10 * len(missing))))
    motor_label = f"{_to_text(m.get('marca')) or 'Motor'} {_to_text(m.get('modelo')) or ''}".strip()
    return {
        "id": _to_text(m.get("id")) or "-",
        "motor": motor_label,
        "categoria": categoria,
        "score": int(score),
        "faltas": missing,
        "alertas": severe + warnings,
    }


def _to_report_table(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for e in entries:
        out.append(
            {
                "ID": e.get("id"),
                "Motor": e.get("motor"),
                "Score": e.get("score"),
                "Faltas essenciais": ", ".join(e.get("faltas") or []) or "-",
                "Alertas técnicos": ", ".join(e.get("alertas") or []) or "-",
            }
        )
    return out


def _render_consistency_report(motores: List[Dict[str, Any]]) -> None:
    if not motores:
        st.caption("Sem motores para analisar com os filtros atuais.")
        return

    analyzed = [_evaluate_motor_consistency(m) for m in motores]
    groups = {
        "aparentemente_certos": [e for e in analyzed if e["categoria"] == "aparentemente_certos"],
        "faltando_essencial": [e for e in analyzed if e["categoria"] == "faltando_essencial"],
        "desnivelados": [e for e in analyzed if e["categoria"] == "desnivelados"],
    }

    c1, c2, c3 = st.columns(3)
    c1.metric("Aparentemente certos", len(groups["aparentemente_certos"]))
    c2.metric("Faltando essencial", len(groups["faltando_essencial"]))
    c3.metric("Totalmente desnivelados", len(groups["desnivelados"]))
    st.caption(
        "Análise automática de triagem técnica (heurística). Sempre confirme em bancada/engenharia antes de decisão final."
    )

    tab_ok, tab_missing, tab_bad = st.tabs(
        [
            "Cálculos certos / coerentes",
            "Faltando essencial",
            "Totalmente desnivelados",
        ]
    )

    with tab_ok:
        if groups["aparentemente_certos"]:
            st.dataframe(_to_report_table(groups["aparentemente_certos"]), use_container_width=True, hide_index=True)
        else:
            st.caption("Nenhum motor caiu neste grupo com os filtros atuais.")

    with tab_missing:
        if groups["faltando_essencial"]:
            st.dataframe(_to_report_table(groups["faltando_essencial"]), use_container_width=True, hide_index=True)
        else:
            st.caption("Nenhum motor com falta essencial nos filtros atuais.")

    with tab_bad:
        if groups["desnivelados"]:
            st.dataframe(_to_report_table(groups["desnivelados"]), use_container_width=True, hide_index=True)
        else:
            st.caption("Nenhum motor classificado como totalmente desnivelado nos filtros atuais.")


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

    with st.expander("Analise tecnica dos calculos (Consulta)", expanded=False):
        _render_consistency_report(filtrados)

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
            mecanica = _section(data, "mecanica")

            motor_id_txt = _to_text(m.get("id")) or "sem_id"
            motor_key = re.sub(r"[^a-zA-Z0-9_-]", "_", motor_id_txt)
            eixo_x, eixo_y = _extract_eixo_xy(mecanica)
            fase_txt = _to_text(m.get("fases")) or _to_text(motor_info.get("fases"))

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
                with st.expander("Informacoes essenciais do motor", expanded=False):
                    k1, k2, k3 = st.columns(3)
                    k1.markdown(
                        f'<div class="metric-tile"><span>Cavalaria</span><strong>{_safe(m.get("potencia"))}</strong></div>',
                        unsafe_allow_html=True,
                    )
                    k2.markdown(
                        f'<div class="metric-tile"><span>RPM</span><strong>{_safe(m.get("rpm"))}</strong></div>',
                        unsafe_allow_html=True,
                    )
                    k3.markdown(
                        f'<div class="metric-tile"><span>Amperagem</span><strong>{_safe(m.get("corrente"))}</strong></div>',
                        unsafe_allow_html=True,
                    )

                    d1, d2, d3 = st.columns(3)
                    d1.markdown(
                        f'<div class="inline-pill">Polaridade: <b>{_safe(m.get("polos"))}</b></div>',
                        unsafe_allow_html=True,
                    )
                    d2.markdown(
                        f'<div class="inline-pill">Fase: <b>{_safe(fase_txt)}</b></div>',
                        unsafe_allow_html=True,
                    )
                    d3.markdown(
                        f'<div class="inline-pill">Tensao: <b>{_safe(m.get("tensao"))}</b></div>',
                        unsafe_allow_html=True,
                    )

                    e1, e2 = st.columns(2)
                    e1.markdown(
                        f'<div class="inline-pill">Eixo X: <b>{_safe(eixo_x)}</b></div>',
                        unsafe_allow_html=True,
                    )
                    e2.markdown(
                        f'<div class="inline-pill">Eixo Y: <b>{_safe(eixo_y)}</b></div>',
                        unsafe_allow_html=True,
                    )
                if _to_text(m.get("feito_por")):
                    st.caption(f"Feito por: {_to_text(m.get('feito_por'))}")

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
                    if st.button("Abrir detalhes", key=f"detail_{motor_key}", use_container_width=True):
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
                if st.button("Abrir detalhes", key=f"detail_{motor_key}", use_container_width=True):
                    ctx.session.selected_motor_id = m["id"]
                    ctx.session.set_route(Route.DETALHE)
                    st.rerun()


def show(ctx) -> None:
    return render(ctx)
