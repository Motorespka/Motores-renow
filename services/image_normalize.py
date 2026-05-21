#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Normalização de imagens para APIs multimodais (HEIC/HEIF → JPEG, resize, limite de tamanho).
"""

from __future__ import annotations

import io
from typing import Optional, Tuple

from PIL import Image

try:
    from pillow_heif import register_heif_opener

    register_heif_opener()
    HEIF_SUPPORTED = True
except Exception:
    HEIF_SUPPORTED = False

# Limites seguros para Gemini inline (conservador)
MAX_IMAGE_BYTES = 4 * 1024 * 1024
MAX_EDGE_PX = 2048
JPEG_QUALITY = 88


def _looks_like_jpeg(raw: bytes) -> bool:
    return len(raw) >= 3 and raw[:3] == b"\xff\xd8\xff"


def _looks_like_png(raw: bytes) -> bool:
    return len(raw) >= 8 and raw[:8] == b"\x89PNG\r\n\x1a\n"


def _looks_like_heif_family(raw: bytes) -> bool:
    if len(raw) < 12:
        return False
    if raw[4:8] != b"ftyp":
        return False
    return raw[8:12] in {
        b"heic",
        b"heix",
        b"hevc",
        b"hevx",
        b"mif1",
        b"msf1",
        b"avif",
        b"avis",
    }


def normalize_image_for_api(
    raw_bytes: bytes,
    *,
    file_name: str = "",
    mime_type: str = "",
) -> Tuple[bytes, str, dict]:
    """
    Converte HEIC/HEIF/PNG/WebP → JPEG otimizado em memória.
    Retorna (bytes, mime, meta) com flags de conversão e dimensões finais.
    """
    lower = (file_name or "").lower().strip()
    mime = (mime_type or "").lower().strip()
    meta: dict = {
        "original_bytes": len(raw_bytes),
        "heif_converted": False,
        "resized": False,
    }

    if not raw_bytes:
        raise ValueError("Imagem vazia.")

    is_heif = (
        lower.endswith((".heic", ".heif", ".avif"))
        or mime
        in {
            "image/heic",
            "image/heif",
            "image/heic-sequence",
            "image/heif-sequence",
            "image/avif",
        }
        or _looks_like_heif_family(raw_bytes)
    )

    if is_heif and not HEIF_SUPPORTED:
        raise RuntimeError(
            "Arquivo HEIC/HEIF detectado, mas pillow-heif não está instalado. "
            "Execute: pip install pillow-heif>=0.13.0"
        )

    if _looks_like_jpeg(raw_bytes) and not is_heif:
        jpeg_bytes = raw_bytes
    elif _looks_like_png(raw_bytes) and lower.endswith(".png") and not is_heif:
        img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True)
        jpeg_bytes = buf.getvalue()
        meta["heif_converted"] = True
    else:
        img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True)
        jpeg_bytes = buf.getvalue()
        meta["heif_converted"] = is_heif or not _looks_like_jpeg(raw_bytes)

    img = Image.open(io.BytesIO(jpeg_bytes))
    w, h = img.size
    meta["width_before"] = w
    meta["height_before"] = h

    longest = max(w, h)
    if longest > MAX_EDGE_PX:
        scale = MAX_EDGE_PX / float(longest)
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        meta["resized"] = True

    buf = io.BytesIO()
    quality = JPEG_QUALITY
    img.save(buf, format="JPEG", quality=quality, optimize=True)
    out = buf.getvalue()

    while len(out) > MAX_IMAGE_BYTES and quality > 52:
        quality -= 8
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        out = buf.getvalue()
    meta["jpeg_quality"] = quality
    meta["final_bytes"] = len(out)
    meta["width_after"], meta["height_after"] = img.size

    if len(out) > MAX_IMAGE_BYTES:
        raise ValueError(
            f"Imagem ainda excede {MAX_IMAGE_BYTES // (1024*1024)} MB após compressão "
            f"({len(out)} bytes). Use foto com resolução menor."
        )

    return out, "image/jpeg", meta
