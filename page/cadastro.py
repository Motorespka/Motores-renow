from __future__ import annotations

import io
import os
import time
from typing import Any, Dict, List

import streamlit as st
from PIL import Image, ImageOps
from postgrest.exceptions import APIError

from services.gemini_oficina import HEIF_SUPPORTED, extract_motor_data_with_gemini
from services.oficina_parser import DEFAULT_EXTRACTED, normalize_extracted_data, to_supabase_payload
from services.supabase_data import clear_motores_cache

SUPPORTED_TYPES = ["jpg", "jpeg", "png", "heic", "heif", "webp", "jfif", "avif"]


def _init_state() -> None:
    st.session_state.setdefault("cadastro_extracted", normalize_extracted_data(DEFAULT_EXTRACTED))
    st.session_state.setdefault("cadastro_uploads", [])
    st.session_state.setdefault("cadastro_status", "Aguardando imagens")


def _list_editor(label: str, values: List[str], key: str, help_text: str = "") -> List[str]:
    raw = st.text_area(
        label,
        value="\n".join(values),
        key=key,
        help=help_text or "Uma linha por item. Também aceita valores separados por vírgula.",
        height=80,
    )
    out = []
    for line in raw.splitlines():
        for part in line.replace(";", ",").split(","):
            value = part.strip()
            if value:
                out.append(value)
    return out


def _show_confidence_warnings(conf: Dict[str, Any]) -> None:
    if not conf:
        return
    low = [f"{k}: {v}" for k, v in conf.items() if isinstance(v, (float, int)) and float(v) < 0.6]
    if low:
        st.warning("Campos com baixa confiança: " + " | ".join(low[:8]))


def _preview_image(uploaded_file):
    raw = uploaded_file.getvalue()
    try:
        img = Image.open(io.BytesIO(raw))
        img = ImageOps.exif_transpose(img)
        return img.copy()
    except Exception:
        return None


def _is_supported_image_upload(uploaded_file) -> bool:
    name = (uploaded_file.name or "").lower()
    mime = (uploaded_file.type or "").lower()

    if mime.startswith("image/"):
        return True

    if any(name.endswith(f".{ext}") for ext in SUPPORTED_TYPES):
        return True

    raw = uploaded_file.getvalue()
    if raw[:3] == b"\xff\xd8\xff":  # JPEG
        return True
    if raw[:8] == b"\x89PNG\r\n\x1a\n":  # PNG
        return True
    if len(raw) >= 12 and raw[4:8] == b"ftyp":  # HEIF/HEIC/AVIF family
        return True

    return False


def _upload_images_to_supabase(ctx, uploads: List[Any]) -> List[str]:
    bucket = (os.environ.get("SUPABASE_MOTORES_BUCKET") or "motores-imagens").strip()
    urls: List[str] = []
    if not uploads:
        return urls

    for file in uploads:
        safe_name = file.name.replace(" ", "_")
        path = f"cadastro/{int(time.time())}_{safe_name}"
        try:
            ctx.supabase.storage.from_(bucket).upload(
                path=path,
                file=file.getvalue(),
                file_options={"content-type": file.type or "application/octet-stream", "upsert": "true"},
            )
            public_url = ctx.supabase.storage.from_(bucket).get_public_url(path)
            if isinstance(public_url, str) and public_url:
                urls.append(public_url)
        except Exception:
            continue
    return urls


def _save_motor(ctx, normalized: Dict[str, Any], uploads: List[Any]) -> None:
    image_names = [f.name for f in uploads]
    image_urls = _upload_images_to_supabase(ctx, uploads)
    payload = to_supabase_payload(normalized, image_paths=image_urls, image_names=image_names)

    try:
        ctx.supabase.table("motores").insert(payload).execute()
    except APIError:
        fallback = {
            "marca": payload.get("marca", ""),
            "modelo": payload.get("modelo", ""),
            "potencia": payload.get("potencia", ""),
            "rpm": payload.get("rpm", ""),
            "tensao": payload.get("tensao", ""),
            "corrente": payload.get("corrente", ""),
            "observacoes": payload.get("observacoes", ""),
        }
        ctx.supabase.table("motores").insert(fallback).execute()
        st.info("Salvo com colunas básicas. Campos JSON podem depender de migração no Supabase.")

    clear_motores_cache()


