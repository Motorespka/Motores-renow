"""
Campos opcionais de operacao na OS (sem dados de cliente / PII).

Valores monetarios em **centavos** (inteiro) para evitar float; prazo em **YYYY-MM-DD**.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MAX_CENTAVOS = 10**12 - 1


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def parse_centavos(value: Any) -> Optional[int]:
    """Inteiro >= 0 ou None se vazio/invalido."""
    if value is None or value == "":
        return None
    try:
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            n = value
        elif isinstance(value, float):
            n = int(round(value))
        else:
            n = int(str(value).strip().replace(".", "").replace(",", ""))
    except (TypeError, ValueError):
        return None
    if n < 0 or n > MAX_CENTAVOS:
        return None
    return n


def parse_prazo_entrega_iso(value: Any) -> Tuple[Optional[str], Optional[str]]:
    """
    Retorna (data_iso, erro_pt).
    Aceita string YYYY-MM-DD ou date/datetime.
    """
    if value is None or value == "":
        return None, None
    if isinstance(value, datetime):
        return value.date().isoformat(), None
    if isinstance(value, date):
        return value.isoformat(), None
    s = _to_text(value)
    if not s:
        return None, None
    if not ISO_DATE.match(s):
        return None, "Prazo: use AAAA-MM-DD (ex.: 2026-04-30)."
    try:
        y, m, d = int(s[0:4]), int(s[5:7]), int(s[8:10])
        date(y, m, d)
    except ValueError:
        return None, "Prazo: data invalida."
    return s, None


def normalize_operacao_payload_patch(patch: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filtra e valida chaves operacionais para merge na OS.
    Levanta ValueError com mensagem PT em caso de erro.
    """
    out: Dict[str, Any] = {}
    if not patch:
        return out

    if "prazo_entrega_previsto" in patch:
        d, err = parse_prazo_entrega_iso(patch.get("prazo_entrega_previsto"))
        if err:
            raise ValueError(err)
        if d:
            out["prazo_entrega_previsto"] = d
        else:
            out["prazo_entrega_previsto"] = ""

    for key in (
        "orcamento_centavos",
        "custo_material_centavos",
        "custo_mao_obra_centavos",
    ):
        if key not in patch:
            continue
        raw = patch.get(key)
        if raw is None or raw == "":
            out[key] = None
            continue
        c = parse_centavos(raw)
        if c is None:
            raise ValueError(f"{key}: informe inteiro em centavos (ex.: 15000 = R$ 150,00).")
        out[key] = c

    if "referencia_interna_os" in patch:
        # Texto curto: referencia de trabalho (OS interna), nao nome de cliente.
        t = _to_text(patch.get("referencia_interna_os"))[:200]
        out["referencia_interna_os"] = t

    return out


def format_centavos_br(c: Optional[int]) -> str:
    if c is None:
        return ""
    reais = c // 100
    cent = c % 100
    # Separador de milhar simples
    s = f"{reais:,}".replace(",", ".")
    return f"R$ {s},{cent:02d}"


def linhas_resumo_operacao_pdf(pl_os: Dict[str, Any]) -> List[str]:
    """Linhas de texto para secao interna do PDF (sem PII obrigatorio)."""
    if not isinstance(pl_os, dict):
        return []
    lines: List[str] = []
    ref = _to_text(pl_os.get("referencia_interna_os"))
    if ref:
        lines.append(f"Referencia interna: {ref}")
    prazo = _to_text(pl_os.get("prazo_entrega_previsto"))
    if prazo:
        lines.append(f"Prazo previsto (entrega interna): {prazo}")
    oc = pl_os.get("orcamento_centavos")
    cm = pl_os.get("custo_material_centavos")
    cl = pl_os.get("custo_mao_obra_centavos")
    oc_p, cm_p, cl_p = parse_centavos(oc), parse_centavos(cm), parse_centavos(cl)
    if oc_p is not None:
        lines.append(f"Orcamento (interno): {format_centavos_br(oc_p)}")
    if cm_p is not None:
        lines.append(f"Custo material (interno): {format_centavos_br(cm_p)}")
    if cl_p is not None:
        lines.append(f"Custo mao-de-obra (interno): {format_centavos_br(cl_p)}")
    if cm_p is not None and cl_p is not None and oc_p is not None:
        margem = oc_p - (cm_p + cl_p)
        lines.append(f"Margem sobre orcamento (interno): {format_centavos_br(margem)}")
    return lines
