#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import io

import pytest
from PIL import Image

from services.image_normalize import (
    HEIF_SUPPORTED,
    MAX_EDGE_PX,
    MAX_IMAGE_BYTES,
    normalize_image_for_api,
)
from services.stator_vision_ingest import (
    merge_vision_into_entrada,
    normalize_vision_response,
    prepare_image_for_vision,
    prompt_stator_vision_extraction,
    extract_stator_geometry_from_images,
    is_vision_reliable,
)


def _jpeg_bytes(w: int = 800, h: int = 600) -> bytes:
    img = Image.new("RGB", (w, h), color=(120, 80, 40))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def test_normalize_jpeg_passthrough_size():
    raw = _jpeg_bytes(400, 300)
    out, mime, meta = normalize_image_for_api(raw, file_name="stator.jpg")
    assert mime == "image/jpeg"
    assert len(out) <= MAX_IMAGE_BYTES
    assert meta["final_bytes"] == len(out)


def test_resize_large_image():
    raw = _jpeg_bytes(MAX_EDGE_PX + 500, MAX_EDGE_PX + 200)
    out, mime, meta = normalize_image_for_api(raw, file_name="big.jpg")
    assert mime == "image/jpeg"
    assert meta.get("resized") is True
    img = Image.open(io.BytesIO(out))
    assert max(img.size) <= MAX_EDGE_PX


def test_prepare_image_for_vision_tuple():
    prep = prepare_image_for_vision(("1000094064.heic", _jpeg_bytes()))
    assert prep.mime_type == "image/jpeg"
    assert len(prep.jpeg_bytes) > 100


@pytest.mark.skipif(not HEIF_SUPPORTED, reason="pillow-heif não instalado")
def test_heic_extension_converts():
    # JPEG disfarçado com extensão .heic — PIL abre após register_heif
    raw = _jpeg_bytes()
    out, mime, meta = normalize_image_for_api(raw, file_name="motor.heic")
    assert mime == "image/jpeg"
    assert out[:3] == b"\xff\xd8\xff"


def test_normalize_vision_response_exact_keys():
    raw = {
        "ranhuras_contadas": 24,
        "diametro_estimado_mm": 80.5,
        "area_ranhura_estimada_mm2": 12.3,
        "confianca_visao": 0.82,
    }
    v = normalize_vision_response(raw)
    assert v["ranhuras_contadas"] == 24
    assert v["diametro_estimado_mm"] == 80.5
    assert v["confianca_visao_0_100"] == 82
    assert v["visao_ilegivel"] is False
    assert is_vision_reliable(v)


def test_low_confidence_blocks_auto_fill():
    v = normalize_vision_response(
        {
            "ranhuras_contadas": None,
            "diametro_estimado_mm": None,
            "confianca_visao": 0.15,
        }
    )
    assert v["visao_ilegivel"] is True
    assert v["exige_entrada_manual"] is True
    ent = merge_vision_into_entrada({"diametro_mm": 80, "pacote_mm": 70}, v)
    assert ent.get("checklist_visao")
    assert not ent.get("ranhuras")


def test_legacy_keys_mapped():
    v = normalize_vision_response(
        {
            "ranhuras_contadas": 36,
            "diametro_interno_mm": 90,
            "area_ranhura_mm2_estimada": 8.0,
            "confianca_visao_0_100": 65,
        }
    )
    assert v["diametro_estimado_mm"] == 90.0
    assert v["confianca_visao"] == 0.65


def test_prompt_requires_exact_json_keys():
    p = prompt_stator_vision_extraction({"ranhuras": 24})
    assert "ranhuras_contadas" in p
    assert "diametro_estimado_mm" in p
    assert "confianca_visao" in p
    assert "contar as ranhuras" in p.lower() or "ranhuras" in p


def test_extract_without_api():
    v = extract_stator_geometry_from_images(
        [_jpeg_bytes()],
        {"diametro_mm": 80},
        call_api=False,
    )
    assert v["confianca_visao"] == 0.0
