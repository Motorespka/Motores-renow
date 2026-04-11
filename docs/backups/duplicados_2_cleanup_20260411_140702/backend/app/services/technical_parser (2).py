from __future__ import annotations

import re
from typing import Any, Dict, List

OCR_NOISE_NOTE = "ruido OCR detectado apos valor principal"
MULTI_VALUE_NOTE = "multiplos valores detectados; revisar manualmente"
NO_NUMBER_NOTE = "nenhum numero reconhecido no campo"


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _to_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [_to_text(v) for v in value if _to_text(v)]
    text = _to_text(value)
    if not text:
        return []
    parts = re.split(r"\s*[\n;|]\s*", text)
    rows = [p.strip() for p in parts if p.strip()]
    return rows if rows else [text]


def _extract_numbers(text: str) -> List[str]:
    found = re.findall(r"\d+(?:[.,]\d+)?", text or "")
    return [item.replace(",", ".") for item in found if item]


def _looks_like_ocr_noise(text: str) -> bool:
    raw = _to_text(text)
    if not raw:
        return False
    if "..." in raw or ".." in raw:
        return True
    if re.search(r"[,;:/\\|]{2,}", raw):
        return True
    if re.search(r"\d+\s*[,\.;:/\\|]+\s*[,;\.:/\\|]+\s*\d+", raw):
        return True
    return False


def _parse_numeric_token(text: str, *, field: str) -> Dict[str, Any]:
    raw = _to_text(text)
    if not raw:
        return {"value": "", "ambiguous": False, "needs_review": False, "notes": []}

    numbers = _extract_numbers(raw)
    if not numbers:
        return {"value": "", "ambiguous": True, "needs_review": True, "notes": [NO_NUMBER_NOTE]}

    if field == "passo" and re.fullmatch(r"\d+(?:\s+\d+)+", raw):
        # "8 10" -> "8-10" e "8 10 12" -> "8-10-12"
        return {
            "value": "-".join(numbers),
            "ambiguous": False,
            "needs_review": False,
            "notes": [],
        }

    if _looks_like_ocr_noise(raw):
        return {
            "value": numbers[0],
            "ambiguous": True,
            "needs_review": True,
            "notes": [OCR_NOISE_NOTE],
        }

    if field == "passo" and len(numbers) > 1 and re.fullmatch(r"\d+(?:[\s,\-:/;]+\d+)+", raw):
        return {
            "value": "-".join(numbers),
            "ambiguous": False,
            "needs_review": False,
            "notes": [],
        }

    if len(numbers) > 1:
        return {
            "value": numbers[0],
            "ambiguous": True,
            "needs_review": True,
            "notes": [MULTI_VALUE_NOTE],
        }

    return {
        "value": numbers[0],
        "ambiguous": False,
        "needs_review": False,
        "notes": [],
    }


def _parse_ligacao(values: List[str]) -> Dict[str, Any]:
    notes: List[str] = []
    estruturas: List[str] = []
    tipos: List[str] = []
    needs_review = False
    ambiguous = False

    for item in values:
        raw = _to_text(item)
        if not raw:
            continue
        for part in re.split(r"\s*[,/;|\\]\s*", raw):
            token_raw = _to_text(part)
            if not token_raw:
                continue
            token = re.sub(r"\s+", "", token_raw).upper()
            if not token:
                continue

            if token == "Y":
                if "estrela" not in tipos:
                    tipos.append("estrela")
                estruturas.append("Y")
                continue

            if token in {"DELTA", "D", "Δ"}:
                if "delta" not in tipos:
                    tipos.append("delta")
                estruturas.append(token_raw)
                continue

            if token in {"ESTRELA", "STAR", "WYE"}:
                if "estrela" not in tipos:
                    tipos.append("estrela")
                estruturas.append(token_raw)
                continue

            # "Y" misturado (ex.: "1Y21"): nao assumir estrela.
            if "Y" in token:
                needs_review = True
                ambiguous = True
                notes.append("marcador Y misturado com outros caracteres; revisar manualmente")
                estruturas.append(token_raw)
                continue

            if "DELTA" in token or "Δ" in token:
                if "delta" not in tipos:
                    tipos.append("delta")
                estruturas.append(token_raw)
                continue

            estruturas.append(token_raw)

    tipo_eletrico = ""
    if len(tipos) == 1:
        tipo_eletrico = tipos[0]
    elif len(tipos) > 1:
        needs_review = True
        ambiguous = True
        notes.append("mais de um tipo de ligacao detectado; revisar manualmente")

    ligacao_observacao = " | ".join(dict.fromkeys(notes))
    return {
        "ligacao_tipo_eletrico": tipo_eletrico,
        "ligacao_estrutura": ", ".join(dict.fromkeys([_to_text(v) for v in estruturas if _to_text(v)])),
        "ligacao_observacao": ligacao_observacao,
        "needs_review": needs_review,
        "ambiguous": ambiguous,
    }


