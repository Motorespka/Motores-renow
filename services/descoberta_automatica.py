from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from statistics import median
from typing import Any, Dict, Iterable, List, Optional, Tuple


MotorRow = Dict[str, Any]


@dataclass
class Descoberta:
    padrao: str
    calculo_inferido: str
    nivel_confianca: float
    amostras: int
    detalhes: Dict[str, Any]


def _normalize_key(key: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(key).strip().lower()).strip("_")


def _build_index(row: MotorRow) -> Dict[str, Any]:
    idx: Dict[str, Any] = {}
    for k, v in row.items():
        nk = _normalize_key(k)
        if nk and nk not in idx and v not in (None, ""):
            idx[nk] = v
    return idx


def _pick(row: MotorRow, aliases: Iterable[str]) -> Any:
    idx = row.get("_norm_index")
    if not isinstance(idx, dict):
        idx = _build_index(row)
    for alias in aliases:
        if alias in row and row.get(alias) not in (None, ""):
            return row.get(alias)
        val = idx.get(_normalize_key(alias))
        if val not in (None, ""):
            return val
    return None


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip().lower()
    if not text:
        return None

    text = text.replace("cv", "").replace("hp", "").replace("kw", "")
    text = text.replace("v", "").replace("a", "")
    text = text.replace(",", ".")

    m = re.search(r"-?\d+(?:\.\d+)?", text)
    if not m:
        return None
    try:
        return float(m.group(0))
    except ValueError:
        return None


def _enriched_rows(motores: List[MotorRow]) -> List[MotorRow]:
    enriched: List[MotorRow] = []
    for row in motores:
        row2 = dict(row)
        row2["_norm_index"] = _build_index(row2)
        enriched.append(row2)
    return enriched


def _discover_polos_rpm(rows: List[MotorRow]) -> List[Descoberta]:
    aliases_polos = ["polos", "numero_polos", "poles", "n_polos"]
    aliases_rpm = ["rpm_nominal", "rpm", "rotacao", "rotacao_nominal"]

    agg: Dict[int, List[float]] = {}
    for r in rows:
        polos = _to_float(_pick(r, aliases_polos))
        rpm = _to_float(_pick(r, aliases_rpm))
        if polos is None or rpm is None:
            continue
        p = int(round(polos))
        agg.setdefault(p, []).append(rpm)

    out: List[Descoberta] = []
    for polos, rpms in agg.items():
        if len(rpms) < 3:
            continue
        rpm_med = median(rpms)
        tol = max(30.0, rpm_med * 0.08)
        dominant = [r for r in rpms if abs(r - rpm_med) <= tol]
        conf = len(dominant) / len(rpms)
        if conf < 0.6:
            continue
        out.append(
            Descoberta(
                padrao="relacao_polos_rpm",
                calculo_inferido=f"rpm ≈ {round(rpm_med, 1)} quando polos = {polos}",
                nivel_confianca=round(conf, 3),
                amostras=len(rpms),
                detalhes={"polos": polos, "rpm_mediana": rpm_med, "rpm_tolerancia": tol},
            )
        )
    return out


def _discover_tensao_corrente(rows: List[MotorRow]) -> List[Descoberta]:
    aliases_tensao = ["tensao_v", "tensao", "voltagem", "voltage", "v"]
    aliases_corrente = ["corrente_nominal_a", "corrente", "amperagem", "corrente_nominal"]

    pairs: List[Tuple[float, float]] = []
    for r in rows:
        t = _to_float(_pick(r, aliases_tensao))
        c = _to_float(_pick(r, aliases_corrente))
        if t is None or c is None or t <= 0 or c <= 0:
            continue
        pairs.append((t, c))

    if len(pairs) < 6:
        return []

    # Modelo recorrente simplificado: I ~= k / V (potência aparente aproximadamente estável).
    k_values = [v * i for v, i in pairs]
    k_med = median(k_values)
    errors = [abs(i - (k_med / v)) / i for v, i in pairs]
    mape = sum(errors) / len(errors)
    conf = max(0.0, 1.0 - mape)
    if conf < 0.55:
        return []

    return [
        Descoberta(
            padrao="relacao_tensao_corrente",
            calculo_inferido=f"corrente ≈ {round(k_med, 3)} / tensao",
            nivel_confianca=round(conf, 3),
            amostras=len(pairs),
            detalhes={"k_medio_vi": round(k_med, 6), "erro_medio_relativo": round(mape, 6)},
        )
    ]


