#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Carrega metadata/sidecars/tail_mutirao_correcoes.json e aplica overrides
antes da auditoria/categorização/reconciliação da cauda B58/B59.
"""

from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CORRECOES_PATH = REPO_ROOT / "metadata" / "sidecars" / "tail_mutirao_correcoes.json"

_META_KEYS = frozenset({"_schema_version", "_instrucoes", "_fonte_csv"})


def _t(v: Any) -> str:
    return "" if v is None else str(v).strip()


def _basename(rel_or_name: str) -> str:
    return Path(_t(rel_or_name).replace("\\", "/")).name


def load_tail_mutirao_correcoes(path: Optional[Path] = None) -> Dict[str, Any]:
    p = path or DEFAULT_CORRECOES_PATH
    if not p.is_file():
        return {}
    data = json.loads(p.read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if k not in _META_KEYS and isinstance(v, dict)}


def _index_correcoes(raw: Dict[str, Any]) -> Tuple[Dict[str, dict], Dict[str, dict]]:
    by_file: Dict[str, dict] = {}
    by_sha: Dict[str, dict] = {}
    for key, entry in raw.items():
        if not isinstance(entry, dict):
            continue
        ent = deepcopy(entry)
        fn = _basename(ent.get("file_name") or key)
        by_file[fn.lower()] = ent
        sh = _t(ent.get("sha")).lower()
        if sh:
            by_sha[sh] = ent
        if key.lower().endswith(".pdf"):
            by_file[_basename(key).lower()] = ent
    return by_file, by_sha


def lookup_correcao(
    raw: Dict[str, Any],
    *,
    arquivo: str = "",
    sha: str = "",
) -> Optional[dict]:
    by_file, by_sha = _index_correcoes(raw)
    sh = _t(sha).lower()
    if sh and sh in by_sha:
        return by_sha[sh]
    bn = _basename(arquivo).lower()
    if bn and bn in by_file:
        return by_file[bn]
    for k, ent in by_file.items():
        if bn and (bn == k or bn.endswith(k) or k in bn):
            return ent
    return None


def apply_override_fields(row: Dict[str, str], correcao: dict) -> Dict[str, str]:
    out = dict(row)
    overrides = correcao.get("override_fields") or {}
    if not isinstance(overrides, dict):
        return out
    for k, v in overrides.items():
        if v is None:
            continue
        out[k] = str(v)
    return out


def filter_alert_codes(codes: List[str], bypass: List[str]) -> List[str]:
    if not bypass:
        return codes
    bp = {_t(x).upper() for x in bypass}
    out: List[str] = []
    for c in codes:
        cu = _t(c).upper()
        skip = False
        for b in bp:
            if cu == b or cu.startswith(b + "_") or b in cu:
                skip = True
                break
        if not skip:
            out.append(c)
    return out


def filter_alert_string(cell: str, bypass: List[str]) -> str:
    if not cell or not bypass:
        return cell
    parts = [p.strip() for p in re.split(r"[;|]", cell) if p.strip()]
    return ";".join(filter_alert_codes(parts, bypass))


def apply_correcao_to_row(
    row: Dict[str, str],
    correcao: Optional[dict],
) -> Dict[str, str]:
    if not correcao:
        return row
    return apply_override_fields(row, correcao)


def apply_correcao_to_audit_row(
    audit_row: Optional[Dict[str, str]],
    correcao: Optional[dict],
) -> Optional[Dict[str, str]]:
    if not audit_row or not correcao:
        return audit_row
    bypass = correcao.get("force_bypass_alerts") or []
    if not bypass:
        return audit_row
    out = dict(audit_row)
    for col in ("alertas_criticos", "alertas", "audit_warnings_A"):
        if col in out:
            out[col] = filter_alert_string(_t(out.get(col)), bypass)
    return out


def resolve_correcao_for_paths(
  path: Optional[Path] = None,
  *,
  arquivo: str = "",
  sha: str = "",
) -> Optional[dict]:
    raw = load_tail_mutirao_correcoes(path)
    return lookup_correcao(raw, arquivo=arquivo, sha=sha)
