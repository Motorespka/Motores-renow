from __future__ import annotations

import io
import json
import os
import re
import time
from typing import Any, Dict, List
import base64

import streamlit as st
from PIL import Image, ImageOps
try:
    from supabase import create_client
except Exception:
    create_client = None
try:
    from postgrest.exceptions import APIError
except Exception:
    class APIError(Exception):
        pass

from core.access_control import require_cadastro_access
from core.calculadora import mensagem_bobinagem_auxiliar_incompleta
from core.navigation import Route
from core.user_identity import resolve_current_user_identity
from services.gemini_oficina import HEIF_SUPPORTED, extract_motor_data_with_gemini
from services.oficina_parser import (
    DEFAULT_EXTRACTED,
    normalize_extracted_data,
    to_motores_schema_payload,
    to_supabase_payload,
)
from services.oficina_runtime import enriquecer_motor_oficina
from services.supabase_data import clear_motores_cache
from utils.motor_hologram import HOLOGRAM_CHOICES

SUPPORTED_TYPES = ["jpg", "jpeg", "png", "heic", "heif", "webp", "jfif", "avif"]


class DuplicateMotorError(RuntimeError):
    def __init__(self, message: str, duplicate_id: str = "") -> None:
        super().__init__(message)
        self.duplicate_id = duplicate_id


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


def _decode_jwt_payload(token: str) -> Dict[str, Any]:
    raw = str(token or "").strip()
    parts = raw.split(".")
    if len(parts) != 3:
        return {}
    payload_b64 = parts[1]
    padding = "=" * (-len(payload_b64) % 4)
    try:
        decoded = base64.urlsafe_b64decode((payload_b64 + padding).encode("utf-8")).decode("utf-8")
        data = json.loads(decoded)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _looks_like_service_role_key(token: str) -> bool:
    raw = str(token or "").strip()
    if not raw:
        return False

    # Chaves novas do Supabase
    if raw.startswith("sb_secret_"):
        return True
    if raw.startswith("sb_publishable_"):
        return False

    payload = _decode_jwt_payload(raw)
    role = str(payload.get("role") or "").strip().lower()
    if role in {"service_role", "supabase_admin"}:
        return True
    if role in {"anon", "authenticated"}:
        return False

    return False


def _resolve_service_role_key() -> str:
    explicit_names = [
        "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_SERVICE_KEY",
        "SUPABASE_SECRET_KEY",
        "SERVICE_ROLE_KEY",
    ]
    for name in explicit_names:
        value = _read_secret_or_env(name)
        if value:
            return value

    shared_key = _read_secret_or_env("SUPABASE_KEY")
    if shared_key and _looks_like_service_role_key(shared_key):
        return shared_key

    return ""


def _init_state() -> None:
    st.session_state.setdefault("cadastro_extracted", normalize_extracted_data(DEFAULT_EXTRACTED))
    st.session_state.setdefault("cadastro_uploads", [])
    st.session_state.setdefault("cadastro_status", "Aguardando imagens")