def _parse_ocr_noise_sequence(raw_values: List[str]) -> Dict[str, Any] | None:
    rows = [_to_text(v) for v in (raw_values or []) if _to_text(v)]
    if not rows:
        return None

    joined = " ".join(rows)
    numbers = _extract_numbers(joined)
    if not numbers:
        return None

    has_noise_marker = any(("..." in item or ".." in item) for item in rows)
    if not has_noise_marker:
        # Exemplo de ruido apos split: ["50", "...", "0"]
        has_noise_marker = any(re.fullmatch(r"[.,;:/\\|]+", item or "") for item in rows)
    if not has_noise_marker:
        return None

    return {
        "value": numbers[0],
        "ambiguous": True,
        "needs_review": True,
        "notes": [OCR_NOISE_NOTE],
    }


def parse_technical_bobinagem(normalized: Dict[str, Any]) -> Dict[str, Any]:
    payload = normalized if isinstance(normalized, dict) else {}
    principal = payload.get("bobinagem_principal") if isinstance(payload.get("bobinagem_principal"), dict) else {}
    auxiliar = payload.get("bobinagem_auxiliar") if isinstance(payload.get("bobinagem_auxiliar"), dict) else {}
    esquema = payload.get("esquema") if isinstance(payload.get("esquema"), dict) else {}

    espiras_bruto = _to_list(principal.get("espiras"))
    passo_bruto = _to_list(principal.get("passos"))

    espiras_normalizado: List[str] = []
    passo_normalizado: List[str] = []
    notes: List[str] = []
    ambiguous = False
    needs_review = False

    espiras_noise = _parse_ocr_noise_sequence(espiras_bruto)
    if espiras_noise:
        if espiras_noise.get("value"):
            espiras_normalizado.append(str(espiras_noise["value"]))
        notes.extend([str(n) for n in espiras_noise.get("notes", []) if str(n).strip()])
        ambiguous = ambiguous or bool(espiras_noise.get("ambiguous"))
        needs_review = needs_review or bool(espiras_noise.get("needs_review"))
    else:
        for item in espiras_bruto:
            parsed = _parse_numeric_token(item, field="espiras")
            if parsed.get("value"):
                espiras_normalizado.append(str(parsed["value"]))
            notes.extend([str(n) for n in parsed.get("notes", []) if str(n).strip()])
            ambiguous = ambiguous or bool(parsed.get("ambiguous"))
            needs_review = needs_review or bool(parsed.get("needs_review"))

    passo_noise = _parse_ocr_noise_sequence(passo_bruto)
    if passo_noise:
        if passo_noise.get("value"):
            passo_normalizado.append(str(passo_noise["value"]))
        notes.extend([str(n) for n in passo_noise.get("notes", []) if str(n).strip()])
        ambiguous = ambiguous or bool(passo_noise.get("ambiguous"))
        needs_review = needs_review or bool(passo_noise.get("needs_review"))
    else:
        for item in passo_bruto:
            parsed = _parse_numeric_token(item, field="passo")
            if parsed.get("value"):
                passo_normalizado.append(str(parsed["value"]))
            notes.extend([str(n) for n in parsed.get("notes", []) if str(n).strip()])
            ambiguous = ambiguous or bool(parsed.get("ambiguous"))
            needs_review = needs_review or bool(parsed.get("needs_review"))

    ligacao_vals: List[str] = []
    for source in [principal.get("ligacao"), auxiliar.get("ligacao"), esquema.get("ligacao")]:
        ligacao_vals.extend(_to_list(source))
    ligacao = _parse_ligacao(ligacao_vals)
    ambiguous = ambiguous or bool(ligacao.get("ambiguous"))
    needs_review = needs_review or bool(ligacao.get("needs_review"))

    parse_note = " | ".join(dict.fromkeys(notes))
    status_revisao = "revisar" if needs_review else "ok"

    if not (espiras_normalizado or passo_normalizado):
        confianca_dados = "baixa"
    elif needs_review:
        confianca_dados = "baixa"
    elif ligacao.get("ligacao_tipo_eletrico"):
        confianca_dados = "alta"
    else:
        confianca_dados = "media"

    return {
        "espiras_bruto": espiras_bruto,
        "passo_bruto": passo_bruto,
        "espiras_normalizado": espiras_normalizado,
        "passo_normalizado": passo_normalizado,
        "confianca_dados": confianca_dados,
        "ligacao_tipo_eletrico": str(ligacao.get("ligacao_tipo_eletrico") or ""),
        "ligacao_estrutura": str(ligacao.get("ligacao_estrutura") or ""),
        "ligacao_observacao": str(ligacao.get("ligacao_observacao") or ""),
        "candidate_alternatives": [],
        "parse_note": parse_note,
        "ambiguous": bool(ambiguous),
        "needs_review": bool(needs_review),
        "status_revisao": status_revisao,
    }
