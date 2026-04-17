from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List

import streamlit as st

from core.access_control import can_access_paid_features, is_admin_user
from core.navigation import Route
from services.supabase_data import fetch_motores_cached


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _to_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _parse_dt(value: Any) -> datetime | None:
    txt = _to_text(value)
    if not txt:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(txt[:19], fmt)
        except Exception:
            continue
    return None


def _count_recent(rows: List[Dict[str, Any]], days: int = 7) -> int:
    cutoff = datetime.utcnow() - timedelta(days=days)
    count = 0
    for r in rows:
        dt = _parse_dt(r.get("created_at")) or _parse_dt(r.get("updated_at"))
        if dt and dt >= cutoff:
            count += 1
    return count


def _count_ocr(rows: List[Dict[str, Any]]) -> int:
    count = 0
    for r in rows:
        payload = _to_dict(r.get("leitura_gemini_json")) or _to_dict(r.get("dados_tecnicos_json"))
        if payload:
            count += 1
    return count


def _fmt_int(value: int) -> str:
    try:
        return f"{int(value):,}".replace(",", ".")
    except Exception:
        return str(value)


def _kpi(label: str, value: Any, hint: str = "", *, icon: str = "MR", variant: str = "primary") -> None:
    variant_text = {
        "primary": "text-primary",
        "accent": "text-accent",
        "warning": "text-warning",
        "destructive": "text-destructive",
    }.get(variant, "text-primary")
    st.markdown(
        f"""
        <div class="premium-card kpi-card">
          <div class="kpi-card__top">
            <div class="kpi-card__icon">{icon}</div>
          </div>
          <div class="kpi-card__value">{value}</div>
          <div class="kpi-card__label">{label}</div>
          <div class="kpi-card__trend {variant_text}">{hint}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _pick_motor_title(row: Dict[str, Any]) -> str:
    marca = _to_text(row.get("marca")) or "Motor"
    modelo = (
        _to_text(row.get("modelo"))
        or _to_text(row.get("modelo_iec"))
        or _to_text(row.get("modelo_nema"))
        or ""
    )
    if modelo:
        return f"{marca} — {modelo}"
    return marca


def _row_stage(row: Dict[str, Any]) -> tuple[str, str, int]:
    has_ocr = bool(_to_dict(row.get("leitura_gemini_json")) or _to_dict(row.get("dados_tecnicos_json")))
    obs = _to_text(row.get("observacoes")).lower()
    if "inconsist" in obs or "revis" in obs:
        return ("REVISÃO", "badge-warning", 80)
    if has_ocr:
        return ("EM ANÁLISE", "badge-primary", 60)
    return ("PENDENTE", "", 15)


def _eta_label(row: Dict[str, Any]) -> str:
    dt = _parse_dt(row.get("created_at")) or _parse_dt(row.get("updated_at"))
    if not dt:
        return "—"
    age_h = (datetime.utcnow() - dt).total_seconds() / 3600.0
    if age_h < 20:
        return "Hoje"
    if age_h < 48:
        return "Amanhã"
    return "2+ dias"


def show(ctx) -> None:
    paid_user = can_access_paid_features(ctx.supabase)
    admin_user = is_admin_user()

    # Base de dados (fallback seguro)
    try:
        motores = fetch_motores_cached(ctx.supabase) or []
    except Exception as exc:
        st.error(f"Falha ao carregar dados para a Visão geral: {exc}")
        if st.button("Abrir Consulta Técnica", use_container_width=True):
            ctx.session.set_route(Route.CONSULTA)
            st.rerun()
        return

    total = len(motores)
    last7 = _count_recent(motores, days=7)
    ocr_total = _count_ocr(motores)

    # Header já vem do shell; aqui só conteúdo.
    c1, c2, c3, c4 = st.columns(4, gap="small")
    with c1:
        _kpi("Motores cadastrados", _fmt_int(total), f"+{_fmt_int(last7)} este período", icon="DB", variant="primary")
    with c2:
        _kpi("OCR concluído", _fmt_int(ocr_total), "+ esta semana", icon="OCR", variant="accent")
    with c3:
        _kpi("Diagnósticos emitidos", "—", "Em migração para API", icon="DIAG", variant="primary")
    with c4:
        _kpi("Cadastros c/ inconsistência", "—", "Requer revisão", icon="!", variant="warning")

    left, right = st.columns([1.7, 1.0], gap="large")
    with left:
        st.markdown(
            """
            <div class="premium-card-elevated">
              <div class="panel-header">
                <div>
                  <div class="panel-title">FILA DE TRABALHO</div>
                  <div class="panel-subtitle">Motores em análise técnica neste workspace</div>
                </div>
                <span class="badge-premium badge-primary">ATIVOS</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        recent = list(reversed(motores))[-6:]
        if recent:
            st.markdown('<div class="premium-card-elevated">', unsafe_allow_html=True)
            for r in reversed(recent):
                motor_id = _to_text(r.get("id") or r.get("Id") or "") or "M-—"
                title = _pick_motor_title(r)
                status_label, status_cls, progress = _row_stage(r)
                eta = _eta_label(r)
                badge = (
                    f'<span class="badge-premium {status_cls}">{status_label}</span>'
                    if status_cls
                    else f'<span class="badge-premium">{status_label}</span>'
                )
                st.markdown(
                    f"""
                    <div class="queue-item">
                      <div class="queue-row">
                        <div class="queue-icon">MR</div>
                        <div class="queue-meta">
                          <div class="queue-idline">
                            <span class="queue-id">{motor_id}</span>
                            {badge}
                          </div>
                          <div class="queue-title">{title}</div>
                          <div class="queue-stage">Etapa: {status_label.title()}</div>
                        </div>
                        <div class="queue-right">
                          <div class="queue-right-top">
                            <span>Progresso</span><span class="queue-id">{progress}%</span>
                          </div>
                          <div class="progress-premium">
                            <div class="progress-premium-fill" style="width:{progress}%"></div>
                          </div>
                          <div class="queue-eta">ETA: {eta}</div>
                        </div>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)

        a, b, c = st.columns(3, gap="small")
        with a:
            if st.button("Abrir Consulta", use_container_width=True):
                ctx.session.set_route(Route.CONSULTA)
                st.rerun()
        with b:
            if st.button("Novo Cadastro / OCR", use_container_width=True, disabled=not paid_user):
                ctx.session.set_route(Route.CADASTRO)
                st.rerun()
        with c:
            if st.button("Diagnóstico", use_container_width=True, disabled=not paid_user):
                ctx.session.set_route(Route.DIAGNOSTICO)
                st.rerun()

        if not paid_user:
            st.info("Alguns recursos estão em modo teaser. O legado segue disponível via Consulta.")

        with st.container(border=True):
            st.markdown("### Atividade técnica — últimos 7 dias")
            st.caption("Resumo simples enquanto a API nova é ligada.")
            st.write(f"- Novos registros: **{last7}**")
            st.write(f"- Registros com OCR/IA: **{ocr_total}**")

    with right:
        st.markdown(
            """
            <div class="premium-card p-5">
              <div class="panel-title" style="margin-bottom: 10px;">AÇÕES PENDENTES</div>
              <div style="display:flex; flex-direction:column; gap:10px;">
                <div class="premium-card" style="padding:10px 12px; background: rgba(9,16,29,0.45);">
                  <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:0.82rem; font-weight:700; color:#e9f7ff;">Cálculos pendentes de conferência</span>
                    <span class="text-warning" style="font-family:Orbitron; font-weight:900;">—</span>
                  </div>
                </div>
                <div class="premium-card" style="padding:10px 12px; background: rgba(9,16,29,0.45);">
                  <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:0.82rem; font-weight:700; color:#e9f7ff;">OCRs aguardando revisão</span>
                    <span class="text-primary" style="font-family:Orbitron; font-weight:900;">—</span>
                  </div>
                </div>
                <div class="premium-card" style="padding:10px 12px; background: rgba(9,16,29,0.45);">
                  <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:0.82rem; font-weight:700; color:#e9f7ff;">Inconsistências detectadas</span>
                    <span class="text-destructive" style="font-family:Orbitron; font-weight:900;">—</span>
                  </div>
                </div>
                <div class="premium-card" style="padding:10px 12px; background: rgba(9,16,29,0.45);">
                  <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:0.82rem; font-weight:700; color:#e9f7ff;">Laudos em redação</span>
                    <span class="text-accent" style="font-family:Orbitron; font-weight:900;">—</span>
                  </div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if admin_user:
            st.caption("Admin: estes itens serão alimentados pela API conforme migração.")

        st.markdown(
            """
            <div class="premium-card p-5" style="margin-top: 16px;">
              <div class="panel-title">ORIGEM DOS DADOS</div>
              <div class="panel-subtitle">Distribuição da base por fonte de captação</div>
              <div style="margin-top: 12px;" class="progress-premium">
                <div class="progress-premium-fill" style="width:58%"></div>
              </div>
              <div style="display:flex; justify-content:space-between; margin-top:10px; font-size:0.78rem;">
                <span class="text-primary">OCR</span><span class="queue-id">58%</span>
              </div>
              <div style="display:flex; justify-content:space-between; margin-top:6px; font-size:0.78rem;">
                <span class="text-accent">Manual</span><span class="queue-id">24%</span>
              </div>
              <div style="display:flex; justify-content:space-between; margin-top:6px; font-size:0.78rem;">
                <span class="text-warning">Histórico</span><span class="queue-id">12%</span>
              </div>
              <div style="display:flex; justify-content:space-between; margin-top:6px; font-size:0.78rem;">
                <span class="text-destructive">Inferido</span><span class="queue-id">6%</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

