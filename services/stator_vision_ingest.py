#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ingestão híbrida: fotos do estator vazio (.heic, .jpg, …) + escala visual → Gemini multimodal.
"""

from __future__ import annotations

import base64
import mimetypes
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO, Optional, Union

from services.image_normalize import HEIF_SUPPORTED, normalize_image_for_api

ImageSource = Union[bytes, BinaryIO, Path, str, tuple[str, bytes], "UploadedImage"]

# Confiança mínima para aceitar ranhuras/Ø automáticos (Fase 3 — sem erro 500, pede manual)
VISION_MIN_CONFIDENCE = 0.40
VISION_BLOCK_CONFIDENCE = 0.25

MSG_VISAO_ILEGIVEL = (
    "Foto ilegível ou sem escala confiável — preencha ranhuras e diâmetro manualmente."
)
MSG_HEIC_SEM_SUPORTE = (
    "Formato HEIC não suportado neste servidor. Instale pillow-heif ou envie JPG/PNG."
)


@dataclass
class PreparedVisionImage:
    jpeg_bytes: bytes
    mime_type: str
    file_name: str
    meta: dict[str, Any]


def _source_name_and_bytes(source: ImageSource) -> tuple[str, bytes]:
    if isinstance(source, tuple) and len(source) >= 2:
        return str(source[0] or "upload.jpg"), bytes(source[1])
    if isinstance(source, bytes):
        return "upload.bin", source
    if isinstance(source, (Path, str)):
        path = Path(source)
        return path.name, path.read_bytes()
    if hasattr(source, "getvalue") and hasattr(source, "name"):
        name = getattr(source, "name", None) or "upload.jpg"
        return str(name), source.getvalue()
    if hasattr(source, "read"):
        name = getattr(source, "name", None) or "upload.jpg"
        return str(name), source.read()
    raise TypeError(f"Fonte de imagem não suportada: {type(source)!r}")


def prepare_image_for_vision(source: ImageSource) -> PreparedVisionImage:
    """Pipeline: HEIC→JPEG, resize, limite de bytes — pronto para Gemini."""
    file_name, raw = _source_name_and_bytes(source)
    mime, _ = mimetypes.guess_type(file_name)
    jpeg, out_mime, meta = normalize_image_for_api(
        raw, file_name=file_name, mime_type=mime or ""
    )
    return PreparedVisionImage(
        jpeg_bytes=jpeg,
        mime_type=out_mime,
        file_name=file_name,
        meta=meta,
    )


def prepare_images_for_vision(sources: list[ImageSource]) -> list[PreparedVisionImage]:
    prepared: list[PreparedVisionImage] = []
    errors: list[str] = []
    for src in sources:
        try:
            prepared.append(prepare_image_for_vision(src))
        except Exception as exc:
            errors.append(str(exc))
    if not prepared and errors:
        raise RuntimeError("; ".join(errors))
    return prepared


def encode_image_part(source: ImageSource) -> dict[str, Any]:
    """Parte inline para API Gemini (base64) após normalização."""
    prep = prepare_image_for_vision(source)
    return {
        "mime_type": prep.mime_type,
        "data": base64.b64encode(prep.jpeg_bytes).decode("ascii"),
        "_meta": prep.meta,
        "_file_name": prep.file_name,
    }


def prompt_stator_vision_extraction(entrada: dict[str, Any]) -> str:
    import json

    dims = json.dumps(entrada, ensure_ascii=False, indent=2)
    return (
        "Voce e especialista em visao computacional aplicada a motores eletricos (WEG/IEC).\n"
        "Modo CAIXA PRETA: estator VAZIO (sem cobre), sem placa de identificacao.\n\n"
        "EXECUTE ESTRITAMENTE ESTAS ETAPAS em cada imagem:\n"
        "1) ESCALA: localize qualquer objeto de referencia (regua, paquimetro, fita metrica, "
        "moeda com diametro conhecido, cartao padrao). Descreva a escala usada.\n"
        "2) COROA: identifique a coroa do estator (anel com ranhuras).\n"
        "3) CONTAGEM: conte as ranhuras (slots) uma a uma na coroa visivel. "
        "Se a foto cortar metade do estator, estime o total se a simetria permitir; "
        "senao reduza confianca_visao.\n"
        "4) METROLOGIA: estime diametro interno da coroa em mm usando a escala. "
        "Estime area de uma ranhura tipica em mm2.\n\n"
        f"Dados do tecnico (referencia, nao substituem a contagem visual):\n{dims}\n\n"
        "Se a foto estiver escura, borrada, sem escala ou com angulo que impede contar ranhuras, "
        "defina confianca_visao baixa (< 0.35) e use null nos campos numericos.\n\n"
        "Responda APENAS JSON com EXATAMENTE estas chaves (sem chaves extras):\n"
        "{\n"
        '  "ranhuras_contadas": <int ou null>,\n'
        '  "diametro_estimado_mm": <float ou null>,\n'
        '  "area_ranhura_estimada_mm2": <float ou null>,\n'
        '  "confianca_visao": <float entre 0.0 e 1.0>\n'
        "}\n"
    )


def normalize_vision_response(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Unifica resposta Gemini (chaves novas ou legadas) e deriva flags de bloqueio UI.
    """
    if not isinstance(raw, dict):
        return {
            "erro": "Resposta de visao invalida",
            "confianca_visao": 0.0,
            "confianca_visao_0_100": 0,
            "visao_ilegivel": True,
            "exige_entrada_manual": True,
        }

    conf = raw.get("confianca_visao")
    if conf is None:
        conf = raw.get("confianca_visao_0_100")
        if conf is not None:
            try:
                conf = float(conf) / 100.0
            except (TypeError, ValueError):
                conf = 0.0
    try:
        conf_f = max(0.0, min(1.0, float(conf or 0)))
    except (TypeError, ValueError):
        conf_f = 0.0

    ran = raw.get("ranhuras_contadas")
    if ran is None and raw.get("ranhuras") is not None:
        ran = raw.get("ranhuras")
    try:
        ran_i = int(ran) if ran is not None else None
        if ran_i is not None and ran_i <= 0:
            ran_i = None
    except (TypeError, ValueError):
        ran_i = None

    diam = raw.get("diametro_estimado_mm")
    if diam is None:
        diam = raw.get("diametro_interno_mm") or raw.get("diametro_externo_mm")
    try:
        diam_f = float(diam) if diam is not None else None
        if diam_f is not None and diam_f <= 0:
            diam_f = None
    except (TypeError, ValueError):
        diam_f = None

    area = raw.get("area_ranhura_estimada_mm2")
    if area is None:
        area = raw.get("area_ranhura_mm2_estimada")
    try:
        area_f = float(area) if area is not None else None
        if area_f is not None and area_f <= 0:
            area_f = None
    except (TypeError, ValueError):
        area_f = None

    ilegivel = conf_f < VISION_BLOCK_CONFIDENCE or (
        conf_f < VISION_MIN_CONFIDENCE and (ran_i is None or diam_f is None)
    )
    exige_manual = ilegivel or conf_f < VISION_MIN_CONFIDENCE

    out: dict[str, Any] = {
        "ranhuras_contadas": ran_i,
        "diametro_estimado_mm": diam_f,
        "area_ranhura_estimada_mm2": area_f,
        "confianca_visao": round(conf_f, 3),
        "confianca_visao_0_100": int(round(conf_f * 100)),
        "visao_ilegivel": ilegivel,
        "exige_entrada_manual": exige_manual,
        "escala_detectada": raw.get("escala_detectada") or "",
        "observacoes": raw.get("observacoes") or raw.get("erro") or "",
    }
    if ilegivel and not out["observacoes"]:
        out["observacoes"] = MSG_VISAO_ILEGIVEL
    if raw.get("erro"):
        out["erro"] = raw["erro"]
    return out


