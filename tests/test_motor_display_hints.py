"""Testes para textos de referência na UI (RPM síncrono teórico, etc.)."""

from __future__ import annotations

import unittest

from utils.motor_display_hints import (
    parse_frequency_hz,
    parse_poles_count,
    rpm_identificacao_display,
    synchronous_rpm_theoretical,
)


class TestMotorDisplayHints(unittest.TestCase):
    def test_sync_2p_50hz(self):
        self.assertAlmostEqual(synchronous_rpm_theoretical(50.0, 2), 3000.0, places=3)

    def test_sync_2p_60hz(self):
        self.assertAlmostEqual(synchronous_rpm_theoretical(60.0, 2), 3600.0, places=3)

    def test_parse_poles(self):
        self.assertEqual(parse_poles_count("2P"), 2)
        self.assertEqual(parse_poles_count("4 polos"), 4)

    def test_parse_freq(self):
        self.assertEqual(parse_frequency_hz("60Hz"), 60.0)
        self.assertEqual(parse_frequency_hz("50"), 50.0)

    def test_rpm_display_uses_placa_when_present(self):
        m = {"rpm_nominal": "3450", "polos": "2P", "frequencia_hz": 60}
        s = rpm_identificacao_display(m, {})
        self.assertIn("3450", s)
        self.assertNotIn("síncrona teórica", s)

    def test_rpm_display_reference_when_missing(self):
        m: dict = {"polos": "2P", "frequencia_hz": 50}
        motor_info: dict = {}
        s = rpm_identificacao_display(m, motor_info)
        self.assertIn("3000", s)
        self.assertIn("síncrona teórica", s)
        self.assertIn("não consta", s)


if __name__ == "__main__":
    unittest.main()
