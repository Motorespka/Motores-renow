"""Testes da camada ``motor_rebobinagem`` (read-only)."""

from __future__ import annotations

import unittest

from services.motor_rebobinagem import analyze_rewinding_coherence, build_rewinding_signature
from services.motor_rebobinagem.normalization import (
    normalize_rewinding_input,
    parse_espiras_field,
    parse_fio_field,
    parse_passo_field,
)
from services.motor_rebobinagem.serialization import prepare_fastapi_rebobinagem_payload
from services.motor_rebobinagem.signature import prepare_similarity_query


def _payload(**kwargs):
    base = {
        "motor": {
            "rpm": "1750",
            "polos": "4",
            "frequencia": "60",
            "tensao": ["380"],
            "corrente": ["10"],
            "fases": "Trifasico",
            "potencia": "5 cv",
            "fator_potencia": "0.85",
            "rendimento": "0.85",
        },
        "bobinagem_principal": {},
        "bobinagem_auxiliar": {},
        "esquema": {},
        "mecanica": {},
    }
    base.update(kwargs)
    return base


class TestParsing(unittest.TestCase):
    def test_passo_formats(self):
        a = parse_passo_field("1:8:10")
        self.assertEqual(a["numbers"], [1, 8, 10])
        b = parse_passo_field("1-8-10")
        self.assertEqual(b["numbers"], [1, 8, 10])
        c = parse_passo_field(["1:8:10"])
        self.assertEqual(c["numbers"], [1, 8, 10])

    def test_espiras(self):
        e = parse_espiras_field("70:70")
        self.assertEqual(e["numbers"], [70, 70])

    def test_fio(self):
        f = parse_fio_field("1x22")
        self.assertEqual(f.get("parallel"), 1)
        self.assertEqual(f.get("gauge_token"), "22")

    def test_ocr_noisy_passo(self):
        p = parse_passo_field("1 ~ 8 ? 10")
        self.assertTrue(p.get("needs_review") or p.get("numbers"))


class TestAnalyze(unittest.TestCase):
    def test_insufficient_empty(self):
        rep = analyze_rewinding_coherence({"motor": {}, "bobinagem_principal": {}, "bobinagem_auxiliar": {}})
        self.assertEqual(rep["validation"]["status"], "insuficiente")

    def test_principal_passo_sem_espiras(self):
        rep = analyze_rewinding_coherence(
            _payload(
                bobinagem_principal={"passos": ["1:8:10"], "espiras": []},
            )
        )
        codes = [w["code"] for w in rep["validation"].get("warnings", [])]
        self.assertIn("principal_passo_sem_espiras", codes)
        self.assertNotEqual(rep["validation"]["status"], "critico")

    def test_rpm_above_sync_critico(self):
        rep = analyze_rewinding_coherence(
            _payload(
                motor={
                    "rpm": "1900",
                    "polos": "4",
                    "frequencia": "60",
                    "tensao": ["380"],
                    "corrente": ["10"],
                    "fases": "Trifasico",
                    "potencia": "5 cv",
                    "fator_potencia": "0.85",
                    "rendimento": "0.85",
                },
                bobinagem_principal={"passos": ["1:6"], "espiras": ["10"]},
            )
        )
        self.assertEqual(rep["validation"]["status"], "critico")

    def test_signature_stable(self):
        raw = _payload(bobinagem_principal={"passos": ["1:8"], "espiras": ["20"], "fios": ["1x21"]})
        n = normalize_rewinding_input(raw)
        el = {
            "power_kw": 3.67,
            "rpm_nominal": 1750.0,
            "poles": 4,
            "frequency_hz": 60.0,
            "phases": "tri",
            "tensions_v": [380.0],
            "tipo_motor": "inducao",
        }
        s1 = build_rewinding_signature(electric_summary=el, rewinding_normalized=n)
        s2 = build_rewinding_signature(electric_summary=el, rewinding_normalized=n)
        self.assertEqual(s1["signature_digest"], s2["signature_digest"])
        q = prepare_similarity_query(s1)
        self.assertIn("payload", q)

    def test_serialization(self):
        rep = analyze_rewinding_coherence(
            _payload(bobinagem_principal={"passos": ["1"], "espiras": ["1"], "fios": ["1x20"]})
        )
        out = prepare_fastapi_rebobinagem_payload(rep)
        self.assertIsInstance(out, dict)


if __name__ == "__main__":
    unittest.main()
