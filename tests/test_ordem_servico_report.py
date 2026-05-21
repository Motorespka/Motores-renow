#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from services.ordem_servico_report import (
    build_ordem_servico_html,
    calculation_ready_for_export,
    collect_export_rows,
)


def test_ready_twin_complete():
    assert calculation_ready_for_export(
        {"completo": True, "bloqueado": False, "candidatos": [{"opcao": "A"}]},
        None,
        None,
    )


def test_not_ready_twin_blocked():
    assert not calculation_ready_for_export(
        {"completo": False, "bloqueado": True, "checklist": ["x"]},
        None,
        None,
    )


def test_ready_optimizer():
    assert calculation_ready_for_export(
        None,
        {"cenarios": [{"cenario_id": "B", "espiras": 45}]},
        None,
    )


def test_build_html_contains_sections():
    html_doc = build_ordem_servico_html(
        entrada={
            "diametro_mm": 80,
            "pacote_mm": 70,
            "ranhuras": 24,
            "polos": 2,
            "tensao_v": 220,
            "ligacao": "Estrela",
        },
        twin_data={
            "completo": True,
            "modo": "auditoria",
            "candidatos": [
                {
                    "opcao": "SUSPEITO",
                    "espiras_por_bobina": 8,
                    "descricao": "1x 14 AWG",
                    "densidade_j": 12.5,
                    "ocupacao_ff": 0.35,
                    "confianca_pct": 0,
                }
            ],
        },
    )
    assert "ORDEM DE SERVIÇO" in html_doc
    assert "Observações do técnico" in html_doc
    assert "Assinatura" in html_doc
    assert "24" in html_doc
    assert "SUSPEITO" in html_doc
    assert "window.print" in html_doc


def test_collect_rows_optimizer():
    rows = collect_export_rows(
        None,
        {
            "cenarios": [
                {
                    "cenario_id": "B",
                    "espiras": 45,
                    "fio_texto": "1x 19 AWG",
                    "current_density_j": 4.0,
                    "fill_factor_ff": 0.35,
                    "confidence_score": 88,
                }
            ]
        },
        None,
    )
    assert len(rows) == 1
    assert rows[0]["espiras"] == 45
