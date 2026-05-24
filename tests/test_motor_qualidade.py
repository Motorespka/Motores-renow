#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from services.motor_qualidade import (
    MSG_CALCULO_SEM_HISTORICO_OFICINA,
    avaliar_qualidade_motor,
    entrada_pode_usar_historico_oficina,
)
from engine.physics_audit import audit_winding_physics


def test_entrada_certificada_completa():
    q = avaliar_qualidade_motor(
        {
            "diametro_mm": "80",
            "pacote_mm": "70",
            "ranhuras": "24",
            "fio": ["1x19"],
            "espiras": ["45:45"],
        }
    )
    assert q["certificado"] is True
    assert entrada_pode_usar_historico_oficina(
        {
            "diametro_mm": 80,
            "pacote_mm": 70,
            "ranhuras": 24,
            "fio_engenheiro": "19",
            "espiras_engenheiro": "45",
        }
    )


def test_entrada_incompleta_sem_historico():
    q = avaliar_qualidade_motor({"diametro_mm": "80", "pacote_mm": "70"})
    assert q["certificado"] is False
    assert not entrada_pode_usar_historico_oficina({"diametro_mm": 80, "pacote_mm": 70})


def test_physics_audit_aviso_sem_geometria():
    r = audit_winding_physics(
        espiras=45,
        awg=19,
        diametro_mm=80,
        pacote_mm=70,
        ranhuras=24,
        polos=2,
        entrada_context={"diametro_mm": 80, "pacote_mm": 70},
        apply_fem_turns_guard=False,
    )
    assert any(MSG_CALCULO_SEM_HISTORICO_OFICINA in (a or "") for a in r.alerts)