def is_vision_reliable(vision: dict[str, Any]) -> bool:
    v = normalize_vision_response(vision)
    if v.get("visao_ilegivel"):
        return False
    try:
        conf = float(v.get("confianca_visao") or 0)
    except (TypeError, ValueError):
        return False
    return conf >= VISION_MIN_CONFIDENCE


def build_multimodal_payload(
    *,
    images: list[ImageSource],
    texto_contexto: str,
    entrada: dict[str, Any],
) -> dict[str, Any]:
    """Payload unificado para análise multimodal (Modo Caixa Preta)."""
    parts: list[dict[str, Any]] = []
    prep_meta: list[dict[str, Any]] = []
    for img in images:
        prep = prepare_image_for_vision(img)
        prep_meta.append(
            {
                "file": prep.file_name,
                "heif_supported": HEIF_SUPPORTED,
                **prep.meta,
            }
        )
        parts.append(
            {
                "inline_data": {
                    "mime_type": prep.mime_type,
                    "data": base64.b64encode(prep.jpeg_bytes).decode("ascii"),
                }
            }
        )
    parts.append({"text": texto_contexto})
    return {
        "parts": parts,
        "entrada": entrada,
        "n_imagens": len(images),
        "preprocess_meta": prep_meta,
        "instrucoes_visao": (
            "Escala geométrica → contagem de ranhuras na coroa → diâmetro e área em mm."
        ),
    }


