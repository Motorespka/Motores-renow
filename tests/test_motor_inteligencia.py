"""
Testes da camada ``motor_inteligencia`` (cálculos, normalização, validação).

Executar: ``python -m unittest tests.test_motor_inteligencia -v``
"""

from __future__ import annotations

import unittest

from services.motor_inteligencia import analyze_motor_technical, validate_motor
from services.motor_inteligencia.batch_review import build_batch_review_report
from services.motor_inteligencia.calculations import calc_ns_rpm, calc_slip_percent, compute_derived_metrics
from services.motor_inteligencia.coercion import coerce_supabase_motor_row
from services.motor_inteligencia.normalization import (
    normalize_motor_inteligencia_input,
    parse_power_kw,
    parse_rpm,
    parse_voltage_list,
)
from services.motor_inteligencia.serialization import intel_report_to_jsonable, prepare_fastapi_intel_payload


def _motor(**kw):
    return {"motor": kw}


class TestNormalization(unittest.TestCase):
    def test_parse_power_variants(self):
        kw, notes, raw = parse_power_kw("10 cv", "")
        self.assertAlmostEqual(kw, 10 * 0.735499, places=3)
        kw2, _, _ = parse_power_kw("7,5 kW", "")
        self.assertAlmostEqual(kw2, 7.5, places=2)
        kw3, _, _ = parse_power_kw("10cv", "")
        self.assertIsNotNone(kw3)

    def test_parse_rpm_ocr(self):
        r, notes, amb = parse_rpm("1750 rpm")
        self.assertEqual(r, 1750.0)
        r2, _, amb2 = parse_rpm("3.450")
        self.assertEqual(r2, 3450.0)
        self.assertTrue(amb2)

    def test_normalize_incomplete(self):
        n = normalize_motor_inteligencia_input(_motor())
        self.assertIsNone(n.get("rpm_nominal"))
        self.assertIn("insufficient_for", n)

    def test_parse_voltage_multi(self):
        volts, _ = parse_voltage_list("220/380")
        self.assertIn(220.0, volts)
        self.assertIn(380.0, volts)


class TestCalculations(unittest.TestCase):
    def test_ns_2p_60hz(self):
        b = calc_ns_rpm(60, 2)
        self.assertEqual(b["value"], 3600.0)

    def test_ns_4p_60hz(self):
        b = calc_ns_rpm(60, 4)
        self.assertEqual(b["value"], 1800.0)

    def test_ns_6p_60hz(self):
        b = calc_ns_rpm(60, 6)
        self.assertEqual(b["value"], 1200.0)

    def test_ns_4p_50hz(self):
        b = calc_ns_rpm(50, 4)
        self.assertEqual(b["value"], 1500.0)

    def test_slip(self):
        ns = calc_ns_rpm(60, 4)["value"]
        s = calc_slip_percent(ns, 1750)
        self.assertAlmostEqual(s["value"], (1800 - 1750) / 1800 * 100, places=2)


class TestValidation(unittest.TestCase):
    def test_rpm_above_sync_critical(self):
        raw = _motor(
            rpm="1900",
            polos="4",
            frequencia="60",
            tensao=["380"],
            corrente="10",
            fases="Trifasico",
            potencia="5 cv",
            fator_potencia="0.85",
            rendimento="0.85",
        )
        v = validate_motor(raw)
        self.assertEqual(v["status"], "critico")
        codes = [i["code"] for i in v.get("issues", [])]
        self.assertIn("rpm_above_sync", codes)

    def test_mono_pin_path(self):
        raw = _motor(
            rpm="1750",
            polos="4",
            frequencia="60 Hz",
            tensao="220",
            corrente="10",
            fases="Monofasico",
            potencia="2 cv",
            fator_potencia="0.82",
            rendimento="0.8",
        )
        rep = analyze_motor_technical(raw)
        self.assertIn("pin_kw", rep["derived"]["_blocks"])
        pin = rep["derived"]["_blocks"]["pin_kw"]["value"]
        self.assertIsNotNone(pin)
        # mono: V*I*fp/1000
        self.assertAlmostEqual(pin, 220 * 10 * 0.82 / 1000.0, places=3)

    def test_tri_pin_sqrt3(self):
        raw = _motor(
            rpm="1750",
            polos="4",
            frequencia="60",
            tensao="380",
            corrente="10",
            fases="Trifasico",
            potencia="5 cv",
            fator_potencia="0.85",
            rendimento="0.85",
        )
        rep = analyze_motor_technical(raw)
        pin = rep["derived"]["pin_kw"]
        self.assertIsNotNone(pin)

    def test_coerce_row_flat_columns(self):
        row = {
            "dados_tecnicos_json": {"motor": {}},
            "rpm_nominal": "1745RPM",
            "polos": "4",
            "frequencia_hz": "60",
            "tensao_v": "220/380",
            "corrente_nominal_a": "12,5",
            "fases": "Trifasico",
            "potencia_hp_cv": "5cv",
        }
        coerced = coerce_supabase_motor_row(row)
        rep = analyze_motor_technical(coerced)
        self.assertIsNotNone(rep["derived"].get("ns_rpm"))


class TestFuture(unittest.TestCase):
    def test_analyze_has_future_block(self):
        rep = analyze_motor_technical(_motor(rpm="1750", polos="4", frequencia="60"))
        self.assertIsInstance(rep.get("future_calculations"), list)
        self.assertTrue(len(rep["future_calculations"]) >= 1)


class TestSeverityPhase2(unittest.TestCase):
    def test_sparse_motor_not_alert(self):
        """Poucos dados → insuficiente, não alerta por lacuna sozinha."""
        v = validate_motor(_motor())
        self.assertEqual(v.get("status"), "insuficiente")

    def test_summary_one_liner_present(self):
        rep = analyze_motor_technical(_motor(rpm="1750", polos="4", frequencia="60 Hz"))
        self.assertTrue(rep.get("summary_one_liner"))
        self.assertIn("summary_one_liner", rep)

    def test_ocr_flag_alert_not_critical(self):
        raw = _motor(
            rpm="1750",
            polos="4",
            frequencia="60",
            tensao="380",
            corrente="10",
            fases="Trifasico",
            potencia="5 cv",
            fator_potencia="0.85",
            rendimento="0.85",
        )
        raw["oficina"] = {"parser_tecnico": {"needs_review": True, "ambiguous": False}}
        v = validate_motor(raw)
        self.assertNotEqual(v.get("status"), "critico")

    def test_batch_review_structure(self):
        rows = [
            {"id": "1", "marca": "A", "modelo": "X", "dados_tecnicos_json": {"motor": {"rpm": "1750", "polos": "4", "frequencia": "60"}}},
            {"id": "2", "marca": "B", "modelo": "Y", "dados_tecnicos_json": {"motor": {}}},
        ]
        rep = build_batch_review_report(rows, limit=10)
        self.assertIn("por_status", rep)
        self.assertIn("top_issues", rep)
        self.assertEqual(rep["meta"]["total_analisado"], 2)

    def test_serialization_roundtrip(self):
        rep = analyze_motor_technical(_motor(rpm="1750", polos="4", frequencia="60"))
        out = prepare_fastapi_intel_payload(rep)
        self.assertIsNone(intel_report_to_jsonable(None))
        self.assertIsInstance(out, dict)


if __name__ == "__main__":
    unittest.main()
