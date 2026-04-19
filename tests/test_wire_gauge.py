"""Tecnico: AWG -> mm2 e inferencia a partir da ficha."""

from __future__ import annotations

import unittest

from services.motor_rebobinagem.normalization import parse_fio_field
from services.motor_rebobinagem.wire_gauge import (
    awg_integer_to_mm2,
    check_wire_vs_plate_current,
    conductor_area_mm2_from_principal_fios,
    infer_awg_from_gauge_token,
)


class TestWireGauge(unittest.TestCase):
    def test_awg18_area(self):
        a = awg_integer_to_mm2(18)
        self.assertIsNotNone(a)
        self.assertAlmostEqual(a, 0.823, places=2)

    def test_infer_awg_from_token(self):
        self.assertEqual(infer_awg_from_gauge_token("20", "2x20"), 20)

    def test_explicit_mm2(self):
        pr = parse_fio_field("1,25 mm2")
        area, _ = conductor_area_mm2_from_principal_fios(pr)
        self.assertAlmostEqual(float(area or 0), 1.25, places=2)

    def test_check_warns_when_too_thin(self):
        pr = parse_fio_field("AWG 30")
        w = check_wire_vs_plate_current(pr_f=pr, current_line_a=40.0)
        self.assertIsNotNone(w)
        self.assertEqual(w.get("code"), "fio_vs_corrente_placa")


if __name__ == "__main__":
    unittest.main()
