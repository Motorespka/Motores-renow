"""Deteção NEMA 42 compacta (NEMA42) e campo Carcaca PascalCase."""

from utils.motor_hologram_glb import (
    _is_nema_42_frame,
    motor_matches_weg_style_carcaca_for_glb,
    nema42_glb_url_efectiva,
    resolve_model_glb_url,
)


def test_nema42_compact_no_space():
    m = {"dados_tecnicos_json": {"mecanica": {"carcaca": "NEMA42"}, "motor": {}}}
    assert _is_nema_42_frame(m)
    u = resolve_model_glb_url(m, "auto")
    assert u and "nema%2042%20closed%20(1).glb" in u


def test_nema42_pascal_case_top_level():
    m = {"Carcaca": "NEMA42"}
    assert _is_nema_42_frame(m)
    u = resolve_model_glb_url(m, "auto")
    assert u and "42" in u


def test_nema42_spaced_still_matches():
    m = {"carcaca": "NEMA 42"}
    assert _is_nema_42_frame(m)


def test_nema42_only_on_quadro_json():
    m = {"dados_tecnicos_json": {"mecanica": {"quadro": "NEMA 42"}, "motor": {}}}
    assert _is_nema_42_frame(m)


def test_nema42_in_modelo_only():
    m = {"dados_tecnicos_json": {"mecanica": {}, "motor": {"modelo": "WEG NEMA42 2HP"}}}
    assert _is_nema_42_frame(m)


def test_nema42_mecanica_pascal_key():
    m = {"dados_tecnicos_json": {"Mecanica": {"carcaca": "NEMA42"}, "motor": {}}}
    assert _is_nema_42_frame(m)


def test_nema42_counts_for_weg_or_nema_rule():
    m = {"dados_tecnicos_json": {"mecanica": {"carcaca": "NEMA42"}, "motor": {}}}
    assert motor_matches_weg_style_carcaca_for_glb(m) is True


def test_nema42_glb_url_efectiva_default():
    u = nema42_glb_url_efectiva()
    assert u and "nema" in u and "42" in u and "closed" in u and ".glb" in u
