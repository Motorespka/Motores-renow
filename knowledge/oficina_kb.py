#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Consulta à base de conhecimento da oficina (referencia_oficina.json).
Prioridade sobre limites IEC teóricos na auditoria física.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from app.search_lib import norm_carcaca

_REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_JSON = _REPO_ROOT / "knowledge" / "referencia_oficina.json"

MSG_CONFORMIDADE_HISTORICO = (
    "Aviso de conformidade com histórico da oficina: parâmetro dentro da faixa "
    "dos {n} cálculos indexados no acervo OFICIAL."
)
MSG_CONFORMIDADE_CV_ESPIRAS = (
    "Aviso de conformidade com histórico: espiras dentro da faixa habitual da oficina "
    "para {cv} CV (acervo: {n} motores, típico {p10}–{p90} espiras)."
)
MSG_CONFORMIDADE_J_GEOM = (
    "Aviso de conformidade com histórico: densidade J dentro da faixa aceita pela oficina "
    "para carcaça/pacote {geom} (mediana histórica ≈ {med} A/mm²)."
)


def _cv_bucket(cv: float) -> str:
    if cv < 0.2:
        return "0.12"
    if cv < 0.35:
        return "0.25"
    if cv < 0.75:
        return "0.5"
    if cv < 1.25:
        return "1.0"
    if cv < 1.75:
        return "1.5"
    if cv < 2.5:
        return "2.0"
    if cv < 4:
        return "3.0"
    if cv < 7.5:
        return "5.0"
    if cv < 15:
        return "10.0"
    if cv < 35:
        return "20.0"
    return "50.0"


def _geom_bucket(carcaca: str, pacote_mm: Optional[float]) -> str:
    cn = norm_carcaca(carcaca) or "desconhecido"
    if pacote_mm is None or pacote_mm <= 0:
        return cn
    p = int(round(float(pacote_mm) / 5.0) * 5)
    return f"{cn}|{p}"


class OficinaKnowledge:
    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data
        self.por_cv: dict[str, Any] = data.get("por_cv") or {}
        self.por_geom: dict[str, Any] = data.get("por_carcaca_pacote") or {}
        self.global_stats: dict[str, Any] = data.get("global") or {}
        self.meta: dict[str, Any] = data.get("meta") or {}

    @property
    def total_registros(self) -> int:
        return int(self.meta.get("total_registros_processados") or self.global_stats.get("n_registros") or 0)

    def resolve_cv_bucket(self, cv: float) -> Optional[dict[str, Any]]:
        if cv <= 0:
            return None
        key = _cv_bucket(cv)
        if key in self.por_cv:
            return self.por_cv[key]
        best_key = None
        best_dist = 1e9
        for k, block in self.por_cv.items():
            try:
                rep = float(block.get("cv_representativo") or k)
            except ValueError:
                continue
            dist = abs(rep - cv)
            if dist < best_dist:
                best_dist = dist
                best_key = k
        if best_key and best_dist <= max(0.35, cv * 0.35):
            return self.por_cv.get(best_key)
        return None

    def resolve_geom_bucket(self, carcaca: str, pacote_mm: Optional[float]) -> Optional[dict[str, Any]]:
        g = _geom_bucket(carcaca, pacote_mm)
        if g in self.por_geom:
            return self.por_geom[g]
        cn = norm_carcaca(carcaca)
        candidates = [(k, v) for k, v in self.por_geom.items() if k.startswith(cn + "|") or k == cn]
        if not candidates:
            return None
        if pacote_mm and pacote_mm > 0:
            candidates.sort(
                key=lambda kv: abs(
                    (kv[1].get("pacote_mm_medio") or pacote_mm) - pacote_mm  # type: ignore[operator]
                )
            )
        return candidates[0][1]

    def espiras_no_historico_cv(self, cv: float, espiras: float) -> tuple[bool, str]:
        block = self.resolve_cv_bucket(cv)
        if not block:
            return False, ""
        faixa = block.get("faixa_espiras_aceitavel") or {}
        lo = float(faixa.get("min") or 0)
        hi = float(faixa.get("max") or 0)
        if lo <= 0 and hi <= 0:
            stats = block.get("espiras") or {}
            lo = float(stats.get("p10") or stats.get("min") or 0)
            hi = float(stats.get("p90") or stats.get("max") or 0)
        margin = max(3.0, 0.08 * max(espiras, 1))
        if lo > 0 and hi > 0 and (espiras < lo - margin or espiras > hi + margin):
            return False, ""
        n = int(block.get("n_registros") or 0)
        p10 = float((block.get("espiras") or {}).get("p10") or lo)
        p90 = float((block.get("espiras") or {}).get("p90") or hi)
        cv_label = block.get("cv_representativo", cv)
        msg = MSG_CONFORMIDADE_CV_ESPIRAS.format(cv=cv_label, n=n, p10=p10, p90=p90)
        return True, msg

    def j_no_historico(
        self,
        j_a_mm2: Optional[float],
        *,
        cv: Optional[float] = None,
        carcaca: str = "",
        pacote_mm: Optional[float] = None,
    ) -> tuple[bool, str]:
        if j_a_mm2 is None:
            return False, ""
        j = float(j_a_mm2)

        g_block = self.resolve_geom_bucket(carcaca, pacote_mm)
        if g_block:
            faixa = g_block.get("faixa_j_aceitavel") or {}
            lo = float(faixa.get("min") or 0)
            hi = float(faixa.get("max") or 0)
            if lo > 0 and hi > 0 and lo <= j <= hi:
                med = float((g_block.get("densidade_j_a_mm2") or {}).get("mediana") or j)
                geom = _geom_bucket(carcaca, pacote_mm)
                return True, MSG_CONFORMIDADE_J_GEOM.format(geom=geom, med=med)

        if cv and cv > 0:
            c_block = self.resolve_cv_bucket(cv)
            if c_block:
                faixa = c_block.get("faixa_j_aceitavel") or {}
                lo = float(faixa.get("min") or 0)
                hi = float(faixa.get("max") or 0)
                if lo > 0 and hi > 0 and lo <= j <= hi:
                    n = int(c_block.get("n_registros") or 0)
                    return True, MSG_CONFORMIDADE_HISTORICO.format(n=n)

        g = self.global_stats.get("faixa_j_aceitavel") or {}
        lo = float(g.get("min") or 2.0)
        hi = float(g.get("max") or 10.0)
        if lo <= j <= hi:
            n = int(self.global_stats.get("n_registros") or self.total_registros)
            return True, MSG_CONFORMIDADE_HISTORICO.format(n=n)
        return False, ""

    def b_saturacao_tolerada_por_cv(self, cv: float, espiras: float, b_t: float) -> tuple[bool, str]:
        """Se B > 1.5 T mas espiras estão no histórico do CV, não tratar como falha dura."""
        if b_t <= 1.5:
            return False, ""
        ok, msg = self.espiras_no_historico_cv(cv, espiras)
        if ok and b_t < 1.8:
            return True, msg + " Indução B elevada, porém espiras coerentes com o acervo da oficina."
        return False, ""


@lru_cache(maxsize=1)
def get_oficina_knowledge(path: Optional[str] = None) -> OficinaKnowledge:
    p = Path(path) if path else DEFAULT_JSON
    if not p.is_file():
        return OficinaKnowledge({"meta": {}, "por_cv": {}, "por_carcaca_pacote": {}, "global": {}})
    data = json.loads(p.read_text(encoding="utf-8"))
    return OficinaKnowledge(data)


def reload_oficina_knowledge() -> OficinaKnowledge:
    get_oficina_knowledge.cache_clear()
    return get_oficina_knowledge()
