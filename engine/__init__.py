#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Motores de engenharia (otimizador de bobinagem, etc.)."""

from engine.winding_optimizer import (
    StatorInput,
    WindingOptimizationResult,
    WindingOptimizer,
    WindingScenario,
)

__all__ = [
    "StatorInput",
    "WindingOptimizationResult",
    "WindingOptimizer",
    "WindingScenario",
]
