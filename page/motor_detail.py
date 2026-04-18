from __future__ import annotations

import html
import re
import streamlit as st

from core.access_control import is_admin_user, require_paid_access
from core.navigation import Route
from services.supabase_data import fetch_motor_by_id_cached
from components.motor_hologram import render_engine_hologram
from utils.motor_normalizer import normalize_motor_row_for_ui
from utils.motor_view import dados_tecnicos_from_row, friendly, is_empty, normalize_motor_record


def _section(data, key: str) -> dict:
    value = data.get(key) if isinstance(data, dict) else {}
    return value if isinstance(value, dict) else {}


def _to_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _join_values(value) -> str:
    if isinstance(value, list):
        items = [str(v).strip() for v in value if str(v).strip()]
        return ", ".join(items) if items else "-"
    txt = str(value).strip() if value is not None else ""
    return txt if txt else "-"


def _render_data_panel(label: str, value) -> None:
    st.markdown(
        f"""
        <div class="data-panel">
            <div class="data-label">{html.escape(label)}</div>
            <div class="data-value">{html.escape(_join_values(value))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render(ctx) -> None:
    if not require_paid_access("Detalhes do motor", client=ctx.supabase):
        if st.button("Voltar para consulta", use_container_width=True):
            ctx.session.set_route(Route.CONSULTA)
            st.rerun()
        return

    admin_user = is_admin_user()

    motor_id = ctx.session.selected_motor_id
    if motor_id is None:
        st.warning("Nenhum motor selecionado para detalhe.")
        if st.button("Voltar para consulta", use_container_width=True):
            ctx.session.set_route(Route.CONSULTA)
            st.rerun()
        return

    motor = fetch_motor_by_id_cached(ctx.supabase, motor_id)
    if motor is None:
        st.error(f"Motor {motor_id} nao encontrado.")
        if st.button("Voltar para consulta", use_container_width=True):
            ctx.session.set_route(Route.CONSULTA)
            st.rerun()
        return

    motor_row = dict(motor)
    seq_sess = st.session_state.get(f"motor_cadastro_seq_{motor_id}")
    if seq_sess is not None:
        try:
            motor_row["cadastro_seq"] = int(seq_sess)
        except (TypeError, ValueError):
            pass

    m = normalize_motor_record(motor_row)
    dados = dados_tecnicos_from_row(m)
    motor_info = _section(dados, "motor")
    ui = normalize_motor_row_for_ui(motor)

    if is_empty(m.get("marca")) and not is_empty(motor_info.get("marca")):
        m["marca"] = motor_info.get("marca")
    modelo_row = str(m.get("modelo") or "").strip()
    inner_mod = motor_info.get("modelo")
    if not is_empty(inner_mod) and (
        is_empty(m.get("modelo"))
        or re.match(r"(?i)^registro\s+#?n[aã]o\s+informado\s*$", modelo_row)
        or re.match(r"(?i)^registro\s+\d+\s*$", modelo_row)
    ):
        m["modelo"] = inner_mod
    if is_empty(m.get("fases")) and not is_empty(motor_info.get("fases")):
        m["fases"] = motor_info.get("fases")

    seq_disp = st.session_state.get(f"motor_cadastro_seq_{motor_id}")
    if seq_disp is not None:
        try:
            sd = int(seq_disp)
            mod_now = _to_text(m.get("modelo"))
            mid = str(m.get("id") or motor_id or "").strip()
            if (not mod_now or mod_now == "Sem modelo") and mid:
                m["modelo"] = f"Registro #{sd}"
            elif mod_now.lower().startswith("registro"):
                tail = re.sub(r"(?i)^registro\s+#?\s*", "", mod_now).strip()
                if not tail or tail == mid or tail.replace("-", "").replace(" ", "") == mid.replace("-", "").replace(
                    " ", ""
                ):
                    m["modelo"] = f"Registro #{sd}"
        except (TypeError, ValueError):
            pass

    chip_fases = m.get("fases") or motor_info.get("fases") or ui.get("tipo_motor")

    id_badge = seq_disp if seq_disp is not None else motor_id

    st.markdown(
        f"""
        <div class="motor-headline">
            <div>
                <div class="motor-id">#{html.escape(str(id_badge))}</div>
                <div class="motor-title">{friendly(m.get('marca'))} <span>{friendly(m.get('modelo'))}</span></div>
            </div>
            <div class="motor-chip">{friendly(chip_fases)} | {friendly(m.get('polos'))} polos</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(
        f'<div class="metric-tile"><span>Potência</span><strong>{friendly(m.get("potencia_hp_cv"))}</strong></div>',
        unsafe_allow_html=True,
    )
    k2.markdown(
        f'<div class="metric-tile"><span>RPM</span><strong>{friendly(m.get("rpm_nominal"))}</strong></div>',
        unsafe_allow_html=True,
    )
    k3.markdown(
        f'<div class="metric-tile"><span>Tensão</span><strong>{friendly(m.get("tensao_v"))}</strong></div>',
        unsafe_allow_html=True,
    )
    k4.markdown(
        f'<div class="metric-tile"><span>Corrente</span><strong>{friendly(m.get("corrente_nominal_a"))}</strong></div>',
        unsafe_allow_html=True,
    )

    holo_m = dict(m)
    holo_m["dados_tecnicos_json"] = dados
    holo_m["rpm"] = holo_m.get("rpm_nominal") or holo_m.get("rpm")
    holo_m["tensao"] = holo_m.get("tensao_v") or holo_m.get("tensao")
    holo_m["corrente"] = holo_m.get("corrente_nominal_a") or holo_m.get("corrente")
    holo_m["fases"] = holo_m.get("fases")
    holo_m["tipo_motor"] = holo_m.get("tipo_motor")
    if holo_m.get("cadastro_seq") in (None, "") and seq_sess is not None:
        holo_m["cadastro_seq"] = seq_sess
    holo_left, holo_right = st.columns([1.25, 1.0], gap="medium")
    with holo_left:
        st.caption(
            "Holograma GLB (starter pack em data URL): aqui há só um viewer WebGL — deve manter-se estável. "
            "Na consulta a listagem usa Three.js leve; GLB completo neste ecrã."
        )
    with holo_right:
        render_engine_hologram(holo_m, key=f"motor_detail_holo_{motor_id}")

    bob_principal = _section(dados, "bobinagem_principal")
    bob_auxiliar = _section(dados, "bobinagem_auxiliar")
    mecanica = _section(dados, "mecanica")
    esquema = _section(dados, "esquema")
    oficina = _section(dados, "oficina")
    resultado = _section(oficina, "resultado_pos_servico")
    diagnostico = _section(oficina, "diagnostico")
    historico = oficina.get("historico_tecnico", []) if isinstance(oficina, dict) else []

    tab1, tab2, tab3, tab4 = st.tabs(["Identificação", "Rebobinagem", "Mecânica", "Oficina / IA"])

    with tab1:
        c1, c2, c3 = st.columns(3)
        with c1:
            _render_data_panel("Marca", m.get("marca") or motor_info.get("marca"))
            _render_data_panel("Modelo", m.get("modelo") or motor_info.get("modelo"))
            _render_data_panel(
                "Tipo do motor",
                motor_info.get("tipo_motor") or ui.get("tipo_motor") or m.get("fases"),
            )
        with c2:
            _render_data_panel("Fases", m.get("fases") or motor_info.get("fases"))
            _render_data_panel("Polos", m.get("polos") or ui.get("polos"))
            _render_data_panel(
                "Frequência",
                motor_info.get("frequencia") or m.get("frequencia_hz") or ui.get("frequencia"),
            )
        with c3:
            _render_data_panel("Número de série", motor_info.get("numero_serie"))
            _render_data_panel("IP", motor_info.get("ip"))
            _render_data_panel("Isolação", motor_info.get("isolacao"))

    with tab2:
        bb1, bb2 = st.columns(2)
        with bb1:
            _render_data_panel(
                "Passos principais",
                bob_principal.get("passos") or ui.get("passo_principal"),
            )
            _render_data_panel(
                "Espiras principais",
                bob_principal.get("espiras") or ui.get("espiras_principal"),
            )
            _render_data_panel(
                "Fio principal",
                bob_principal.get("fios") or ui.get("fio_principal"),
            )
            _render_data_panel(
                "Ligação principal",
                bob_principal.get("ligacao") or ui.get("ligacao_principal"),
            )
            _render_data_panel("Qtd. grupos", bob_principal.get("quantidade_grupos"))
            _render_data_panel("Qtd. bobinas", bob_principal.get("quantidade_bobinas"))
        with bb2:
            _render_data_panel(
                "Passos auxiliares",
                bob_auxiliar.get("passos") or ui.get("passo_auxiliar"),
            )
            _render_data_panel(
                "Espiras auxiliares",
                bob_auxiliar.get("espiras") or ui.get("espiras_auxiliar"),
            )
            _render_data_panel(
                "Fio auxiliar",
                bob_auxiliar.get("fios") or ui.get("fio_auxiliar"),
            )
            _render_data_panel(
                "Ligação auxiliar",
                bob_auxiliar.get("ligacao") or ui.get("ligacao_auxiliar"),
            )
            _render_data_panel("Capacitor", bob_auxiliar.get("capacitor"))
            _render_data_panel("Obs. bobinagem", bob_principal.get("observacoes") or bob_auxiliar.get("observacoes"))

    with tab3:
        mc1, mc2 = st.columns(2)
        with mc1:
            _render_data_panel("Rolamentos", mecanica.get("rolamentos"))
            _render_data_panel("Eixo", mecanica.get("eixo") or ui.get("eixo"))
            _render_data_panel("Carcaça", mecanica.get("carcaca") or ui.get("carcaca"))
            _render_data_panel("Comprimento ponta", mecanica.get("comprimento_ponta"))
            _render_data_panel("Obs. mecânica", mecanica.get("observacoes"))
        with mc2:
            _render_data_panel("Medidas", mecanica.get("medidas") or ui.get("medidas"))
            _render_data_panel("Esquema de ligação", esquema.get("ligacao"))
            _render_data_panel("Ranhuras", esquema.get("ranhuras"))
            _render_data_panel("Camadas", esquema.get("camadas"))
            _render_data_panel("Distribuição bobinas", esquema.get("distribuicao_bobinas"))

    with tab4:
        _render_data_panel("Status oficina", resultado.get("status"))
        _render_data_panel("Observações pós-serviço", resultado.get("observacoes"))
        _render_data_panel("Historico técnico", f"{len(historico) if isinstance(historico, list) else 0} registro(s)")
        avisos = diagnostico.get("avisos", []) if isinstance(diagnostico, dict) else []
        if isinstance(avisos, list) and avisos:
            st.markdown("**Diagnóstico da oficina**")
            for aviso in avisos[:8]:
                st.write(f"- {aviso}")
        else:
            st.caption("Sem alertas técnicos registrados pela IA para este motor.")

    if admin_user:
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Editar motor", use_container_width=True):
                ctx.session.set_route(Route.EDIT)
                st.rerun()
        with c2:
            if st.button("Voltar", use_container_width=True):
                ctx.session.set_route(Route.CONSULTA)
                st.rerun()
    else:
        if st.button("Voltar", use_container_width=True):
            ctx.session.set_route(Route.CONSULTA)
            st.rerun()


def show(ctx):
    return render(ctx)
