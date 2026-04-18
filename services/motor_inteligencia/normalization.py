"""
Normalização numérica e textual para a camada de inteligência técnica.

Todas as inferências a partir de texto ruidoso ou formatos ambíguos são tratadas
como **heurísticas**: devolvemos notas e flags ``needs_review`` em vez de forçar
valores “certos” sem evidência.
"""

from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

# Constantes de conversão (IEC usuais em ferramentas de campo; heurística de unidade)
_CV_TO_KW = 0.735499
_HP_TO_KW = 0.7457


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(v).strip() for v in value if str(v).strip())
    return str(value).strip()


def _strip_noise(s: str) -> str:
    s = s.replace("\u00a0", " ")
    s = re.sub(r"\[[^\]]*\]", " ", s)
    s = re.sub(r"[^\d,.\-/a-zA-Z\u00b0]", " ", s, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", s).strip()


def _parse_float_token(token: str) -> Optional[float]:
    """
    Converte token numérico com vírgula ou ponto decimal.
    Não interpreta separador de milhares aqui (evita ambiguidade 1.234).
    """
    t = token.strip().replace(" ", "")
    if not t:
        return None
    t = t.replace(",", ".")
    if t.count(".") > 1:
        return None
    try:
        return float(t)
    except ValueError:
        return None


def parse_rpm(value: Any) -> Tuple[Optional[float], List[str], bool]:
    """
    Extrai RPM nominal. Heurística: ``3.450`` / ``1.750`` como milhares (pt-BR) quando cai na faixa típica.
    """
    notes: List[str] = []
    raw = _to_text(value)
    if not raw:
        return None, [], False
    s = _strip_noise(raw.lower().replace("rpm", " ").replace("r.p.m", " "))
    s_num = s.replace(",", ".")
    m = re.search(r"\b(\d{1,2})\.(\d{3})\b", s_num)
    if m:
        alt = int(m.group(1)) * 1000 + int(m.group(2))
        if 500 <= alt <= 6000:
            notes.append(
                "Heurística RPM: notação x.xxx tratada como milhares; confirmar na placa se ambíguo."
            )
            return float(alt), notes, True
    m2 = re.search(r"(\d+(?:\.\d+)?)", s_num)
    if not m2:
        return None, notes + ["RPM: nenhum número reconhecido."], False
    try:
        v = float(m2.group(1))
        if v <= 0:
            return None, notes + ["RPM: valor não positivo."], False
        if v < 120:
            notes.append("RPM muito baixo; possível OCR parcial — revisão recomendada.")
        return v, notes, False
    except ValueError:
        return None, notes + ["RPM: parse falhou."], False


def parse_frequency_hz(value: Any) -> Tuple[Optional[float], List[str]]:
    notes: List[str] = []
    raw = _to_text(value)
    if not raw:
        return None, notes
    s = _strip_noise(raw.lower())
    m = re.search(r"(\d{2})\s*hz", s)
    if m:
        hz = float(m.group(1))
        if hz in (50, 60):
            return hz, notes
    nums = re.findall(r"\d+", s)
    if nums:
        for n in nums:
            if n in ("50", "60"):
                return float(n), notes
    return None, notes + ["Frequência: não foi possível extrair 50/60 Hz com confiança."]


def parse_poles(value: Any) -> Tuple[Optional[int], List[str]]:
    notes: List[str] = []
    raw = _to_text(value)
    if not raw:
        return None, notes
    s = raw.upper().replace("POLOS", "P").replace(" ", "")
    m = re.search(r"(\d+)\s*P\b", s)
    if m:
        p = int(m.group(1))
        if p in (2, 4, 6, 8, 10, 12):
            return p, notes
        notes.append("Polos: valor fora do conjunto comum 2–12; verificar placa.")
        return p, notes
    m2 = re.search(r"(\d+)", s)
    if m2:
        p = int(m2.group(1))
        if p in (2, 4, 6, 8, 10, 12):
            return p, notes
        if p % 2 == 0 and 2 <= p <= 24:
            notes.append("Polos: número par não usual — heurística fraca.")
            return p, notes
    return None, notes + ["Polos: não identificados."]


def parse_power_kw(potencia: Any, cv_field: Any) -> Tuple[Optional[float], List[str], str]:
    """
    Converte potência para kW. Heurística de unidade por sufixo (cv, hp, kw).
    """
    notes: List[str] = []
    combined = _to_text(potencia) or _to_text(cv_field)
    if not combined:
        return None, notes, ""
    s = _strip_noise(combined.lower())
    m = re.search(
        r"(\d+(?:[.,]\d+)?)\s*(cv|hp|kw|kva|kvw)?",
        s,
        flags=re.IGNORECASE,
    )
    if not m:
        m = re.search(r"(\d+(?:[.,]\d+)?)(cv|hp|kw)\b", s, flags=re.IGNORECASE)
    if not m:
        return None, notes + ["Potência: formato não reconhecido."], combined
    val = _parse_float_token(m.group(1).replace(",", "."))
    if val is None or val <= 0:
        return None, notes + ["Potência: valor inválido."], combined
    unit = (m.group(2) or "").lower()
    if unit in ("kw",):
        return val, notes, combined
    if unit in ("cv", "hp", ""):
        # Sem unidade: heurística típica Brasil = CV quando valor “pequeno” de potência em cv
        factor = _CV_TO_KW if unit != "hp" else _HP_TO_KW
        if not unit:
            notes.append(
                "Heurística potência: unidade ausente; assumido CV (Brasil) para converter a kW — "
                "confirmar na placa."
            )
        return val * factor, notes, combined
    if unit in ("kva", "kvw"):
        notes.append(
            "Potência em kVA/kVW: conversão a kW ativa não é única sem fator de potência — "
            "não convertido a kW ativo; marcar revisão."
        )
        return None, notes, combined
    return val * _CV_TO_KW, notes, combined


def parse_current_a(value: Any) -> Tuple[Optional[float], List[str]]:
    notes: List[str] = []
    raw = _to_text(value)
    if not raw:
        return None, notes
    s = _strip_noise(raw.lower().replace("a", " ").replace("amp", " "))
    m = re.search(r"(\d+(?:[.,]\d+)?)", s)
    if not m:
        return None, notes + ["Corrente: número não encontrado."]
    v = _parse_float_token(m.group(1))
    if v is None or v <= 0:
        return None, notes + ["Corrente: valor inválido."]
    return v, notes


def parse_voltage_list(value: Any) -> Tuple[List[float], List[str]]:
    """
    Extrai lista de tensões em V (nominal). Aceita 220/380, 220-380, listas.
    Heurística: primeira tensão pode ser usada como “primária” para cálculos mono/tri simplificados.
    """
    notes: List[str] = []
    out: List[float] = []
    if value is None:
        return out, notes
    if isinstance(value, list):
        chunks = [_to_text(v) for v in value if _to_text(v)]
    else:
        chunks = re.split(r"[/|;,\s]+", _to_text(value))
    for ch in chunks:
        if not ch:
            continue
        m = re.findall(r"\d{2,3}(?:[.,]\d+)?", ch.replace(",", "."))
        for g in m:
            v = _parse_float_token(g)
            if v is not None and 50 <= v <= 1000:
                out.append(v)
    if not out:
        return [], notes + ["Tensão: nenhum valor numérico na faixa 50–1000 V."]
    if len(out) >= 2:
        notes.append(
            "Heurística tensão: múltiplas tensões podem indicar ligação Y/D; "
            "cálculos usam valor primário (maior típico) como tensão de referência."
        )
    return sorted(set(round(x, 2) for x in out)), notes


def parse_power_factor(value: Any) -> Tuple[Optional[float], List[str]]:
    raw = _to_text(value)
    if not raw:
        return None, []
    v = _parse_float_token(raw.replace(",", "."))
    if v is None:
        return None, ["Fator de potência: não interpretado."]
    if not (0.05 < v <= 1.0):
        return None, ["Fator de potência: fora do intervalo plausível (0,05–1]."]
    return v, []


def parse_efficiency(value: Any) -> Tuple[Optional[float], List[str]]:
    raw = _to_text(value)
    if not raw:
        return None, []
    v = _parse_float_token(raw.replace(",", "."))
    if v is None:
        return None, []
    if v > 1.5:  # provavelmente em %
        v = v / 100.0
    if not (0.2 <= v <= 1.0):
        return None, ["Rendimento: fora do intervalo plausível."]
    return v, []


def infer_phases(raw: Dict[str, Any], motor: Dict[str, Any]) -> Tuple[str, List[str]]:
    """
    Retorna ``mono`` | ``tri`` | ``unknown`` com notas heurísticas.
    Não adivinha fases só pela tensão (evita viés perigoso).
    """
    notes: List[str] = []
    fases = _to_text(motor.get("fases") or raw.get("fases")).lower()
    tipo = _to_text(motor.get("tipo_motor") or raw.get("tipo_motor")).lower()
    if "trif" in fases or "trif" in tipo or "3f" in tipo:
        return "tri", notes
    if "monof" in fases or "mono" in tipo or "1f" in tipo:
        return "mono", notes
    if "mono" in fases and "tri" not in fases:
        return "mono", notes
    notes.append(
        "Heurística fases: não determinado a partir de fases/tipo_motor — "
        "cálculos elétricos que dependem de mono/tri podem ficar indisponíveis."
    )
    return "unknown", notes


def _motor_block(raw: Dict[str, Any]) -> Dict[str, Any]:
    if isinstance(raw.get("motor"), dict):
        return raw["motor"]
    return {}


def _pick_row_scalar(raw: Dict[str, Any], *keys: str) -> Any:
    for k in keys:
        if k in raw and _to_text(raw.get(k)):
            return raw.get(k)
    return ""


def normalize_motor_inteligencia_input(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Constrói dicionário normalizado para cálculo/validação a partir de vários formatos de entrada.

    Não altera ``raw``; não persiste dados.
    """
    motor = _motor_block(raw)
    parse_notes: List[str] = []
    needs_review = False

    marca = _to_text(motor.get("marca") or raw.get("marca"))
    tipo_motor = _to_text(motor.get("tipo_motor") or raw.get("tipo_motor"))

    power_kw, p_notes, power_raw = parse_power_kw(motor.get("potencia"), motor.get("cv"))
    parse_notes.extend(p_notes)

    rpm, rpm_notes, rpm_ambiguous = parse_rpm(motor.get("rpm") or raw.get("rpm_nominal") or raw.get("rpm"))
    parse_notes.extend(rpm_notes)
    needs_review = needs_review or rpm_ambiguous

    freq, f_notes = parse_frequency_hz(motor.get("frequencia") or raw.get("frequencia_hz"))
    parse_notes.extend(f_notes)

    poles, pol_notes = parse_poles(motor.get("polos") or raw.get("polos"))
    parse_notes.extend(pol_notes)

    tensions, t_notes = parse_voltage_list(motor.get("tensao") or raw.get("tensao_v"))
    parse_notes.extend(t_notes)

    cur_raw = motor.get("corrente") or raw.get("corrente_nominal_a") or raw.get("corrente")
    if isinstance(cur_raw, list):
        cur_raw = cur_raw[0] if cur_raw else ""
    current_a, c_notes = parse_current_a(cur_raw)
    parse_notes.extend(c_notes)

    fp, fp_notes = parse_power_factor(
        motor.get("fator_potencia") or motor.get("fp") or raw.get("fator_potencia")
    )
    parse_notes.extend(fp_notes)

    eta, eta_notes = parse_efficiency(motor.get("rendimento") or raw.get("rendimento"))
    parse_notes.extend(eta_notes)

    phases, ph_notes = infer_phases(raw, motor)
    parse_notes.extend(ph_notes)

    # Mecânica / esquema (texto livre para futuro)
    mecanica = raw.get("mecanica") if isinstance(raw.get("mecanica"), dict) else {}
    esquema = raw.get("esquema") if isinstance(raw.get("esquema"), dict) else {}
    carcaca = _to_text(motor.get("carcaca") or mecanica.get("carcaca"))
    diametro_mm = _to_text(mecanica.get("diametro_mm") or raw.get("diametro_mm"))
    pacote_mm = _to_text(mecanica.get("pacote_mm") or raw.get("pacote_mm"))
    ranhuras = _to_text(esquema.get("ranhuras") or raw.get("ranhuras"))

    aux = raw.get("bobinagem_auxiliar") if isinstance(raw.get("bobinagem_auxiliar"), dict) else {}
    capacitor = _to_text(aux.get("capacitor"))

    texto_ocr = _to_text(raw.get("texto_ocr"))
    texto_norm = _to_text(raw.get("texto_normalizado"))

    oficina = raw.get("oficina") if isinstance(raw.get("oficina"), dict) else {}
    parser_tecnico = oficina.get("parser_tecnico") if isinstance(oficina.get("parser_tecnico"), dict) else {}
    ocr_ambiguous = bool(parser_tecnico.get("ambiguous"))
    ocr_needs = bool(parser_tecnico.get("needs_review"))
    if ocr_ambiguous or ocr_needs:
        needs_review = True
        parse_notes.append(
            "Metadados OCR (oficina.parser_tecnico) indicam ambiguidade ou necessidade de revisão humana."
        )

    tension_primary: Optional[float] = tensions[-1] if tensions else None  # heurística: maior valor comum em Y/D
    if len(tensions) >= 2:
        parse_notes.append(
            "Heurística tensão primária: usado maior valor da lista para Pin simplificado (ligações múltiplas)."
        )

    insufficient_for: List[str] = []
    if power_kw is None:
        insufficient_for.append("consistência P×I×V (falta potência em kW)")
    if rpm is None:
        insufficient_for.append("escorregamento e torque (falta RPM)")
    if freq is None:
        insufficient_for.append("rotação síncrona (falta frequência)")
    if poles is None:
        insufficient_for.append("rotação síncrona (falta polos)")
    if tension_primary is None:
        insufficient_for.append("potência elétrica de entrada (falta tensão)")
    if current_a is None:
        insufficient_for.append("potência elétrica de entrada (falta corrente)")
    if phases == "unknown":
        insufficient_for.append("Pin mono vs tri (falta identificação de fases)")
    if fp is None:
        insufficient_for.append("Pin kW exato (falta fator de potência)")
    if eta is None:
        insufficient_for.append("Pout e rendimento cruzado (falta rendimento)")

    return {
        "marca": marca,
        "tipo_motor": tipo_motor,
        "power_kw": power_kw,
        "power_raw": power_raw,
        "rpm_nominal": rpm,
        "frequency_hz": freq,
        "poles": poles,
        "tensions_v": tensions,
        "tension_v_primary": tension_primary,
        "current_a": current_a,
        "power_factor": fp,
        "efficiency": eta,
        "phases": phases,
        "carcaca": carcaca,
        "capacitor": capacitor,
        "diametro_mm": diametro_mm,
        "pacote_mm": pacote_mm,
        "ranhuras": ranhuras,
        "texto_ocr_len": len(texto_ocr),
        "texto_normalizado_len": len(texto_norm),
        "parse_notes": parse_notes,
        "needs_review": needs_review,
        "insufficient_for": insufficient_for,
        "confidence_base": _confidence_score(
            power_kw, rpm, freq, poles, tension_primary, current_a, phases, fp, eta
        ),
    }


def _confidence_score(
    power_kw: Optional[float],
    rpm: Optional[float],
    freq: Optional[float],
    poles: Optional[int],
    v: Optional[float],
    i: Optional[float],
    phases: str,
    fp: Optional[float],
    eta: Optional[float],
) -> float:
    score = 0.0
    if power_kw:
        score += 0.15
    if rpm:
        score += 0.15
    if freq:
        score += 0.1
    if poles:
        score += 0.1
    if v:
        score += 0.15
    if i:
        score += 0.15
    if phases != "unknown":
        score += 0.1
    if fp:
        score += 0.05
    if eta:
        score += 0.05
    return round(min(score, 1.0), 3)
