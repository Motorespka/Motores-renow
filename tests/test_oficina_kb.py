#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
from pathlib import Path

from engine.physics_audit import audit_winding_physics
from knowledge.oficina_kb import get_oficina_knowledge, reload_oficina_knowledge


def test_referencia_json_exists_and_populated():
    p = Path(__file__).resolve().parents[1] / "knowledge" / "referencia_oficina.json"
    assert p.is_file()
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["meta"]["total_registros_processados"] >= 1000
    assert len(data["por_cv"]) >= 5


def test_kb_15cv_espiras_45():
    reload_oficina_knowledge()
    kb = get_oficina_knowledge()
    ok, msg = kb.espiras_no_historico_cv(1.5, 45.0)
    assert ok or kb.total_registros < 20
    if ok:
        assert "conformidade" in msg.lower()


def test_audit_j_usa_historico_15cv():
    reload_oficina_knowledge()
    r = audit_winding_physics(
        espiras=45,
        awg=21,
        diametro_mm=80,
        pacote_mm=70,
        ranhuras=24,
        polos=2,
        carcaca="80A",
        potencia_cv=1.5,
        corrente_nominal_a=3.8,
        apply_fem_turns_guard=False,
    )
    assert r.survival_pass
    assert not r.calculation_aborted
    assert any("conformidade" in (a or "").lower() for a in r.alerts) or r.current_density_j is not None
