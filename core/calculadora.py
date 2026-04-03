"""
Ferramentas de engenharia para bobinagem de motores de indução (uso em oficina).

Heurísticas conservadoras — não substituem norma IEC/NBR nem catálogo WEG;
servem para alertar inconsistências óbvias e sugerir paralelos de fio.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from itertools import combinations_with_replacement
from typing import Any, Dict, List, Optional, Sequence, Tuple

# Tabela AWG (sólido) → mm² aproximado (IEC/NEMA comuns em catálogos)
_AWG_MM2: Dict[int, float] = {
    8: 8.37,
    9: 6.63,
    10: 5.26,
    11: 4.17,
    12: 3.31,
    13: 2.63,
    14: 2.08,
    15: 1.65,
    16: 1.31,
    17: 1.04,
    18: 0.823,
    19: 0.653,
    20: 0.518,
    21: 0.411,
    22: 0.326,
    23: 0.258,
    24: 0.205,
    25: 0.162,
    26: 0.128,
    27: 0.102,
    28: 0.0804,
    29: 0.0647,
    30: 0.0507,
    31: 0.0405,
    32: 0.0320,
    33: 0.0255,
    34: 0.0201,
    35: 0.0160,
    36: 0.0127,
}

# Estoque típico de oficina (mm²) — bitolas comuns para motores
ESTOQUE_PADRAO_MM2: Tuple[float, ...] = (
    0.5,
    0.75,
    1.0,
    1.5,
    2.5,
    4.0,
    6.0,
    10.0,
    16.0,
    25.0,
    35.0,
)


def _norm_txt(s: str) -> str:
    """Normaliza strings para busca e comparação."""
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def mm2_de_awg(awg: int) -> Optional[float]:
    """Converte número AWG para seção em mm²."""
    return _AWG_MM2.get(int(awg))


def mm2_por_diametro_mm(d_mm: float) -> float:
    """Calcula a área (mm²) a partir do diâmetro (mm)."""
    r = d_mm / 2.0
    return math.pi * r * r


def extrair_mm2_de_texto(texto: str) -> Optional[float]:
    """
    Interpreta entradas como '1,5 mm2', 'AWG18', '2x1,5'.
    Retorna o valor da bitola unitária em mm².
    """
    t = _norm_txt(texto)
    if not t:
        return None

    # Tenta encontrar padrão AWG
    m = re.search(r"awg\s*(\d{1,2})", t)
    if not m:
        m = re.search(r"(\d{1,2})\s*awg", t)
    if m:
        awg = int(m.group(1))
        return mm2_de_awg(awg)

    # Tenta encontrar números (mm²)
    nums: List[float] = []
    for part in re.findall(r"(\d+[.,]\d+|\d+)", t.replace("²", "")):
        try:
            nums.append(float(part.replace(",", ".")))
        except ValueError:
            continue
    if not nums:
        return None

    # Heurística: se houver indicação de mm, pegar o valor plausível
    if "mm" in t or "mm2" in t or "mm²" in t:
        for n in sorted(nums, reverse=True):
            if 0.05 <= n <= 300:
                return n

    # Caso '2x1,5' -> retornar a bitola individual (1,5)
    plausible = [n for n in nums if 0.05 <= n <= 300]
    if plausible:
        return min(plausible)

    return None


def _melhor_combinacao_paralela(
    alvo_mm2: float,
    estoque: Sequence[float],
    n_fios: int,
) -> Optional[Tuple[Tuple[float, ...], float]]:
    """Encontra a melhor combinação de N fios para atingir a área alvo."""
    estoque_u = sorted({float(x) for x in estoque if x > 0})
    if not estoque_u or n_fios < 2:
        return None

    best: Optional[Tuple[float, Tuple[float, ...]]] = None
    for combo in combinations_with_replacement(estoque_u, n_fios):
        area = sum(combo)
        if area + 1e-9 < alvo_mm2:
            continue
        excesso = area - alvo_mm2
        if best is None or excesso < best[0] - 1e-9:
            best = (excesso, combo)
    
    if best is None:
        return None
    excesso, combo = best
    return combo, sum(combo)


def sugerir_equivalentes_paralelos(
    fio_texto: str,
    estoque_mm2: Sequence[float] = ESTOQUE_PADRAO_MM2,
) -> List[str]:
    """Sugere 2 ou 3 fios em paralelo para substituir uma bitola indisponível."""
    alvo = extrair_mm2_de_texto(fio_texto)
    if alvo is None or alvo <= 0:
        return []

    # Se a bitola já existe no estoque (tolerância de 2%), não sugerir
    for e in estoque_mm2:
        if abs(e - alvo) / alvo <= 0.02:
            return []

    out: List[str] = []
    for n in (2, 3):
        res = _melhor_combinacao_paralela(alvo, estoque_mm2, n)
        if not res:
            continue
        combo, area = res
        bits = " + ".join(f"{b:g} mm²" for b in combo)
        exc = (area - alvo) / alvo * 100.0
        out.append(
            f"Paralelo de {n} fios: {bits} → Σ ≈ {area:.3f} mm² "
            f"(+{exc:.1f}% vs alvo {alvo:.3f} mm²)"
        )
    return out


def _parse_potencia_cv_kw(texto: str) -> Optional[Tuple[str, float]]:
    """Identifica se a potência está em CV ou kW."""
    t = _norm_txt(texto)
    if not t:
        return None

    m = re.search(r"(\d+[.,]?\d*)\s*(cv|hp)\b", t)
    if m:
        return "cv", float(m.group(1).replace(",", "."))

    m = re.search(r"(\d+[.,]?\d*)\s*(kw|kilowatt|k w)\b", t)
    if m:
        return "kw", float(m.group(1).replace(",", "."))

    m = re.search(r"^(\d+[.,]?\d*)\s*$", t)
    if m:
        return "cv", float(m.group(1).replace(",", "."))

    return None


def _potencia_w(cv_kw: str, valor: float) -> float:
    """Converte potência para Watts."""
    if cv_kw == "cv":
        return valor * 736.0
    return valor * 1000.0


def _corrente_nominal_estimada_3f(
    p_w: float,
    tensao_v: float = 380.0,
    fp: float = 0.85,
    rend: float = 0.88,
) -> float:
    """Estimativa de corrente para motores trifásicos."""
    if tensao_v <= 0 or fp <= 0:
        return 0.0
    p_el = p_w / max(rend, 0.5)
    return p_el / (math.sqrt(3.0) * tensao_v * fp)


def _primeiro_inteiro_plausivel_espiras(texto: str) -> Optional[int]:
    """Extrai número de espiras do texto."""
    t = _norm_txt(texto)
    if not t:
        return None
    nums = [int(float(x.replace(",", "."))) for x in re.findall(r"\d+", t)]
    plausible = [n for n in nums if 1 <= n <= 5000]
    return min(plausible) if plausible else None


def extrair_tensao_linha_v(texto: str) -> float:
    """Extrai a tensão do motor (ex: 380V)."""
    t = (texto or "").strip()
    if not t:
        return 380.0
    m = re.search(r"(\d{3})\s*/\s*(\d{3})", t.replace(" ", ""))
    vals: List[float] = []
    if m:
        vals.extend([float(m.group(1)), float(m.group(2))])
    for x in re.findall(r"\b(\d{2,3})\b", t):
        v = float(x)
        if 110 <= v <= 690:
            vals.append(v)
    if not vals:
        return 380.0
    return max(vals)


def alertas_validacao_projeto(motor: Dict[str, Any]) -> List[str]:
    """
    Realiza validações técnicas para evitar erros de projeto (ex: fio fino demais).
    """
    alertas: List[str] = []

    pk = _parse_potencia_cv_kw(str(motor.get("potencia") or ""))
    if not pk:
        return alertas

    kind, val = pk
    p_w = _potencia_w(kind, val)
    tensao = extrair_tensao_linha_v(str(motor.get("tensao") or ""))
    in_a = _corrente_nominal_estimada_3f(p_w, tensao_v=tensao)

    fio = str(motor.get("fio_principal") or motor.get("fio_princ") or "")
    mm2 = extrair_mm2_de_texto(fio)

    if mm2 and mm2 > 0 and in_a > 0:
        j = in_a / mm2  # Densidade de corrente A/mm²
        if j > 6.0:
            alertas.append(
                f"⚠️ Densidade de corrente muito alta (≈ {j:.2f} A/mm²). "
                "Risco de queima. Verifique a bitola principal."
            )
        elif j > 4.5:
            alertas.append(
                f"⚠️ Densidade de corrente elevada (≈ {j:.2f} A/mm²). "
                "Verifique o regime de trabalho."
            )
        elif j < 1.2 and val >= 5:
            alertas.append(
                f"ℹ️ Bitola parece superdimensionada (densidade ≈ {j:.2f} A/mm²)."
            )

    esp = _primeiro_inteiro_plausivel_espiras(str(motor.get("espira_principal") or motor.get("espiras_princ") or ""))
    if esp is not None and val >= 10 and esp <= 8:
        alertas.append("⚠️ Poucas espiras para um motor de alta potência. Verifique os dados.")

    return alertas


@dataclass
class AnaliseFio:
    alvo_mm2: Optional[float]
    sugestoes_paralelo: List[str]
    alertas: List[str]


def analisar_fio_para_cadastro(fio_texto: str) -> AnaliseFio:
    """Interface para facilitar o uso na tela de cadastro."""
    alvo = extrair_mm2_de_texto(fio_texto)
    sug = sugerir_equivalentes_paralelos(fio_texto) if fio_texto.strip() else []
    return AnaliseFio(alvo_mm2=alvo, sugestoes_paralelo=sug, alertas=[])