def extract_stator_geometry_from_images(
    images: list[ImageSource],
    entrada: dict[str, Any],
    *,
    require_ok: bool = False,
    call_api: bool = True,
) -> dict[str, Any]:
    """
    Normaliza imagens, chama Gemini multimodal e retorna JSON padronizado.
    Nunca propaga exceção bruta — fallback com confianca_visao baixa.
    """
    if not images:
        return normalize_vision_response(
            {"erro": "Nenhuma imagem fornecida", "confianca_visao": 0.0}
        )

    try:
        prepare_images_for_vision(images)
    except RuntimeError as exc:
        msg = str(exc)
        if "HEIC" in msg or "heif" in msg.lower():
            msg = MSG_HEIC_SEM_SUPORTE
        return normalize_vision_response({"erro": msg, "confianca_visao": 0.0})
    except Exception as exc:
        return normalize_vision_response({"erro": str(exc), "confianca_visao": 0.0})

    if not call_api:
        return normalize_vision_response(
            {
                "ranhuras_contadas": None,
                "diametro_estimado_mm": None,
                "area_ranhura_estimada_mm2": None,
                "confianca_visao": 0.0,
                "observacoes": "API desligada (modo teste)",
            }
        )

    payload = build_multimodal_payload(
        images=images,
        texto_contexto=prompt_stator_vision_extraction(entrada),
        entrada=entrada,
    )

    try:
        from config.api_manager import get_gemini_api_manager

        mgr = get_gemini_api_manager()
        raw = mgr.call_multimodal_json(
            prompt_text=payload["parts"][-1]["text"],
            image_parts=[p["inline_data"] for p in payload["parts"][:-1]],
            require_ok=require_ok,
        )
        out = normalize_vision_response(raw)
        out["preprocess_meta"] = payload.get("preprocess_meta")
        return out
    except Exception as exc:
        return normalize_vision_response(
            {
                "erro": f"Falha na API de visao: {exc}",
                "confianca_visao": 0.0,
                "observacoes": MSG_VISAO_ILEGIVEL,
            }
        )


def merge_vision_into_entrada(
    entrada: dict[str, Any],
    vision: dict[str, Any],
) -> dict[str, Any]:
    """
    Funde extração visual com formulário.
    Só preenche campos vazios se a visão for confiável; senão marca checklist manual.
    """
    out = dict(entrada)
    vision = normalize_vision_response(vision)
    reliable = is_vision_reliable(vision)

    if reliable and vision.get("ranhuras_contadas") and not out.get("ranhuras"):
        out["ranhuras"] = int(vision["ranhuras_contadas"])
    if reliable and vision.get("diametro_estimado_mm") and not out.get("diametro_mm"):
        out["diametro_mm"] = float(vision["diametro_estimado_mm"])
    if reliable and vision.get("area_ranhura_estimada_mm2"):
        out["area_ranhura_mm2"] = float(vision["area_ranhura_estimada_mm2"])

    out["visao_computacional"] = vision
    if vision.get("exige_entrada_manual"):
        checklist = list(out.get("checklist_visao") or [])
        if MSG_VISAO_ILEGIVEL not in checklist:
            checklist.append(MSG_VISAO_ILEGIVEL)
        if not vision.get("ranhuras_contadas") and not out.get("ranhuras"):
            checklist.append("Contagem de ranhuras — conferir na bancada ou nova foto com escala")
        if not vision.get("diametro_estimado_mm") and not out.get("diametro_mm"):
            checklist.append("Diâmetro do estator (mm) — medir com paquímetro ou régua na foto")
        out["checklist_visao"] = checklist
    return out


def vision_status_message(vision: dict[str, Any]) -> str:
    """Mensagem amigável para UI (sem stack trace)."""
    v = normalize_vision_response(vision)
    if v.get("erro"):
        return str(v["erro"])
    conf = v.get("confianca_visao_0_100", 0)
    if v.get("visao_ilegivel"):
        return f"Visão: foto ilegível ({conf}% confiança). {MSG_VISAO_ILEGIVEL}"
    if v.get("exige_entrada_manual"):
        return f"Visão: confiança moderada ({conf}%) — confira ranhuras e diâmetro no formulário."
    ran = v.get("ranhuras_contadas", "—")
    diam = v.get("diametro_estimado_mm", "—")
    return f"Visão: {conf}% — ranhuras={ran}, Ø≈{diam} mm"