def render(ctx):
    _init_state()

    st.title("⚡ Cadastro Técnico de Motores")
    st.caption("Fluxo: upload de foto → leitura Gemini → revisão manual → salvar.")

    st.subheader("1) Upload de imagens")
    uploads = st.file_uploader(
        "Selecione uma ou mais fotos de oficina",
        accept_multiple_files=True,
        key="cadastro_motor_fotos",
        help="Fotos de câmera/galeria (JPG/PNG/HEIC/HEIF/WEBP/AVIF).",
    )

    if uploads:
        valid_uploads: List[Any] = []
        invalid_names: List[str] = []
        for file in uploads:
            if _is_supported_image_upload(file):
                valid_uploads.append(file)
            else:
                invalid_names.append(file.name or "arquivo sem nome")

        st.session_state["cadastro_uploads"] = valid_uploads
        st.session_state["cadastro_status"] = f"{len(valid_uploads)} imagem(ns) carregada(s)"

        if invalid_names:
            st.warning("Alguns arquivos não parecem ser imagem suportada: " + ", ".join(invalid_names))
    current_uploads = st.session_state.get("cadastro_uploads") or []
    has_uploads = len(current_uploads) > 0

    cols = st.columns([2, 1])
    with cols[0]:
        st.info(f"Status: {st.session_state['cadastro_status']}")
    with cols[1]:
        if not HEIF_SUPPORTED:
            st.caption("ℹ️ Para HEIC/HEIF de iPhone, instale pillow-heif no ambiente.")

    if has_uploads:
        prev_cols = st.columns(3)
        for idx, file in enumerate(current_uploads):
            with prev_cols[idx % 3]:
                preview = _preview_image(file)
                if preview is not None:
                    st.image(preview, caption=file.name, use_container_width=True)
                else:
                    # fallback para bytes em navegadores móveis
                    try:
                        st.image(file.getvalue(), caption=file.name, use_container_width=True)
                    except Exception:
                        st.warning(f"Não foi possível gerar preview de {file.name}")
                st.caption(f"tipo={file.type or 'desconhecido'} | tamanho={len(file.getvalue())} bytes")

    if st.button("Ler foto com Gemini", use_container_width=True):
        if not has_uploads:
            st.warning("Envie ao menos uma foto para análise antes de usar o Gemini.")
        else:
            files_payload = [
                {"name": f.name, "bytes": f.getvalue(), "mime_type": f.type}
                for f in current_uploads
            ]
            st.session_state["cadastro_status"] = "Analisando imagens no Gemini..."
            try:
                with st.spinner("Extraindo campos técnicos..."):
                    extracted = extract_motor_data_with_gemini(files_payload)
                st.session_state["cadastro_extracted"] = normalize_extracted_data(extracted)
                st.session_state["cadastro_status"] = "Campos extraídos e prontos para revisão"
                st.success("Leitura finalizada. Revise os campos antes de salvar.")
            except Exception as exc:
                st.session_state["cadastro_status"] = "Falha na leitura com Gemini"
                st.error(f"Falha ao ler foto com Gemini: {exc}")

    if st.button("Limpar formulário", use_container_width=True):
        st.session_state["cadastro_extracted"] = normalize_extracted_data(DEFAULT_EXTRACTED)
        st.session_state["cadastro_uploads"] = []
        st.session_state["cadastro_status"] = "Aguardando imagens"
        st.rerun()

    data = st.session_state["cadastro_extracted"]
    _show_confidence_warnings(data.get("confianca") or {})

    st.subheader("2) Revisão e cadastro")

    with st.form("cadastro_motor_oficina_form"):
        st.markdown("### A. Identificação do motor")
        c1, c2, c3 = st.columns(3)
        with c1:
            data["motor"]["marca"] = st.text_input("Marca", value=data["motor"].get("marca", ""))
            data["motor"]["modelo"] = st.text_input("Modelo", value=data["motor"].get("modelo", ""))
            data["motor"]["potencia"] = st.text_input("Potência", value=data["motor"].get("potencia", ""))
            data["motor"]["cv"] = st.text_input("CV / HP / kW", value=data["motor"].get("cv", ""))
            data["motor"]["rpm"] = st.text_input("RPM", value=data["motor"].get("rpm", ""))
        with c2:
            data["motor"]["polos"] = st.text_input("Polos", value=data["motor"].get("polos", ""))
            data["motor"]["frequencia"] = st.text_input("Frequência", value=data["motor"].get("frequencia", ""))
            data["motor"]["isolacao"] = st.text_input("Isolação", value=data["motor"].get("isolacao", ""))
            data["motor"]["ip"] = st.text_input("IP", value=data["motor"].get("ip", ""))
            data["motor"]["fator_servico"] = st.text_input("Fator de serviço", value=data["motor"].get("fator_servico", ""))
        with c3:
            data["motor"]["tipo_motor"] = st.text_input("Tipo do motor", value=data["motor"].get("tipo_motor", ""))
            data["motor"]["fases"] = st.selectbox(
                "Fases",
                options=["", "Monofásico", "Trifásico"],
                index=["", "Monofásico", "Trifásico"].index(data["motor"].get("fases", "") if data["motor"].get("fases", "") in ["", "Monofásico", "Trifásico"] else ""),
            )
            data["motor"]["numero_serie"] = st.text_input("Número de série", value=data["motor"].get("numero_serie", ""))
            data["motor"]["data_anotacao"] = st.text_input("Data da anotação", value=data["motor"].get("data_anotacao", ""))

        data["motor"]["tensao"] = _list_editor("Tensão (lista)", data["motor"].get("tensao", []), "motor_tensao_lista")
        data["motor"]["corrente"] = _list_editor("Corrente (lista)", data["motor"].get("corrente", []), "motor_corrente_lista")
        data["observacoes_gerais"] = st.text_area("Observações gerais", value=data.get("observacoes_gerais", ""), height=100)

        st.markdown("### B. Bobinagem principal")
        data["bobinagem_principal"]["passos"] = _list_editor("Passo principal", data["bobinagem_principal"].get("passos", []), "principal_passos")
        data["bobinagem_principal"]["espiras"] = _list_editor("Espiras principais", data["bobinagem_principal"].get("espiras", []), "principal_espiras")
        data["bobinagem_principal"]["fios"] = _list_editor("Fio principal", data["bobinagem_principal"].get("fios", []), "principal_fios")
        pc1, pc2, pc3 = st.columns(3)
        with pc1:
            data["bobinagem_principal"]["quantidade_grupos"] = st.text_input("Qtd. grupos", value=data["bobinagem_principal"].get("quantidade_grupos", ""))
        with pc2:
            data["bobinagem_principal"]["quantidade_bobinas"] = st.text_input("Qtd. bobinas", value=data["bobinagem_principal"].get("quantidade_bobinas", ""))
        with pc3:
            data["bobinagem_principal"]["ligacao"] = st.text_input("Ligação principal", value=data["bobinagem_principal"].get("ligacao", ""))
        data["bobinagem_principal"]["observacoes"] = st.text_area("Obs. principal", value=data["bobinagem_principal"].get("observacoes", ""), height=80)

        st.markdown("### C. Bobinagem auxiliar")
        data["bobinagem_auxiliar"]["passos"] = _list_editor("Passo auxiliar", data["bobinagem_auxiliar"].get("passos", []), "aux_passos")
        data["bobinagem_auxiliar"]["espiras"] = _list_editor("Espiras auxiliares", data["bobinagem_auxiliar"].get("espiras", []), "aux_espiras")
        data["bobinagem_auxiliar"]["fios"] = _list_editor("Fio auxiliar", data["bobinagem_auxiliar"].get("fios", []), "aux_fios")
        ac1, ac2 = st.columns(2)
        with ac1:
            data["bobinagem_auxiliar"]["capacitor"] = st.text_input("Capacitor", value=data["bobinagem_auxiliar"].get("capacitor", ""))
        with ac2:
            data["bobinagem_auxiliar"]["ligacao"] = st.text_input("Ligação auxiliar", value=data["bobinagem_auxiliar"].get("ligacao", ""))
        data["bobinagem_auxiliar"]["observacoes"] = st.text_area("Obs. auxiliar", value=data["bobinagem_auxiliar"].get("observacoes", ""), height=80)

        st.markdown("### D. Mecânica")
        data["mecanica"]["rolamentos"] = _list_editor("Rolamentos", data["mecanica"].get("rolamentos", []), "mec_rolamentos")
        m1, m2, m3 = st.columns(3)
        with m1:
            data["mecanica"]["eixo"] = st.text_input("Eixo", value=data["mecanica"].get("eixo", ""))
        with m2:
            data["mecanica"]["carcaca"] = st.text_input("Carcaça", value=data["mecanica"].get("carcaca", ""))
        with m3:
            data["mecanica"]["comprimento_ponta"] = st.text_input("Comprimento de ponta", value=data["mecanica"].get("comprimento_ponta", ""))
        data["mecanica"]["medidas"] = _list_editor("Medidas mecânicas", data["mecanica"].get("medidas", []), "mec_medidas")
        data["mecanica"]["observacoes"] = st.text_area("Notas mecânicas", value=data["mecanica"].get("observacoes", ""), height=90)

        st.markdown("### E. Esquema técnico (opcional)")
        st.caption("Preencha apenas se precisar detalhar ligações e desenho da bobinagem.")
        data["esquema"]["descricao_desenho"] = st.text_area(
            "Resumo do desenho / ligação",
            value=data["esquema"].get("descricao_desenho", ""),
            height=90,
        )
        e1, e2 = st.columns(2)
        with e1:
            data["esquema"]["distribuicao_bobinas"] = st.text_area(
                "Distribuição das bobinas",
                value=data["esquema"].get("distribuicao_bobinas", ""),
                height=90,
            )
            data["esquema"]["ligacao"] = st.text_input(
                "Ligação do motor (ex.: Delta 380V / Estrela 660V)",
                value=data["esquema"].get("ligacao", ""),
            )
        with e2:
            data["esquema"]["ranhuras"] = st.text_input(
                "Ranhuras (opcional)",
                value=data["esquema"].get("ranhuras", ""),
            )
            data["esquema"]["camadas"] = st.text_input(
                "Camadas (opcional)",
                value=data["esquema"].get("camadas", ""),
            )
            data["esquema"]["observacoes"] = st.text_area(
                "Observações do esquema",
                value=data["esquema"].get("observacoes", ""),
                height=90,
            )

        with st.expander("F. Dados avançados da leitura (opcional)", expanded=False):
            st.caption("Use apenas para conferência técnica da leitura da IA.")
            data["texto_ocr"] = st.text_area("Texto bruto extraído", value=data.get("texto_ocr", ""), height=120)
            data["texto_normalizado"] = st.text_area(
                "Texto normalizado",
                value=data.get("texto_normalizado", ""),
                height=120,
            )
            st.json(data.get("confianca", {}), expanded=False)

        salvar = st.form_submit_button("Salvar", use_container_width=True)

    if salvar:
        if not data["motor"].get("marca") and not data["motor"].get("modelo"):
            st.warning("Informe ao menos marca ou modelo antes de salvar.")
            return

        _save_motor(ctx, data, uploads=current_uploads)
        st.success("Cadastro técnico salvo com sucesso.")

    st.divider()
    st.subheader("Cadastro de O.S. (mantido)")

    with st.form("os_form"):
        cliente = st.text_input("Cliente")
        marca = st.text_input("Marca")
        potencia = st.text_input("Potência")
        rpm = st.text_input("RPM")
        tensao = st.text_input("Tensão")
        corrente = st.text_input("Corrente")
        diagnostico = st.text_area("Diagnóstico de entrada")
        salvar_os = st.form_submit_button("Salvar ordem", use_container_width=True)

    if salvar_os:
        if not cliente or not marca:
            st.warning("Preencha Cliente e Marca.")
            return
        payload = {
            "cliente": cliente,
            "marca": marca,
            "potencia": potencia,
            "rpm": rpm,
            "tensao": tensao,
            "corrente": corrente,
            "diagnostico": diagnostico,
            "status": "Em Análise",
        }
        ctx.supabase.table("ordens_servico").insert(payload).execute()
        st.success("Ordem salva com sucesso.")


def show(ctx):
    return render(ctx)