def _list_editor(label: str, values: List[str], key: str, help_text: str = "") -> List[str]:
    raw = st.text_area(
        label,
        value="\n".join(values),
        key=key,
        help=help_text or "Uma linha por item. Tambem aceita valores separados por virgula.",
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
        st.warning("Campos com baixa confianca: " + " | ".join(low[:8]))


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
        raw_name = (file.name or "").replace("\\", "/").split("/")[-1]
        safe_name = "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in raw_name)
        safe_name = safe_name.strip("._") or "imagem_upload.bin"
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


def _norm_text(value: Any) -> str:
    txt = str(value or "").strip().lower()
    txt = re.sub(r"\s+", " ", txt)
    return txt


def _norm_digits(value: Any) -> str:
    txt = str(value or "")
    return "".join(ch for ch in txt if ch.isdigit())


def _norm_slash_list(values: Any) -> str:
    if isinstance(values, list):
        raw = [str(v or "").strip() for v in values]
    else:
        raw = [str(values or "").strip()]
    out: List[str] = []
    for item in raw:
        if not item:
            continue
        for token in re.split(r"[;,/|]+", item):
            cleaned = token.strip().lower()
            if cleaned:
                out.append(cleaned)
    if not out:
        return ""
    return "/".join(out)


def _extract_duplicate_values_from_normalized(normalized: Dict[str, Any]) -> Dict[str, str]:
    motor = normalized.get("motor") if isinstance(normalized.get("motor"), dict) else {}
    return {
        "marca": _norm_text(motor.get("marca")),
        "modelo": _norm_text(motor.get("modelo")),
        "potencia": _norm_text(motor.get("potencia") or motor.get("cv")),
        "rpm": _norm_digits(motor.get("rpm")),
        "tensao": _norm_slash_list(motor.get("tensao")),
        "corrente": _norm_slash_list(motor.get("corrente")),
    }


def _extract_duplicate_values_from_row(row: Dict[str, Any]) -> Dict[str, str]:
    return {
        "marca": _norm_text(row.get("marca") or row.get("Marca")),
        "modelo": _norm_text(row.get("modelo") or row.get("Modelo")),
        "potencia": _norm_text(row.get("potencia") or row.get("Potencia")),
        "rpm": _norm_digits(row.get("rpm") or row.get("Rpm")),
        "tensao": _norm_slash_list(row.get("tensao") or row.get("Tensao")),
        "corrente": _norm_slash_list(row.get("corrente") or row.get("Corrente")),
    }


def _build_duplicate_key(values: Dict[str, str]) -> str:
    marca = values.get("marca", "")
    modelo = values.get("modelo", "")
    potencia = values.get("potencia", "")
    rpm = values.get("rpm", "")
    tensao = values.get("tensao", "")
    corrente = values.get("corrente", "")
    if not marca or not modelo:
        return ""
    if not potencia and not rpm:
        return ""
    return "|".join([marca, modelo, potencia, rpm, tensao, corrente])


def _find_duplicate_motor(ctx, normalized: Dict[str, Any]) -> Dict[str, Any] | None:
    target_values = _extract_duplicate_values_from_normalized(normalized)
    target_key = _build_duplicate_key(target_values)
    if not target_key:
        return None

    is_local_runtime = bool(getattr(ctx.supabase, "is_local_runtime", False))
    rows: List[Dict[str, Any]] = []
    try:
        query = (
            ctx.supabase
            .table("motores")
            .select("id,marca,modelo,potencia,rpm,tensao,corrente,created_at,updated_at")
        )
        marca = target_values.get("marca", "")
        modelo = target_values.get("modelo", "")
        if not is_local_runtime:
            if marca:
                query = query.ilike("marca", marca)
            if modelo:
                query = query.ilike("modelo", modelo)
        res = query.limit(120).execute()
        data = getattr(res, "data", None) or []
        if isinstance(data, list):
            rows = data
    except Exception:
        rows = []

    for row in rows:
        if not isinstance(row, dict):
            continue
        row_key = _build_duplicate_key(_extract_duplicate_values_from_row(row))
        if row_key and row_key == target_key:
            return row
    return None


def _is_rls_error(exc: Exception | None) -> bool:
    text = str(exc or "").lower()
    return (
        "row-level security policy" in text
        or "new row violates row-level security policy" in text
        or "'code': '42501'" in text
        or '"code":"42501"' in text
    )


def _build_service_role_client():
    if create_client is None:
        return None

    supabase_url = _read_secret_or_env("SUPABASE_URL")
    service_key = _resolve_service_role_key()
    if not supabase_url or not service_key:
        return None

    cache_key = f"{supabase_url}|{service_key[:16]}"
    cached_key = str(st.session_state.get("_service_role_client_key") or "")
    cached_client = st.session_state.get("_service_role_client")
    if cached_client is not None and cached_key == cache_key:
        return cached_client

    try:
        client = create_client(supabase_url, service_key)
    except Exception:
        return None

    st.session_state["_service_role_client_key"] = cache_key
    st.session_state["_service_role_client"] = client
    return client


def _with_rls_owner_hints(payload: Dict[str, Any], identity: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(payload or {})
    user_id = str(identity.get("user_id") or "").strip()
    email = str(identity.get("email") or "").strip().lower()
    username = str(identity.get("username") or "").strip().lower()

    if user_id:
        for key in [
            "user_id",
            "owner_id",
            "created_by",
            "created_by_id",
            "auth_user_id",
            "usuario_id",
            "cadastrado_por_id",
        ]:
            if key not in out or not str(out.get(key) or "").strip():
                out[key] = user_id

    if email:
        for key in ["user_email", "created_by_email", "cadastrado_por_email"]:
            if key not in out or not str(out.get(key) or "").strip():
                out[key] = email

    if username:
        for key in ["username", "created_by_username", "cadastrado_por_username"]:
            if key not in out or not str(out.get(key) or "").strip():
                out[key] = username

    return out


def _extract_missing_column(exc: Exception) -> str:
    text = str(exc or "")
    patterns = [
        r"Could not find the '([^']+)' column",
        r'column "([^"]+)" of relation',
        r"column ([a-zA-Z_][a-zA-Z0-9_]*) does not exist",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return (match.group(1) or "").strip()
    return ""


def _insert_resilient(
    ctx,
    payload: Dict[str, Any],
    write_client=None,
) -> tuple[bool, Exception | None, List[str]]:
    client = write_client or ctx.supabase
    candidate = dict(payload or {})
    removed_columns: List[str] = []
    last_error: Exception | None = None

    for _ in range(15):
        if not candidate:
            break
        try:
            client.table("motores").insert(candidate).execute()
            return True, None, removed_columns
        except Exception as exc:
            last_error = exc
            missing_column = _extract_missing_column(exc)
            if not missing_column or missing_column not in candidate:
                break
            candidate.pop(missing_column, None)
            removed_columns.append(missing_column)

    return False, last_error, removed_columns


def _save_motor(ctx, normalized: Dict[str, Any], uploads: List[Any]) -> None:
    normalized = enriquecer_motor_oficina(normalized, evento="cadastro")
    normalized = _with_creator_metadata(normalized)
    duplicated = _find_duplicate_motor(ctx, normalized)
    if isinstance(duplicated, dict):
        duplicate_id = str(duplicated.get("id") or "").strip()
        duplicate_ref = f"ID {duplicate_id}" if duplicate_id else "registro existente"
        raise DuplicateMotorError(
            f"Cadastro bloqueado: motor duplicado detectado ({duplicate_ref}).",
            duplicate_id=duplicate_id,
        )

    identity = resolve_current_user_identity()
    creator = identity.get("display_name", "Usuario")
    image_names = [f.name for f in uploads]
    image_urls = _upload_images_to_supabase(ctx, uploads)
    legacy_payload = to_supabase_payload(normalized, image_paths=image_urls, image_names=image_names)
    schema_payload = to_motores_schema_payload(normalized, image_paths=image_urls, image_names=image_names)
    legacy_payload = _with_rls_owner_hints(legacy_payload, identity)
    schema_payload = _with_rls_owner_hints(schema_payload, identity)

    saved = False
    last_error = None

    saved, last_error, removed_cols = _insert_resilient(ctx, legacy_payload)
    if saved and removed_cols:
        st.info(
            "Cadastro salvo com ajuste automatico de schema. "
            f"Colunas removidas: {', '.join(removed_cols)}."
        )

    if not saved:
        saved, schema_error, removed_cols = _insert_resilient(ctx, schema_payload)
        if saved:
            st.info("Salvo no schema tecnico compativel (motores/vw_motores_para_site).")
            if removed_cols:
                st.info(
                    "Cadastro salvo com ajuste automatico de schema. "
                    f"Colunas removidas: {', '.join(removed_cols)}."
                )
        else:
            last_error = schema_error or last_error

    if not saved:
        fallback_obs = f"{legacy_payload.get('observacoes', '')} | Feito por: {creator}".strip(" |")
        modelo_txt = str(legacy_payload.get("modelo") or "").strip()
        if modelo_txt:
            fallback_obs = f"Modelo informado: {modelo_txt} | {fallback_obs}".strip(" |")

        fallback = {
            "marca": legacy_payload.get("marca", ""),
            "potencia": legacy_payload.get("potencia", ""),
            "rpm": legacy_payload.get("rpm", ""),
            "tensao": legacy_payload.get("tensao", ""),
            "corrente": legacy_payload.get("corrente", ""),
            "observacoes": fallback_obs,
        }
        fallback = _with_rls_owner_hints(fallback, identity)
        saved, fallback_error, removed_cols = _insert_resilient(ctx, fallback)
        if saved:
            st.info("Salvo com colunas basicas. Campos JSON podem depender de migracao no Supabase.")
            if removed_cols:
                st.info(
                    "Cadastro salvo com ajuste automatico de schema. "
                    f"Colunas removidas: {', '.join(removed_cols)}."
                )
        else:
            last_error = fallback_error or last_error

    if not saved and _is_rls_error(last_error):
        service_role_client = _build_service_role_client()
        if service_role_client is None:
            raise PermissionError(
                "Permissao de escrita bloqueada pelo RLS na tabela motores. "
                "Configure SUPABASE_SERVICE_ROLE_KEY (ou SUPABASE_SERVICE_KEY/SERVICE_ROLE_KEY) no Streamlit Cloud "
                "ou ajuste policy INSERT para usuarios autenticados."
            )

        saved, service_error, removed_cols = _insert_resilient(ctx, legacy_payload, write_client=service_role_client)
        if saved:
            st.info("Salvo com credencial administrativa (fallback de RLS).")
            if removed_cols:
                st.info(
                    "Cadastro salvo com ajuste automatico de schema. "
                    f"Colunas removidas: {', '.join(removed_cols)}."
                )
        else:
            last_error = service_error or last_error

        if not saved:
            saved, service_error, removed_cols = _insert_resilient(
                ctx,
                schema_payload,
                write_client=service_role_client,
            )
            if saved:
                st.info("Salvo no schema tecnico compativel (fallback de RLS).")
                if removed_cols:
                    st.info(
                        "Cadastro salvo com ajuste automatico de schema. "
                        f"Colunas removidas: {', '.join(removed_cols)}."
                    )
            else:
                last_error = service_error or last_error

        if not saved:
            saved, service_error, removed_cols = _insert_resilient(
                ctx,
                fallback,
                write_client=service_role_client,
            )
            if saved:
                st.info("Salvo com colunas basicas (fallback de RLS).")
                if removed_cols:
                    st.info(
                        "Cadastro salvo com ajuste automatico de schema. "
                        f"Colunas removidas: {', '.join(removed_cols)}."
                    )
            else:
                last_error = service_error or last_error

    if not saved:
        raise RuntimeError(f"Nao foi possivel salvar o motor em nenhum schema compativel: {last_error}")

    clear_motores_cache()


def _with_creator_metadata(normalized: Dict[str, Any]) -> Dict[str, Any]:
    identity = resolve_current_user_identity()

    try:
        enriched = json.loads(json.dumps(normalized or {}))
    except Exception:
        enriched = dict(normalized or {})

    meta = enriched.get("meta")
    if not isinstance(meta, dict):
        meta = {}

    meta.update(
        {
            "cadastrado_por_id": identity.get("user_id", ""),
            "cadastrado_por_email": identity.get("email", ""),
            "cadastrado_por_username": identity.get("username", ""),
            "cadastrado_por_nome": identity.get("nome", ""),
            "cadastrado_por_display": identity.get("display_name", ""),
            "cadastrado_em": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
        }
    )
    enriched["meta"] = meta

    oficina = enriched.get("oficina")
    if not isinstance(oficina, dict):
        oficina = {}
    servico = oficina.get("servico_executado")
    if not isinstance(servico, dict):
        servico = {}
    if not str(servico.get("responsavel") or "").strip():
        servico["responsavel"] = identity.get("display_name", "")
    oficina["servico_executado"] = servico
    enriched["oficina"] = oficina

    return enriched


def render(ctx):
    if not require_cadastro_access("Cadastro tecnico (motor, O.S. e IA Gemini)", client=ctx.supabase):
        if st.button("Ir para Consulta", use_container_width=True):
            ctx.session.set_route(Route.CONSULTA)
            st.rerun()
        return

    _init_state()

    st.title("Cadastro Tecnico de Motores")
    st.caption("Fluxo: upload de foto -> leitura Gemini -> revisao manual -> salvar.")

    st.subheader("1) Upload de imagens")
    uploads = st.file_uploader(
        "Selecione uma ou mais fotos de oficina",
        accept_multiple_files=True,
        key="cadastro_motor_fotos",
        help="Fotos de camera/galeria (JPG/PNG/HEIC/HEIF/WEBP/AVIF).",
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
            st.warning("Alguns arquivos nao parecem ser imagem suportada: " + ", ".join(invalid_names))
    current_uploads = st.session_state.get("cadastro_uploads") or []
    has_uploads = len(current_uploads) > 0

    cols = st.columns([2, 1])
    with cols[0]:
        st.info(f"Status: {st.session_state['cadastro_status']}")
    with cols[1]:
        if not HEIF_SUPPORTED:
            st.caption("Para HEIC/HEIF de iPhone, instale pillow-heif no ambiente.")

    if has_uploads:
        prev_cols = st.columns(3)
        for idx, file in enumerate(current_uploads):
            with prev_cols[idx % 3]:
                preview = _preview_image(file)
                if preview is not None:
                    st.image(preview, caption=file.name, use_container_width=True)
                else:
                    # fallback para bytes em navegadores moveis
                    try:
                        st.image(file.getvalue(), caption=file.name, use_container_width=True)
                    except Exception:
                        st.warning(f"Nao foi possivel gerar preview de {file.name}")
                st.caption(f"tipo={file.type or 'desconhecido'} | tamanho={len(file.getvalue())} bytes")

    if st.button("Ler foto com Gemini", use_container_width=True):
        if not has_uploads:
            st.warning("Envie ao menos uma foto para analise antes de usar o Gemini.")
        else:
            files_payload = [
                {"name": f.name, "bytes": f.getvalue(), "mime_type": f.type}
                for f in current_uploads
            ]
            st.session_state["cadastro_status"] = "Analisando imagens no Gemini..."
            try:
                with st.spinner("Extraindo campos tecnicos..."):
                    extracted = extract_motor_data_with_gemini(files_payload)
                st.session_state["cadastro_extracted"] = normalize_extracted_data(extracted)
                st.session_state["cadastro_status"] = "Campos extraidos e prontos para revisao"
                st.success("Leitura finalizada. Revise os campos antes de salvar.")
            except Exception as exc:
                st.session_state["cadastro_status"] = "Falha na leitura com Gemini"
                st.error(f"Falha ao ler foto com Gemini: {exc}")

    if st.button("Limpar formulario", use_container_width=True):
        st.session_state["cadastro_extracted"] = normalize_extracted_data(DEFAULT_EXTRACTED)
        st.session_state["cadastro_uploads"] = []
        st.session_state["cadastro_status"] = "Aguardando imagens"
        st.rerun()

    data = st.session_state["cadastro_extracted"]
    _show_confidence_warnings(data.get("confianca") or {})

    st.subheader("2) Revisao e cadastro")

    with st.form("cadastro_motor_oficina_form"):
        st.markdown("### A. Identificacao do motor")
        c1, c2, c3 = st.columns(3)
        with c1:
            data["motor"]["marca"] = st.text_input("Marca", value=data["motor"].get("marca", ""))
            data["motor"]["modelo"] = st.text_input("Modelo", value=data["motor"].get("modelo", ""))
            data["motor"]["potencia"] = st.text_input("Potencia", value=data["motor"].get("potencia", ""))
            data["motor"]["cv"] = st.text_input("CV / HP / kW / kVA / kVW", value=data["motor"].get("cv", ""))
            data["motor"]["rpm"] = st.text_input("RPM", value=data["motor"].get("rpm", ""))
        with c2:
            data["motor"]["polos"] = st.text_input("Polos", value=data["motor"].get("polos", ""))
            data["motor"]["frequencia"] = st.text_input("Frequencia", value=data["motor"].get("frequencia", ""))
            data["motor"]["isolacao"] = st.text_input("Isolacao", value=data["motor"].get("isolacao", ""))
            data["motor"]["ip"] = st.text_input("IP", value=data["motor"].get("ip", ""))
            holo_keys = [k for k, _ in HOLOGRAM_CHOICES]
            holo_labels = {k: v for k, v in HOLOGRAM_CHOICES}
            _h_cur = data["motor"].get("holograma_preset", "auto") or "auto"
            _h_idx = holo_keys.index(_h_cur) if _h_cur in holo_keys else 0
            data["motor"]["holograma_preset"] = st.selectbox(
                "Holograma 3D (consulta)",
                options=holo_keys,
                index=_h_idx,
                format_func=lambda k: holo_labels.get(k, k),
                help="Automatico: estilo a partir do IP e da carcaca. Ou escolha um preset fixo.",
            )
            data["motor"]["holograma_glb_url"] = st.text_input(
                "URL do modelo GLB (opcional)",
                value=data["motor"].get("holograma_glb_url", "") or "",
                help="HTTPS para ficheiro .glb (ex.: Supabase Storage). Com URL, a consulta usa <model-viewer> em vez da silhueta CSS.",
            )
            data["motor"]["fator_servico"] = st.text_input("Fator de servico", value=data["motor"].get("fator_servico", ""))
        with c3:
            data["motor"]["tipo_motor"] = st.text_input("Tipo do motor", value=data["motor"].get("tipo_motor", ""))
            data["motor"]["fases"] = st.selectbox(
                "Fases",
                options=["", "Monofasico", "Trifasico"],
                index=["", "Monofasico", "Trifasico"].index(data["motor"].get("fases", "") if data["motor"].get("fases", "") in ["", "Monofasico", "Trifasico"] else ""),
            )
            data["motor"]["numero_serie"] = st.text_input("Numero de serie", value=data["motor"].get("numero_serie", ""))
            data["motor"]["data_anotacao"] = st.text_input("Data da anotacao", value=data["motor"].get("data_anotacao", ""))

        st.caption(
            "Previa do holograma: com URL GLB valida, use gestos/camera; sem URL, arraste a silhueta CSS. Na consulta, o mesmo aparece no card."
        )
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
            render_engine_hologram(_prev, key="cadastro_holo_preview")
        except Exception:
            pass

        data["motor"]["tensao"] = _list_editor("Tensao (lista)", data["motor"].get("tensao", []), "motor_tensao_lista")
        data["motor"]["corrente"] = _list_editor("Corrente (lista)", data["motor"].get("corrente", []), "motor_corrente_lista")
        data["observacoes_gerais"] = st.text_area("Observacoes gerais", value=data.get("observacoes_gerais", ""), height=100)

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
            data["bobinagem_principal"]["ligacao"] = st.text_input("Ligacao principal", value=data["bobinagem_principal"].get("ligacao", ""))
        data["bobinagem_principal"]["observacoes"] = st.text_area("Obs. principal", value=data["bobinagem_principal"].get("observacoes", ""), height=80)

        st.markdown("### C. Bobinagem auxiliar")
        data["bobinagem_auxiliar"]["passos"] = _list_editor("Passo auxiliar", data["bobinagem_auxiliar"].get("passos", []), "aux_passos")
        data["bobinagem_auxiliar"]["espiras"] = _list_editor("Espiras auxiliares", data["bobinagem_auxiliar"].get("espiras", []), "aux_espiras")
        data["bobinagem_auxiliar"]["fios"] = _list_editor("Fio auxiliar", data["bobinagem_auxiliar"].get("fios", []), "aux_fios")
        ac1, ac2 = st.columns(2)
        with ac1:
            data["bobinagem_auxiliar"]["capacitor"] = st.text_input("Capacitor", value=data["bobinagem_auxiliar"].get("capacitor", ""))
        with ac2:
            data["bobinagem_auxiliar"]["ligacao"] = st.text_input("Ligacao auxiliar", value=data["bobinagem_auxiliar"].get("ligacao", ""))
        data["bobinagem_auxiliar"]["observacoes"] = st.text_area("Obs. auxiliar", value=data["bobinagem_auxiliar"].get("observacoes", ""), height=80)

        with st.expander("Coerencia de rebobinagem (read-only)", expanded=False):
            from components.motor_rebobinagem_panel import render_rebobinagem_panel

            render_rebobinagem_panel(data, key_prefix="cadastro_rb", title="Inteligencia de rebobinagem")

        st.markdown("### D. Mecanica")
        data["mecanica"]["rolamentos"] = _list_editor("Rolamentos", data["mecanica"].get("rolamentos", []), "mec_rolamentos")
        m1, m2, m3 = st.columns(3)
        with m1:
            data["mecanica"]["eixo"] = st.text_input("Eixo", value=data["mecanica"].get("eixo", ""))
        with m2:
            data["mecanica"]["carcaca"] = st.text_input("Carcaca", value=data["mecanica"].get("carcaca", ""))
        with m3:
            data["mecanica"]["comprimento_ponta"] = st.text_input("Comprimento de ponta", value=data["mecanica"].get("comprimento_ponta", ""))
        data["mecanica"]["medidas"] = _list_editor("Medidas mecanicas", data["mecanica"].get("medidas", []), "mec_medidas")
        data["mecanica"]["observacoes"] = st.text_area("Notas mecanicas", value=data["mecanica"].get("observacoes", ""), height=90)

        st.markdown("### E. Esquema tecnico (opcional)")
        st.caption("Preencha apenas se precisar detalhar ligacoes e desenho da bobinagem.")
        data["esquema"]["descricao_desenho"] = st.text_area(
            "Resumo do desenho / ligacao",
            value=data["esquema"].get("descricao_desenho", ""),
            height=90,
        )
        e1, e2 = st.columns(2)
        with e1:
            data["esquema"]["distribuicao_bobinas"] = st.text_area(
                "Distribuicao das bobinas",
                value=data["esquema"].get("distribuicao_bobinas", ""),
                height=90,
            )
            data["esquema"]["ligacao"] = st.text_input(
                "Ligacao do motor (ex.: Delta 380V / Estrela 660V)",
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
                "Observacoes do esquema",
                value=data["esquema"].get("observacoes", ""),
                height=90,
            )

        with st.expander("F. Dados avancados da leitura (opcional)", expanded=False):
            st.caption("Use apenas para conferencia tecnica da leitura da IA.")
            data["texto_ocr"] = st.text_area("Texto bruto extraido", value=data.get("texto_ocr", ""), height=120)
            data["texto_normalizado"] = st.text_area(
                "Texto normalizado",
                value=data.get("texto_normalizado", ""),
                height=120,
            )
            st.json(data.get("confianca", {}), expanded=False)

        with st.expander("Inteligência técnica Moto-Renow (read-only)", expanded=False):
            from components.motor_inteligencia_panel import render_motor_inteligencia_panel

            render_motor_inteligencia_panel(data, key_prefix="cadastro_intel")

        salvar = st.form_submit_button("Salvar", use_container_width=True)

    if salvar:
        if not data["motor"].get("marca") and not data["motor"].get("modelo"):
            st.warning("Informe ao menos marca ou modelo antes de salvar.")
            return

        msg_bob = mensagem_bobinagem_auxiliar_incompleta(data)
        if msg_bob:
            st.error(msg_bob)
            return

        try:
            _save_motor(ctx, data, uploads=current_uploads)
            st.success("Cadastro tecnico salvo com sucesso.")
        except DuplicateMotorError as exc:
            st.warning(str(exc))
        except Exception as exc:
            st.error(f"Falha ao salvar cadastro tecnico: {exc}")

def show(ctx):
    return render(ctx)

