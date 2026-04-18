from __future__ import annotations

import json
from typing import Any, Dict, List

import streamlit as st
try:
    from postgrest.exceptions import APIError
except Exception:
    class APIError(Exception):
        pass

from core.access_control import require_admin_access
from core.calculadora import mensagem_bobinagem_auxiliar_incompleta
from core.navigation import Route
from services.oficina_parser import (
    DEFAULT_EXTRACTED,
    build_normalized_from_motor_row,
    normalize_extracted_data,
    to_motores_schema_payload,
    to_supabase_payload,
)
from services.oficina_runtime import enriquecer_motor_oficina
from services.supabase_data import clear_motores_cache, fetch_motor_by_id_cached
from utils.motor_hologram import HOLOGRAM_CHOICES
from utils.motor_normalizer import normalize_motor_row_for_ui
from utils.motor_view import dados_tecnicos_from_row


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _to_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str) and value.strip().startswith("{"):
        try:
            return json.loads(value)
        except Exception:
            return {}
    return {}


def _nonempty_list(val: Any) -> bool:
    if not isinstance(val, list):
        return False
    return any(_to_text(x) for x in val)


def _split_csv_tokens(s: str) -> List[str]:
    out: List[str] = []
    for part in s.replace(";", ",").split(","):
        t = part.strip()
        if t:
            out.append(t)
    return out


def _merge_ui_fields_into_normalized_data(data: Dict[str, Any], motor: Dict[str, Any]) -> None:
    """Preenche lacunas do JSON com colunas da view / VariaveisSite (mesma regra da consulta/detalhe)."""
    ui = normalize_motor_row_for_ui(motor)
    info = data.setdefault("motor", {})
    bp = data.setdefault("bobinagem_principal", {})
    ba = data.setdefault("bobinagem_auxiliar", {})
    mec = data.setdefault("mecanica", {})

    if not _nonempty_list(bp.get("passos")) and ui.get("passo_principal"):
        bp["passos"] = _split_csv_tokens(ui["passo_principal"])
    if not _nonempty_list(bp.get("espiras")) and ui.get("espiras_principal"):
        bp["espiras"] = _split_csv_tokens(ui["espiras_principal"])
    if not _nonempty_list(bp.get("fios")) and ui.get("fio_principal"):
        bp["fios"] = _split_csv_tokens(ui["fio_principal"])
    if not _to_text(bp.get("ligacao")) and ui.get("ligacao_principal"):
        bp["ligacao"] = ui["ligacao_principal"]

    if not _nonempty_list(ba.get("passos")) and ui.get("passo_auxiliar"):
        ba["passos"] = _split_csv_tokens(ui["passo_auxiliar"])
    if not _nonempty_list(ba.get("espiras")) and ui.get("espiras_auxiliar"):
        ba["espiras"] = _split_csv_tokens(ui["espiras_auxiliar"])
    if not _nonempty_list(ba.get("fios")) and ui.get("fio_auxiliar"):
        ba["fios"] = _split_csv_tokens(ui["fio_auxiliar"])
    if not _to_text(ba.get("ligacao")) and ui.get("ligacao_auxiliar"):
        ba["ligacao"] = ui["ligacao_auxiliar"]

    if not _to_text(mec.get("eixo")) and ui.get("eixo"):
        mec["eixo"] = ui["eixo"]
    if not _to_text(mec.get("carcaca")) and ui.get("carcaca"):
        mec["carcaca"] = ui["carcaca"]
    if not _nonempty_list(mec.get("medidas")) and ui.get("medidas"):
        mec["medidas"] = [ui["medidas"]]

    if not _to_text(info.get("frequencia")) and ui.get("frequencia"):
        info["frequencia"] = ui["frequencia"]
    if not _to_text(info.get("tipo_motor")) and ui.get("tipo_motor"):
        info["tipo_motor"] = ui["tipo_motor"]
    if not _to_text(info.get("polos")) and ui.get("polos"):
        info["polos"] = ui["polos"]


def _to_list(value: Any, split_slash: bool = False) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [_to_text(v) for v in value if _to_text(v)]
    txt = _to_text(value)
    if not txt:
        return []
    raw = txt.replace(";", ",")
    if split_slash:
        raw = raw.replace("/", ",")
    return [p.strip() for p in raw.split(",") if p.strip()]


