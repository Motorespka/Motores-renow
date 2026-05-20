#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Busca por geometria e validação de cálculo vs acervo OFICIAL indexado."""

from __future__ import annotations

import json
import math
import re
import sqlite3
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = REPO_ROOT / "data" / "oficial_search.sqlite"

_RE_NUM = re.compile(r"\d+(?:[.,]\d+)?")


def parse_mm(raw: str) -> Optional[float]:
    """Converte texto de dimensão para mm (heurística tolerante a OCR)."""
    s = (raw or "").strip().lower().replace(",", ".")
    if not s:
        return None
    m = _RE_NUM.search(s)
    if not m:
        return None
    try:
        v = float(m.group().replace(",", "."))
    except ValueError:
        return None
    if "cm" in s and v < 80:
        v *= 10.0
    # VOGE e placas antigas: "855" costuma ser 85,5 mm
    if v > 250 and "cm" not in s:
        v = v / 10.0
    return round(v, 2)


def parse_passo_nums(raw: str) -> list[float]:
    if not raw:
        return []
    out: list[float] = []
    for m in _RE_NUM.finditer(raw.replace(";", ":").replace("-", " ")):
        try:
            out.append(float(m.group().replace(",", ".")))
        except ValueError:
            continue
    return out


def norm_carcaca(raw: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (raw or "").lower())


def parse_scalar(raw: str) -> Optional[float]:
    """Numero simples (espiras, etc.) sem heuristica de mm."""
    s = (raw or "").strip().replace(",", ".")
    if not s:
        return None
    m = _RE_NUM.search(s)
    if not m:
        return None
    try:
        return float(m.group().replace(",", "."))
    except ValueError:
        return None


def motor_polos_int(raw: Optional[str]) -> Optional[int]:
    """Extrai número de polos de texto de cadastro (2 / 4 / 6 …)."""
    if raw is None or not str(raw).strip():
        return None
    s = str(raw).strip().lower()
    for tok in ("mono", "monof"):
        if tok in s:
            return None
    m = _RE_NUM.search(s.replace(",", "."))
    if not m:
        return None
    try:
        val = int(float(m.group().replace(",", ".")))
    except ValueError:
        return None
    if val not in {2, 4, 6, 8, 10, 12}:
        return None
    return val


def parse_polos_for_calc(raw: Any, *, default: int | None = None) -> int | None:
    """
    Normaliza polos vindos de UI (int, float, '4', '4P', '2 polos').
    Zero ou vazio = não informado (None). Polaridade é opcional no cálculo.
    """
    if raw is None or (isinstance(raw, str) and not str(raw).strip()):
        return default
    if isinstance(raw, bool):
        return default
    if isinstance(raw, (int, float)):
        n = int(raw)
        if n <= 0:
            return None
        return n
    txt = str(raw).strip()
    if txt in {"0", "—", "-"}:
        return None
    p = motor_polos_int(txt)
    if p is not None:
        return p
    v = parse_scalar(txt)
    if v is not None:
        n = int(v)
        return n if n > 0 else None
    return default


def parse_ranhuras_for_calc(raw: Any, *, default: int | None = None) -> int | None:
    """Normaliza número de ranhuras (UI ou texto)."""
    if raw is None or (isinstance(raw, str) and not str(raw).strip()):
        return default
    if isinstance(raw, bool):
        return default
    if isinstance(raw, (int, float)):
        n = int(raw)
        return n if n > 0 else default
    v = parse_scalar(str(raw).strip())
    if v is not None:
        n = int(v)
        return n if n > 0 else default
    return default


def parse_awg_number(raw: str) -> Optional[float]:
    """Extrai número AWG de '23', '2 x 23', '#23'."""
    s = (raw or "").strip().lower()
    if not s:
        return None
    nums = [float(x.replace(",", ".")) for x in _RE_NUM.findall(s)]
    if not nums:
        return None
    return nums[-1]


def passo_overlap(user_nums: list[float], ref_nums: list[float]) -> bool:
    if not user_nums or not ref_nums:
        return False
    umin, umax = min(user_nums), max(user_nums)
    rmin, rmax = min(ref_nums), max(ref_nums)
    return not (umax < rmin - 1.0 or umin > rmax + 1.0)