def _discover_potencia_bitola(rows: List[MotorRow]) -> List[Descoberta]:
    aliases_pot = ["potencia_hp_cv", "potencia_kw", "potencia", "potencia_cv", "potencia_hp", "cv", "cavalaria"]
    aliases_bitola = ["bitola_fio", "bitola", "fio", "fio_original", "wire_gauge", "secao_mm2", "secao_fio"]

    pts: List[Tuple[float, float]] = []
    for r in rows:
        p = _to_float(_pick(r, aliases_pot))
        b = _to_float(_pick(r, aliases_bitola))
        if p is None or b is None or p <= 0 or b <= 0:
            continue
        pts.append((p, b))

    if len(pts) < 5:
        return []

    n = len(pts)
    sx = sum(p for p, _ in pts)
    sy = sum(b for _, b in pts)
    sxx = sum(p * p for p, _ in pts)
    sxy = sum(p * b for p, b in pts)
    den = (n * sxx) - (sx * sx)
    if den == 0:
        return []

    a = ((n * sxy) - (sx * sy)) / den
    c = (sy - a * sx) / n

    y_bar = sy / n
    ss_tot = sum((b - y_bar) ** 2 for _, b in pts)
    ss_res = sum((b - (a * p + c)) ** 2 for p, b in pts)
    if ss_tot == 0:
        return []
    r2 = max(0.0, min(1.0, 1 - (ss_res / ss_tot)))

    if r2 < 0.45:
        return []

    return [
        Descoberta(
            padrao="relacao_potencia_bitola",
            calculo_inferido=f"bitola ≈ ({a:.4f} * potencia) + {c:.4f}",
            nivel_confianca=round(r2, 3),
            amostras=n,
            detalhes={"coef_angular": round(a, 6), "coef_linear": round(c, 6), "r2": round(r2, 6)},
        )
    ]


def _discover_enrolamento_ranhuras(rows: List[MotorRow]) -> List[Descoberta]:
    aliases_enrol = ["tipo_enrolamento", "enrolamento", "winding_type", "fases", "fase"]
    aliases_ranh = ["numero_ranhuras", "ranhuras", "slots", "n_ranhuras"]

    agg: Dict[str, List[int]] = {}
    for r in rows:
        e = _pick(r, aliases_enrol)
        nr = _to_float(_pick(r, aliases_ranh))
        if e in (None, "") or nr is None:
            continue
        key = str(e).strip().lower()
        agg.setdefault(key, []).append(int(round(nr)))

    out: List[Descoberta] = []
    for enrol, ranhs in agg.items():
        if len(ranhs) < 3:
            continue
        moda = max(set(ranhs), key=ranhs.count)
        freq = ranhs.count(moda)
        conf = freq / len(ranhs)
        if conf < 0.6:
            continue
        out.append(
            Descoberta(
                padrao="relacao_enrolamento_ranhuras",
                calculo_inferido=f"ranhuras mais comum = {moda} para enrolamento '{enrol}'",
                nivel_confianca=round(conf, 3),
                amostras=len(ranhs),
                detalhes={"enrolamento": enrol, "ranhuras_moda": moda, "frequencia": freq},
            )
        )
    return out



def _is_missing_descobertas_table_error(exc: Exception) -> bool:
    txt = str(exc).lower()
    return "pgrst205" in txt or "could not find the table 'public.descobertas_ia'" in txt


def _insert_descoberta(supabase: Any, descoberta: Descoberta) -> None:
    payload = {
        "padrao": descoberta.padrao,
        "calculo_inferido": descoberta.calculo_inferido,
        "nivel_confianca": descoberta.nivel_confianca,
        "amostras": descoberta.amostras,
        "detalhes": descoberta.detalhes,
        "gerado_em": datetime.now(timezone.utc).isoformat(),
    }
    supabase.table("descobertas_ia").insert(payload).execute()


def executar_descoberta_automatica(supabase: Any) -> Dict[str, Any]:
    """
    Analisa dados da tabela `motores` e grava padrões recorrentes em `descobertas_ia`.

    Regras de descoberta implementadas:
      - relação polos x rpm
      - relação tensão x corrente
      - potência x bitola de fio
      - tipo de enrolamento x número de ranhuras

    Este módulo NÃO altera registros da tabela `motores`.
    """
    motores = (supabase.table("motores").select("*").execute().data) or []
    rows = _enriched_rows(motores)

    descobertas: List[Descoberta] = []
    descobertas.extend(_discover_polos_rpm(rows))
    descobertas.extend(_discover_tensao_corrente(rows))
    descobertas.extend(_discover_potencia_bitola(rows))
    descobertas.extend(_discover_enrolamento_ranhuras(rows))

    persistidas = 0
    falhas_persistencia = []
    tabela_descobertas_ausente = False

    for d in descobertas:
        try:
            _insert_descoberta(supabase, d)
            persistidas += 1
        except Exception as exc:
            if _is_missing_descobertas_table_error(exc):
                tabela_descobertas_ausente = True
            falhas_persistencia.append(str(exc))

    return {
        "total_motores_lidos": len(rows),
        "total_descobertas": len(descobertas),
        "total_persistidas": persistidas,
        "tabela_descobertas_ausente": tabela_descobertas_ausente,
        "falhas_persistencia": falhas_persistencia[:3],
        "descobertas": [
            {
                "padrao": d.padrao,
                "calculo_inferido": d.calculo_inferido,
                "nivel_confianca": d.nivel_confianca,
                "amostras": d.amostras,
            }
            for d in descobertas
        ],
    }