def _list_editor(label: str, values: List[str], key: str, help_text: str = "") -> List[str]:
    raw = st.text_area(
        label,
        value="\n".join(values),
        key=key,
        help=help_text or "Uma linha por item. TambÃ©m aceita valores separados por vÃ­rgula.",
        height=80,
    )
    out: List[str] = []
    for line in raw.splitlines():
        for part in line.replace(";", ",").split(","):
            value = part.strip()
            if value:
                out.append(value)
    return out


def _build_initial_data(motor: Dict[str, Any]) -> Dict[str, Any]:
    source = dados_tecnicos_from_row(motor)
    if not source:
        source = _to_dict(motor.get("dados_tecnicos_json") or motor.get("leitura_gemini_json"))
    if not source:
        source = build_normalized_from_motor_row(motor)
    source = source or DEFAULT_EXTRACTED
    data = normalize_extracted_data(source)

    info = data.get("motor", {})

    if not info.get("marca"):
        info["marca"] = _to_text(motor.get("marca") or motor.get("Marca"))
    if not info.get("modelo"):
        info["modelo"] = _to_text(
            motor.get("modelo")
            or motor.get("Modelo")
            or motor.get("modelo_iec")
            or motor.get("modelo_nema")
        )
    if not info.get("potencia"):
        info["potencia"] = _to_text(motor.get("potencia") or motor.get("Potencia") or motor.get("potencia_cv"))
    if not info.get("rpm"):
        info["rpm"] = _to_text(motor.get("rpm") or motor.get("Rpm") or motor.get("rpm_nominal"))
    if not info.get("polos"):
        info["polos"] = _to_text(motor.get("polos") or motor.get("Polos"))
    if not info.get("tipo_motor"):
        info["tipo_motor"] = _to_text(motor.get("tipo_motor") or motor.get("TipoMotor"))
    if not info.get("fases"):
        info["fases"] = _to_text(motor.get("fases") or motor.get("Fases"))
    if not info.get("tensao"):
        info["tensao"] = _to_list(
            motor.get("tensao") or motor.get("Tensao") or motor.get("tensao_v"),
            split_slash=True,
        )
    if not info.get("corrente"):
        info["corrente"] = _to_list(
            motor.get("corrente") or motor.get("Corrente") or motor.get("corrente_a"),
            split_slash=True,
        )

    if not data.get("observacoes_gerais"):
        data["observacoes_gerais"] = _to_text(motor.get("observacoes") or motor.get("Observacoes"))
    if not data.get("texto_ocr"):
        data["texto_ocr"] = _to_text(motor.get("texto_bruto_extraido") or motor.get("TextoBrutoExtraido"))

    _merge_ui_fields_into_normalized_data(data, motor)

    return data


def _update_motor_supabase(supabase, id_motor, payload_legacy: dict, payload_schema: dict) -> None:
    try:
        supabase.table("motores").update(payload_legacy).eq("id", id_motor).execute()
        return
    except APIError:
        pass
    except Exception:
        pass

    try:
        supabase.table("motores").update(payload_schema).eq("id", id_motor).execute()
        return
    except Exception:
        pass

    try:
        fallback = {
            "marca": payload_legacy.get("marca", ""),
            "modelo": payload_legacy.get("modelo", ""),
            "potencia": payload_legacy.get("potencia", ""),
            "rpm": payload_legacy.get("rpm", ""),
            "tensao": payload_legacy.get("tensao", ""),
            "corrente": payload_legacy.get("corrente", ""),
            "observacoes": payload_legacy.get("observacoes", ""),
        }
        supabase.table("motores").update(fallback).eq("id", id_motor).execute()
        return
    except Exception as exc:
        raise RuntimeError(f"Nao foi possivel atualizar o motor em nenhum schema compativel: {exc}") from exc