def passo_canonical(raw: str) -> str:
    """Chave comparável para passo (ex.: '10-12', '10 : 12' -> '10-12')."""
    nums = parse_passo_nums(raw)
    if nums:
        parts: list[str] = []
        for n in nums:
            parts.append(str(int(n)) if abs(n - int(n)) < 1e-6 else str(round(n, 2)))
        return "-".join(parts)
    s = (raw or "").strip().lower()
    s = re.sub(r"[:;\s]+", "-", s)
    return re.sub(r"-+", "-", s).strip("-")


def passo_exact_match(user_passo: str, ref_passo: str) -> bool:
    """Exige o mesmo passo de bobinagem (Lei da Ranhura — filtro duro)."""
    u = passo_canonical(user_passo)
    r = passo_canonical(ref_passo)
    if not u:
        return True
    if not r:
        return False
    return u == r


def awg_to_mm2(awg: float) -> float:
    """Área da seção do fio (mm²) a partir do número AWG."""
    if awg <= 0:
        return 0.0
    return 0.012668 * (92 ** ((36.0 - awg) / 39.0))


def awg_from_mm2(area_mm2: float) -> Optional[float]:
    if area_mm2 <= 0:
        return None
    try:
        awg = 36.0 - (39.0 / math.log(92)) * math.log(area_mm2 / 0.012668)
    except (ValueError, ZeroDivisionError):
        return None
    return round(max(0.0, min(40.0, awg)), 1)


def slot_fill_units(espiras: float, awg: float) -> float:
    """Proxy de enchimento de ranhura: espiras × seção do fio (mm²·espiras)."""
    if espiras <= 0 or awg <= 0:
        return 0.0
    return espiras * awg_to_mm2(awg)


@dataclass
class MotorRow:
    sha: str
    arquivo_rel: str
    melhor_status: str
    carcaca: str
    diametro_mm: Optional[float]
    pacote_mm: Optional[float]
    passo_principal: str
    passo_nums_json: str
    fio_principal: str
    espiras_principal: Optional[float]
    fio_auxiliar: str
    espiras_auxiliar: Optional[float]
    potencia_cv: str
    polos: str
    tipo_motor: str
    ligacao: str = ""
    tipo_bobinagem: str = ""
    tipo_bobinagem_norm: str = ""
    is_file: int = 0

    @property
    def passo_nums(self) -> list[float]:
        try:
            return json.loads(self.passo_nums_json or "[]")
        except json.JSONDecodeError:
            return []


@dataclass
class MatchResult:
    motor: MotorRow
    score: float
    dist_mm: float


@dataclass
class Suggestion:
    matches: list[MatchResult]
    diametro_mm: Optional[float]
    pacote_mm: Optional[float]
    carcaca_mode: str
    passo_label: str
    fio_principal: Optional[float]
    espiras_principal: Optional[float]
    fio_auxiliar: Optional[float]
    espiras_auxiliar: Optional[float]
    n_geom: int


@dataclass
class ValidationReport:
    status: str
    message: str
    details: list[str]


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    path = (db_path or DEFAULT_DB).resolve()
    if not path.is_file():
        raise FileNotFoundError(
            f"Indice nao encontrado: {path}\n"
            "Execute: python scripts/index_for_search.py"
        )
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def load_all_motors(conn: sqlite3.Connection) -> list[MotorRow]:
    cols = {r[1] for r in conn.execute("PRAGMA table_info(motores_oficial)").fetchall()}
    lig_col = ", ligacao" if "ligacao" in cols else ", '' AS ligacao"
    topo_col = ", tipo_bobinagem, tipo_bobinagem_norm" if "tipo_bobinagem" in cols else ", '' AS tipo_bobinagem, '' AS tipo_bobinagem_norm"
    file_col = ", is_file" if "is_file" in cols else ", 0 AS is_file"
    rows = conn.execute(
        f"""
        SELECT sha, arquivo_rel, melhor_status, carcaca,
               diametro_mm, pacote_mm, passo_principal, passo_nums_json,
               fio_principal, espiras_principal, fio_auxiliar, espiras_auxiliar,
               potencia_cv, polos, tipo_motor{lig_col}{topo_col}{file_col}
        FROM motores_oficial
        """
    ).fetchall()
    return [MotorRow(**dict(r)) for r in rows]


