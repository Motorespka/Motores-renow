"""Campos operacionais da OS (interno, sem PII)."""

from __future__ import annotations

import unittest

from services.oficina_os_operacao import (
    format_centavos_br,
    linhas_resumo_operacao_pdf,
    normalize_operacao_payload_patch,
    parse_centavos,
    parse_prazo_entrega_iso,
)


class TestOsOperacao(unittest.TestCase):
    def test_parse_centavos(self):
        self.assertEqual(parse_centavos(15050), 15050)
        self.assertEqual(parse_centavos("15050"), 15050)
        self.assertIsNone(parse_centavos(None))

    def test_prazo_iso(self):
        d, err = parse_prazo_entrega_iso("2026-04-30")
        self.assertEqual(d, "2026-04-30")
        self.assertIsNone(err)
        _, err2 = parse_prazo_entrega_iso("99-99-99")
        self.assertIsNotNone(err2)

    def test_normalize_patch_dono(self):
        out = normalize_operacao_payload_patch(
            {
                "referencia_interna_os": "NF 1234",
                "prazo_entrega_previsto": "2026-05-01",
                "orcamento_centavos": 500000,
                "custo_material_centavos": 100000,
                "custo_mao_obra_centavos": 150000,
            }
        )
        self.assertEqual(out["orcamento_centavos"], 500000)
        self.assertEqual(out["referencia_interna_os"], "NF 1234")

    def test_format_centavos_br(self):
        self.assertIn("5.000,00", format_centavos_br(500000))

    def test_linhas_pdf(self):
        lines = linhas_resumo_operacao_pdf(
            {
                "referencia_interna_os": "X",
                "prazo_entrega_previsto": "2026-01-15",
                "orcamento_centavos": 10000,
                "custo_material_centavos": 3000,
                "custo_mao_obra_centavos": 4000,
            }
        )
        self.assertTrue(any("Margem" in ln for ln in lines))


if __name__ == "__main__":
    unittest.main()