def render(ctx):
    if not require_admin_access("Edicao de motor", client=ctx.supabase):
        if st.button("Voltar para Consulta", use_container_width=True):
            ctx.session.set_route(Route.CONSULTA)
            st.rerun()
        return

    st.title("âœï¸ Editar Motor")

    id_motor = ctx.session.selected_motor_id
    if id_motor is None:
        st.warning("Nenhum motor selecionado para ediÃ§Ã£o.")
        if st.button("ðŸ”™ Voltar para Consulta", use_container_width=True):
            ctx.session.set_route(Route.CONSULTA)
            st.rerun()
        return

    motor = fetch_motor_by_id_cached(ctx.supabase, id_motor)
    if motor is None:
        st.error("Motor nÃ£o encontrado.")
        if st.button("ðŸ”™ Voltar para Consulta", use_container_width=True):
            ctx.session.set_route(Route.CONSULTA)
            st.rerun()
        return

    seq_sess = st.session_state.get(f"motor_cadastro_seq_{id_motor}")
    if seq_sess is not None:
        try:
            st.caption(f"Cadastro #{int(seq_sess)} · ID interno (Supabase): {id_motor}")
        except (TypeError, ValueError):
            st.caption(f"ID interno (Supabase): {id_motor}")

    state_key = f"edit_motor_data_{id_motor}"
    loaded_key = "edit_loaded_motor_id"
    if st.session_state.get(loaded_key) != id_motor or state_key not in st.session_state:
        st.session_state[state_key] = _build_initial_data(motor)
        st.session_state[loaded_key] = id_motor

    data = st.session_state[state_key]
    k = f"edit_{id_motor}_"

    with st.form("edit_motor_form_full"):
        st.markdown("### A. IdentificaÃ§Ã£o do motor")
        c1, c2, c3 = st.columns(3)
        with c1:
            data["motor"]["marca"] = st.text_input("Marca", value=data["motor"].get("marca", ""), key=f"{k}marca")
            data["motor"]["modelo"] = st.text_input("Modelo", value=data["motor"].get("modelo", ""), key=f"{k}modelo")
            data["motor"]["potencia"] = st.text_input("PotÃªncia", value=data["motor"].get("potencia", ""), key=f"{k}potencia")
            data["motor"]["cv"] = st.text_input("CV / HP / kW / kVA / kVW", value=data["motor"].get("cv", ""), key=f"{k}cv")
            data["motor"]["rpm"] = st.text_input("RPM", value=data["motor"].get("rpm", ""), key=f"{k}rpm")
        with c2:
            data["motor"]["polos"] = st.text_input("Polos", value=data["motor"].get("polos", ""), key=f"{k}polos")
            data["motor"]["frequencia"] = st.text_input("FrequÃªncia", value=data["motor"].get("frequencia", ""), key=f"{k}frequencia")
            data["motor"]["isolacao"] = st.text_input("IsolaÃ§Ã£o", value=data["motor"].get("isolacao", ""), key=f"{k}isolacao")
            data["motor"]["ip"] = st.text_input("IP", value=data["motor"].get("ip", ""), key=f"{k}ip")
            holo_keys = [x for x, _ in HOLOGRAM_CHOICES]
            holo_labels = {x: y for x, y in HOLOGRAM_CHOICES}
            _h_cur = data["motor"].get("holograma_preset", "auto") or "auto"
            _h_idx = holo_keys.index(_h_cur) if _h_cur in holo_keys else 0
            data["motor"]["holograma_preset"] = st.selectbox(
                "Holograma 3D (consulta)",
                options=holo_keys,
                index=_h_idx,
                format_func=lambda x: holo_labels.get(x, x),
                key=f"{k}holograma_preset",
                help="Automatico: estilo a partir do IP e da carcaca.",
            )
            data["motor"]["holograma_glb_url"] = st.text_input(
                "URL do modelo GLB (opcional)",
                value=data["motor"].get("holograma_glb_url", "") or "",
                key=f"{k}holograma_glb_url",
                help="HTTPS para .glb; com URL, a consulta mostra modelo 3D interactivo.",
            )
            data["motor"]["fator_servico"] = st.text_input("Fator de serviÃ§o", value=data["motor"].get("fator_servico", ""), key=f"{k}fator_servico")
        with c3:
            data["motor"]["tipo_motor"] = st.text_input("Tipo do motor", value=data["motor"].get("tipo_motor", ""), key=f"{k}tipo_motor")
            fases_atual = data["motor"].get("fases", "")
            fases_idx = ["", "MonofÃ¡sico", "TrifÃ¡sico"].index(fases_atual if fases_atual in ["", "MonofÃ¡sico", "TrifÃ¡sico"] else "")
            data["motor"]["fases"] = st.selectbox("Fases", options=["", "MonofÃ¡sico", "TrifÃ¡sico"], index=fases_idx, key=f"{k}fases")
            data["motor"]["numero_serie"] = st.text_input("NÃºmero de sÃ©rie", value=data["motor"].get("numero_serie", ""), key=f"{k}numero_serie")
            data["motor"]["data_anotacao"] = st.text_input("Data da anotaÃ§Ã£o", value=data["motor"].get("data_anotacao", ""), key=f"{k}data_anotacao")

        st.caption("Previa do holograma (como na consulta).")
        try:
            from components.motor_hologram import render_engine_hologram

            _prev = {
                "dados_tecnicos_json": data,
                "rpm": data["motor"].get("rpm"),
                "tensao": data["motor"].get("tensao"),
                "corrente": data["motor"].get("corrente"),
                "fases": data["motor"].get("fases"),
                "tipo_motor": data["motor"].get("tipo_motor"),
            }
            render_engine_hologram(_prev, key=f"{k}holo_preview")
        except Exception:
            pass

        data["motor"]["tensao"] = _list_editor("TensÃ£o (lista)", data["motor"].get("tensao", []), f"{k}motor_tensao_lista")
        data["motor"]["corrente"] = _list_editor("Corrente (lista)", data["motor"].get("corrente", []), f"{k}motor_corrente_lista")
        data["observacoes_gerais"] = st.text_area("ObservaÃ§Ãµes gerais", value=data.get("observacoes_gerais", ""), height=100, key=f"{k}observacoes_gerais")

        st.markdown("### B. Bobinagem principal")
        data["bobinagem_principal"]["passos"] = _list_editor("Passo principal", data["bobinagem_principal"].get("passos", []), f"{k}principal_passos")
        data["bobinagem_principal"]["espiras"] = _list_editor("Espiras principais", data["bobinagem_principal"].get("espiras", []), f"{k}principal_espiras")
        data["bobinagem_principal"]["fios"] = _list_editor("Fio principal", data["bobinagem_principal"].get("fios", []), f"{k}principal_fios")
        pc1, pc2, pc3 = st.columns(3)
        with pc1:
            data["bobinagem_principal"]["quantidade_grupos"] = st.text_input("Qtd. grupos", value=data["bobinagem_principal"].get("quantidade_grupos", ""), key=f"{k}principal_qtd_grupos")
        with pc2:
            data["bobinagem_principal"]["quantidade_bobinas"] = st.text_input("Qtd. bobinas", value=data["bobinagem_principal"].get("quantidade_bobinas", ""), key=f"{k}principal_qtd_bobinas")
        with pc3:
            data["bobinagem_principal"]["ligacao"] = st.text_input("LigaÃ§Ã£o principal", value=data["bobinagem_principal"].get("ligacao", ""), key=f"{k}principal_ligacao")
        data["bobinagem_principal"]["observacoes"] = st.text_area("Obs. principal", value=data["bobinagem_principal"].get("observacoes", ""), height=80, key=f"{k}principal_observacoes")

        st.markdown("### C. Bobinagem auxiliar")
        data["bobinagem_auxiliar"]["passos"] = _list_editor("Passo auxiliar", data["bobinagem_auxiliar"].get("passos", []), f"{k}aux_passos")
        data["bobinagem_auxiliar"]["espiras"] = _list_editor("Espiras auxiliares", data["bobinagem_auxiliar"].get("espiras", []), f"{k}aux_espiras")
        data["bobinagem_auxiliar"]["fios"] = _list_editor("Fio auxiliar", data["bobinagem_auxiliar"].get("fios", []), f"{k}aux_fios")
        ac1, ac2 = st.columns(2)
        with ac1:
            data["bobinagem_auxiliar"]["capacitor"] = st.text_input("Capacitor", value=data["bobinagem_auxiliar"].get("capacitor", ""), key=f"{k}aux_capacitor")
        with ac2:
            data["bobinagem_auxiliar"]["ligacao"] = st.text_input("LigaÃ§Ã£o auxiliar", value=data["bobinagem_auxiliar"].get("ligacao", ""), key=f"{k}aux_ligacao")
        data["bobinagem_auxiliar"]["observacoes"] = st.text_area("Obs. auxiliar", value=data["bobinagem_auxiliar"].get("observacoes", ""), height=80, key=f"{k}aux_observacoes")

        with st.expander("Coerencia de rebobinagem (read-only)", expanded=False):
            from components.motor_rebobinagem_panel import render_rebobinagem_panel

            render_rebobinagem_panel(
                data,
                key_prefix=f"edit_rb_{id_motor}",
                title="Inteligencia de rebobinagem",
                show_download=False,
            )

        st.markdown("### D. MecÃ¢nica")
        data["mecanica"]["rolamentos"] = _list_editor("Rolamentos", data["mecanica"].get("rolamentos", []), f"{k}mec_rolamentos")
        m1, m2, m3 = st.columns(3)
        with m1:
            data["mecanica"]["eixo"] = st.text_input("Eixo", value=data["mecanica"].get("eixo", ""), key=f"{k}mec_eixo")
        with m2:
            data["mecanica"]["carcaca"] = st.text_input("CarcaÃ§a", value=data["mecanica"].get("carcaca", ""), key=f"{k}mec_carcaca")
        with m3:
            data["mecanica"]["comprimento_ponta"] = st.text_input("Comprimento de ponta", value=data["mecanica"].get("comprimento_ponta", ""), key=f"{k}mec_comprimento_ponta")
        data["mecanica"]["medidas"] = _list_editor("Medidas mecÃ¢nicas", data["mecanica"].get("medidas", []), f"{k}mec_medidas")
        data["mecanica"]["observacoes"] = st.text_area("Notas mecÃ¢nicas", value=data["mecanica"].get("observacoes", ""), height=90, key=f"{k}mec_observacoes")

        st.markdown("### E. Desenho / esquema tÃ©cnico")
        data["esquema"]["descricao_desenho"] = st.text_area("DescriÃ§Ã£o do desenho", value=data["esquema"].get("descricao_desenho", ""), height=90, key=f"{k}esquema_descricao")
        e1, e2 = st.columns(2)
        with e1:
            data["esquema"]["distribuicao_bobinas"] = st.text_area("DistribuiÃ§Ã£o das bobinas", value=data["esquema"].get("distribuicao_bobinas", ""), height=90, key=f"{k}esquema_distribuicao")
            data["esquema"]["ligacao"] = st.text_input("LigaÃ§Ã£o", value=data["esquema"].get("ligacao", ""), key=f"{k}esquema_ligacao")
        with e2:
            data["esquema"]["ranhuras"] = st.text_input("Ranhuras", value=data["esquema"].get("ranhuras", ""), key=f"{k}esquema_ranhuras")
            data["esquema"]["camadas"] = st.text_input("Camadas", value=data["esquema"].get("camadas", ""), key=f"{k}esquema_camadas")
            data["esquema"]["observacoes"] = st.text_area("ObservaÃ§Ãµes do esquema", value=data["esquema"].get("observacoes", ""), height=90, key=f"{k}esquema_observacoes")

        st.markdown("### F. Dados brutos da leitura")
        data["texto_ocr"] = st.text_area("Texto bruto extraÃ­do", value=data.get("texto_ocr", ""), height=120, key=f"{k}texto_ocr")
        data["texto_normalizado"] = st.text_area("Texto normalizado", value=data.get("texto_normalizado", ""), height=120, key=f"{k}texto_normalizado")
        st.code(json.dumps(data.get("confianca", {}), ensure_ascii=False, indent=2), language="json")
        st.code(json.dumps(data, ensure_ascii=False, indent=2), language="json")

        with st.expander("Inteligência técnica Moto-Renow (read-only)", expanded=False):
            from components.motor_inteligencia_panel import render_motor_inteligencia_panel

            render_motor_inteligencia_panel(data, key_prefix=f"edit_intel_{id_motor}")

        c1, c2 = st.columns(2)
        with c1:
            salvar = st.form_submit_button("ðŸ’¾ SALVAR ALTERAÃ‡Ã•ES", use_container_width=True)
        with c2:
            voltar = st.form_submit_button("ðŸ”™ VOLTAR", use_container_width=True)

    with st.expander("Baixar JSON rebobinagem (fora do formulario)", expanded=False):
        from components.motor_rebobinagem_panel import render_rebobinagem_json_download_button

        render_rebobinagem_json_download_button(data, key_prefix=f"edit_rb_{id_motor}")

    if voltar:
        ctx.session.set_route(Route.DETALHE)
        st.rerun()

    if salvar:
        msg_bob = mensagem_bobinagem_auxiliar_incompleta(data)
        if msg_bob:
            st.error(msg_bob)
            return
        image_names = _to_list(motor.get("imagens_origem") or motor.get("arquivo_origem") or motor.get("ArquivoOrigem"))
        image_urls = _to_list(motor.get("imagens_urls"))
        data = enriquecer_motor_oficina(data, evento="edicao")
        payload_legacy = to_supabase_payload(data, image_paths=image_urls, image_names=image_names)
        payload_schema = to_motores_schema_payload(data, image_paths=image_urls, image_names=image_names)
        _update_motor_supabase(ctx.supabase, id_motor, payload_legacy, payload_schema)
        clear_motores_cache()
        st.success("AlteraÃ§Ãµes salvas com sucesso.")
        ctx.session.set_route(Route.DETALHE)
        st.rerun()


def show(ctx):
    return render(ctx)