def _geo_distance(
    d_user: Optional[float],
    p_user: Optional[float],
    d_ref: Optional[float],
    p_ref: Optional[float],
) -> float:
    parts: list[float] = []
    if d_user is not None and d_ref is not None and d_ref > 0:
        parts.append(abs(d_user - d_ref) / max(d_ref, 1.0))
    if p_user is not None and p_ref is not None and p_ref > 0:
        parts.append(abs(p_user - p_ref) / max(p_ref, 1.0))
    if not parts:
        return 999.0
    return sum(parts) / len(parts)


def find_similar(
    motors: list[MotorRow],
    *,
    diametro_mm: Optional[float],
    pacote_mm: Optional[float],
    carcaca: str,
    passo: str,
    top_k: int = 25,
    max_geo_dist: float = 0.22,
    passo_exact: bool = False,
    tipo_bobinagem: str = "",
    topology_exact: bool = False,
) -> list[MatchResult]:
    from app.topologia_bobinagem import norm_tipo_bobinagem, tipo_exact_match

    car_key = norm_carcaca(carcaca)
    user_passo = parse_passo_nums(passo)
    user_passo_key = passo_canonical(passo)
    user_topo = norm_tipo_bobinagem(tipo_bobinagem)
    scored: list[MatchResult] = []

    for m in motors:
        if m.diametro_mm is None and m.pacote_mm is None:
            continue
        if passo_exact and user_passo_key:
            if not passo_exact_match(passo, m.passo_principal):
                continue
        if topology_exact and user_topo:
            ref_topo = m.tipo_bobinagem_norm or m.tipo_bobinagem
            if not tipo_exact_match(tipo_bobinagem, ref_topo):
                continue
        dist = _geo_distance(diametro_mm, pacote_mm, m.diametro_mm, m.pacote_mm)
        if dist > max_geo_dist and (diametro_mm is not None or pacote_mm is not None):
            continue
        score = 1.0 - min(dist, 1.0)
        if car_key and norm_carcaca(m.carcaca) == car_key:
            score += 0.35
        elif car_key and car_key in norm_carcaca(m.carcaca):
            score += 0.2
        if user_passo and passo_overlap(user_passo, m.passo_nums):
            score += 0.25
        if user_topo:
            ref_topo = norm_tipo_bobinagem(m.tipo_bobinagem_norm or m.tipo_bobinagem)
            if ref_topo == user_topo:
                score += 0.4
        scored.append(MatchResult(motor=m, score=score, dist_mm=dist))

    scored.sort(key=lambda x: (-x.score, x.dist_mm))
    return scored[:top_k]


def _median(nums: list[float]) -> Optional[float]:
    nums = [n for n in nums if n is not None]
    if not nums:
        return None
    return round(statistics.median(nums), 2)


def build_suggestion(matches: list[MatchResult]) -> Suggestion:
    if not matches:
        return Suggestion(
            matches=[],
            diametro_mm=None,
            pacote_mm=None,
            carcaca_mode="",
            passo_label="",
            fio_principal=None,
            espiras_principal=None,
            fio_auxiliar=None,
            espiras_auxiliar=None,
            n_geom=0,
        )

    ms = [m.motor for m in matches]
    n_geom = sum(1 for m in ms if m.diametro_mm is not None and m.pacote_mm is not None)
    carcas = [m.carcaca for m in ms if m.carcaca]
    car_mode = max(set(carcas), key=carcas.count) if carcas else ""
    passos = [m.passo_principal for m in ms if m.passo_principal]
    passo_mode = max(set(passos), key=passos.count) if passos else ""

    return Suggestion(
        matches=matches,
        diametro_mm=_median([m.diametro_mm for m in ms if m.diametro_mm is not None]),
        pacote_mm=_median([m.pacote_mm for m in ms if m.pacote_mm is not None]),
        carcaca_mode=car_mode,
        passo_label=passo_mode,
        fio_principal=_median([parse_awg_number(m.fio_principal) for m in ms]),
        espiras_principal=_median(
            [m.espiras_principal for m in ms if m.espiras_principal is not None]
        ),
        fio_auxiliar=_median([parse_awg_number(m.fio_auxiliar) for m in ms]),
        espiras_auxiliar=_median(
            [m.espiras_auxiliar for m in ms if m.espiras_auxiliar is not None]
        ),
        n_geom=n_geom,
    )


