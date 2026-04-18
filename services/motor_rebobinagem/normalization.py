"""
Normalização de dados de oficina / rebobinagem (passo, espiras, fio, ranhuras, dimensões).

Tudo é heurístico: devolve notas, confiança e ``needs_review`` em vez de forçar interpretação única.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join(str(v).strip() for v in value if str(v).strip())
    return str(value).strip()


def _listish(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x).strip() for x in value if str(x).strip()]
    s = _to_text(value)
    if not s:
        return []
    out: List[str] = []
    for part in re.split(r"[,;\n]+", s):
        for sub in re.split(r"\s+", part.strip()):
            if sub:
                out.append(sub)
    return out


def _split_passo_tokens(s: str) -> List[str]:
    """Passo: aceita :, -, espaços e mistura OCR."""
    s = re.sub(r"\s+", " ", s.strip())
    if not s:
        return []
    for sep in (":", "-", "/", "|"):
        if sep in s:
            return [p.strip() for p in s.split(sep) if p.strip()]
    return [p for p in s.split(" ") if p]


def parse_passo_field(value: Any) -> Dict[str, Any]:
    """
    Normaliza lista de passos (por bobina / etapa) a partir de texto ou lista.
    """
    notes: List[str] = []
    tokens: List[str] = []
    if isinstance(value, list):
        for it in value:
            tokens.extend(_split_passo_tokens(_to_text(it)))
    else:
        tokens = _split_passo_tokens(_to_text(value))
    numbers: List[int] = []
    ambiguous = False
    for t in tokens:
        m = re.match(r"^(\d+)$", t)
        if m:
            numbers.append(int(m.group(1)))
            continue
        m2 = re.search(r"(\d+)", t)
        if m2:
            numbers.append(int(m2.group(1)))
            notes.append(f"Heurística passo: token '{t}' reduzido a número — confirmar leitura.")
            ambiguous = True
    conf = 0.9 if numbers and not ambiguous else 0.55 if numbers else 0.2
    if not numbers:
        notes.append("Passo: nenhum valor numérico estável.")
    return {
        "raw": _to_text(value) if not isinstance(value, list) else value,
        "tokens": tokens,
        "numbers": numbers or None,
        "confidence": round(conf, 3),
        "parse_notes": notes,
        "needs_review": ambiguous or (bool(tokens) and not numbers),
    }


def parse_espiras_field(value: Any) -> Dict[str, Any]:
    """Espiras: listas, vírgulas ou notação tipo 70:70."""
    notes: List[str] = []
    tokens: List[str] = []
    if isinstance(value, list):
        for it in value:
            s = _to_text(it).replace(";", ",")
            tokens.extend([p.strip() for p in re.split(r"[,:\s]+", s) if p.strip()])
    else:
        s = _to_text(value).replace(";", ",")
        tokens = [p.strip() for p in re.split(r"[,:\s]+", s) if p.strip()]
    numbers: List[int] = []
    ambiguous = False
    for t in tokens:
        m = re.match(r"^(\d+)$", t)
        if m:
            numbers.append(int(m.group(1)))
            continue
        if re.search(r"[a-zA-Z]", t):
            ambiguous = True
            notes.append(f"Espiras: token com letras '{t}' — possível ruído OCR.")
        m2 = re.search(r"(\d+)", t)
        if m2:
            numbers.append(int(m2.group(1)))
    conf = 0.88 if numbers and not ambiguous else 0.5 if numbers else 0.25
    if not numbers:
        notes.append("Espiras: nenhum número confiável.")
    return {
        "raw": value,
        "tokens": tokens,
        "numbers": numbers or None,
        "confidence": round(conf, 3),
        "parse_notes": notes,
        "needs_review": ambiguous or (bool(tokens) and not numbers),
    }


def parse_fio_field(value: Any) -> Dict[str, Any]:
    """
    Fio: formatos ``1x22``, ``2x18``, ``AWG 20``, ``0,80 mm`` (apenas heurística de extração).
    """
    notes: List[str] = []
    s = _to_text(value) if not isinstance(value, list) else " ".join(_listish(value))
    if not s:
        return {
            "raw": value,
            "parallel": None,
            "gauge_token": None,
            "confidence": 0.0,
            "parse_notes": ["Fio: vazio."],
            "needs_review": False,
        }
    low = s.lower().replace(" ", "")
    parallel = 1
    gauge: Optional[str] = None
    m = re.match(r"^(\d+)x(\d+(\.\d+)?)$", low.replace(",", "."))
    if m:
        parallel = int(m.group(1))
        gauge = m.group(2)
    else:
        m2 = re.search(r"(\d+)\s*[xX]\s*(\d+(\.\d+)?)", s)
        if m2:
            parallel = int(m2.group(1))
            gauge = m2.group(2)
        else:
            awg = re.search(r"awg\s*(\d+)", s, re.I)
            if awg:
                gauge = awg.group(1)
                notes.append("Fio: referência AWG — comparação mm² não feita nesta versão.")
            else:
                nums = re.findall(r"\d+(?:[.,]\d+)?", s.replace(",", "."))
                if nums:
                    gauge = nums[0]
                    notes.append("Heurística fio: primeiro número usado como referência de calibre — revisar.")
    conf = 0.75 if gauge else 0.35
    return {
        "raw": value,
        "parallel": parallel,
        "gauge_token": gauge,
        "confidence": round(conf, 3),
        "parse_notes": notes,
        "needs_review": conf < 0.5,
    }


def parse_ranhuras_field(value: Any) -> Dict[str, Any]:
    notes: List[str] = []
    s = _to_text(value)
    if not s:
        return {"raw": "", "value": None, "confidence": 0.0, "parse_notes": ["Ranhuras: ausente."], "needs_review": False}
    m = re.search(r"(\d+)", s)
    if not m:
        notes.append("Ranhuras: nenhum inteiro encontrado.")
        return {"raw": s, "value": None, "confidence": 0.2, "parse_notes": notes, "needs_review": True}
    v = int(m.group(1))
    if v < 6 or v > 200:
        notes.append("Ranhuras: valor fora da faixa comum (6–200) — possível erro de leitura.")
        return {"raw": s, "value": v, "confidence": 0.45, "parse_notes": notes, "needs_review": True}
    return {"raw": s, "value": v, "confidence": 0.85, "parse_notes": notes, "needs_review": False}


def parse_mm_field(value: Any, label: str) -> Dict[str, Any]:
    notes: List[str] = []
    s = _to_text(value).replace(",", ".")
    if not s:
        return {
            "raw": "",
            "value_mm": None,
            "confidence": 0.0,
            "parse_notes": [f"{label}: ausente."],
            "needs_review": False,
        }
    m = re.search(r"(\d+(?:\.\d+)?)", s)
    if not m:
        return {"raw": s, "value_mm": None, "confidence": 0.2, "parse_notes": notes + ["Sem número."], "needs_review": True}
    v = float(m.group(1))
    if v <= 0 or v > 2000:
        notes.append(f"{label}: valor improvável — revisão sugerida.")
        return {"raw": s, "value_mm": v, "confidence": 0.4, "parse_notes": notes, "needs_review": True}
    return {"raw": s, "value_mm": v, "confidence": 0.82, "parse_notes": notes, "needs_review": False}


def _section(data: Dict[str, Any], key: str) -> Dict[str, Any]:
    v = data.get(key)
    return v if isinstance(v, dict) else {}


def normalize_rewinding_input(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extrai e normaliza blocos de rebobinagem / esquema / mecânica a partir do payload de oficina ou linha coerced.
    """
    data = raw if isinstance(raw, dict) else {}
    motor = _section(data, "motor")
    principal = _section(data, "bobinagem_principal")
    aux = _section(data, "bobinagem_auxiliar")
    esquema = _section(data, "esquema")
    mecanica = _section(data, "mecanica")
    oficina = _section(data, "oficina")
    parser = oficina.get("parser_tecnico") if isinstance(oficina.get("parser_tecnico"), dict) else {}

    pr_passos = parse_passo_field(principal.get("passos"))
    pr_esp = parse_espiras_field(principal.get("espiras"))
    pr_fio = parse_fio_field(principal.get("fios"))

    ax_passos = parse_passo_field(aux.get("passos"))
    ax_esp = parse_espiras_field(aux.get("espiras"))
    ax_fio = parse_fio_field(aux.get("fios"))

    ran = parse_ranhuras_field(esquema.get("ranhuras") or mecanica.get("ranhuras"))
    d_mm = parse_mm_field(mecanica.get("diametro_mm"), "Diâmetro")
    p_mm = parse_mm_field(mecanica.get("pacote_mm"), "Pacote")

    texto_ocr = _to_text(data.get("texto_ocr"))
    texto_norm = _to_text(data.get("texto_normalizado"))
    ocr_flag = bool(parser.get("needs_review") or parser.get("ambiguous"))

    global_notes: List[str] = []
    if ocr_flag:
        global_notes.append("Metadados de leitura (parser_tecnico) sugerem revisão humana.")

    return {
        "motor_ref": {
            "tipo_motor": _to_text(motor.get("tipo_motor")),
            "fases": _to_text(motor.get("fases")),
            "carcaca": _to_text(motor.get("carcaca") or mecanica.get("carcaca")),
            "capacitor": _to_text(aux.get("capacitor")),
        },
        "principal": {"passos": pr_passos, "espiras": pr_esp, "fios": pr_fio},
        "auxiliar": {"passos": ax_passos, "espiras": ax_esp, "fios": ax_fio, "capacitor": _to_text(aux.get("capacitor"))},
        "esquema": {"ranhuras": ran},
        "mecanica": {"diametro_mm": d_mm, "pacote_mm": p_mm},
        "texto": {"ocr_len": len(texto_ocr), "normalizado_len": len(texto_norm), "ocr_meta_flag": ocr_flag},
        "parse_notes_global": global_notes,
    }
