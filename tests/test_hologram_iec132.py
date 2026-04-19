"""GLB dedicado IEC 132 (carcaça na ficha)."""

from utils.motor_hologram_glb import (
    iec132_glb_url_efectiva,
    motor_familia_iec132_silhueta_somente_ficha,
    motor_familia_iec_tefc_b3_catalogo_silhueta_somente_ficha,
    resolve_model_glb_url,
)


def test_iec132_etiqueta_compacta():
    m = {"dados_tecnicos_json": {"mecanica": {"carcaca": "IEC132"}, "motor": {}}}
    assert motor_familia_iec132_silhueta_somente_ficha(m) is True


def test_iec132_resolve_url():
    m = {
        "dados_tecnicos_json": {
            "mecanica": {"carcaca": "IEC 132 TEFC B3"},
            "motor": {},
        }
    }
    u = resolve_model_glb_url(m, "auto")
    assert u and "269c0156-2633-44cf-9d80-98c14483011c.glb" in u


def test_iec132_132m_com_b3_tefc():
    m = {
        "dados_tecnicos_json": {
            "mecanica": {"carcaca": "132M B3 TEFC"},
            "motor": {},
        }
    }
    assert motor_familia_iec132_silhueta_somente_ficha(m) is True


def test_iec132_glb_url_efectiva_embed():
    u = iec132_glb_url_efectiva()
    assert u and "269c0156" in u


def test_iec112_sem_sufixo_112m_entra_no_catalogo_tefc_b3():
    m = {
        "dados_tecnicos_json": {
            "mecanica": {"carcaca": "IEC 112 TEFC B3"},
            "motor": {},
        }
    }
    assert motor_familia_iec_tefc_b3_catalogo_silhueta_somente_ficha(m) is True
    u = resolve_model_glb_url(m, "generico")
    assert u and ".glb" in u.lower()