def _within_margin(user: Optional[float], ref: Optional[float], pct: float = 0.15) -> Optional[bool]:
    if user is None or ref is None or ref == 0:
        return None
    return abs(user - ref) <= max(ref * pct, 2.0)


def validate_calculation(
    suggestion: Suggestion,
    *,
    user_fio: str,
    user_espiras: str,
    user_passo: str,
    diametro_mm: Optional[float],
    pacote_mm: Optional[float],
) -> ValidationReport:
    if not suggestion.matches:
        return ValidationReport(
            status="SEM_REFERENCIA",
            message="Nenhum motor OFICIAL com geometria parecida no acervo indexado.",
            details=[],
        )

    details: list[str] = []
    ok = 0
    checks = 0

    uf = parse_awg_number(user_fio)
    ue = parse_scalar(user_espiras)
    up = parse_passo_nums(user_passo)

    if suggestion.fio_principal is not None and uf is not None:
        checks += 1
        w = _within_margin(uf, suggestion.fio_principal, 0.12)
        if w:
            ok += 1
            details.append(f"Fio AWG {uf}: dentro da faixa do acervo (mediana {suggestion.fio_principal}).")
        else:
            details.append(
                f"Fio AWG {uf}: fora da faixa (mediana oficial {suggestion.fio_principal}, tol. ~12%)."
            )

    if suggestion.espiras_principal is not None and ue is not None:
        checks += 1
        w = _within_margin(ue, suggestion.espiras_principal, 0.15)
        if w:
            ok += 1
            details.append(
                f"Espiras {ue:.0f}: coerente com mediana {suggestion.espiras_principal:.0f} do grupo."
            )
        else:
            details.append(
                f"Espiras {ue:.0f}: diverge da mediana {suggestion.espiras_principal:.0f} (>15%)."
            )

    if up and suggestion.passo_label:
        checks += 1
        ref_nums = parse_passo_nums(suggestion.passo_label)
        pool = []
        for m in suggestion.matches:
            pool.extend(m.motor.passo_nums)
        if passo_overlap(up, pool or ref_nums):
            ok += 1
            details.append("Passo: compativel com registros similares do acervo.")
        else:
            details.append(
                f"Passo {user_passo}: pouca sobreposicao com o grupo (moda: {suggestion.passo_label})."
            )

    if diametro_mm and suggestion.diametro_mm:
        checks += 1
        w = _within_margin(diametro_mm, suggestion.diametro_mm, 0.12)
        if w:
            ok += 1
        else:
            details.append(
                f"Diametro estator {diametro_mm} mm vs mediana {suggestion.diametro_mm} mm."
            )

    if pacote_mm and suggestion.pacote_mm:
        checks += 1
        w = _within_margin(pacote_mm, suggestion.pacote_mm, 0.12)
        if w:
            ok += 1
        else:
            details.append(
                f"Comprimento pacote {pacote_mm} mm vs mediana {suggestion.pacote_mm} mm."
            )

    if checks == 0:
        return ValidationReport(
            status="INCOMPLETO",
            message="Preencha fio, espiras ou passo para validar o calculo.",
            details=details,
        )

    ratio = ok / checks
    if ratio >= 0.75:
        status = "APROVADO"
        msg = "Calculo alinhado ao que foi aprovado no acervo oficial (dentro da margem)."
    elif ratio >= 0.45:
        status = "REVISAR"
        msg = "Calculo parcialmente alinhado — revisar itens em amarelo."
    else:
        status = "ATENCAO"
        msg = "Calculo diverge do padrao dos motores oficiais similares."

    return ValidationReport(status=status, message=msg, details=details)
