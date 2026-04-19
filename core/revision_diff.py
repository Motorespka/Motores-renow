"""Resumo legivel de alteracoes entre dois dicts (ex.: revisao de ficha)."""

from __future__ import annotations

import json
from typing import Any, Dict, List


def _flatten_dict(d: Dict[str, Any], prefix: str = "") -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not isinstance(d, dict):
        return {prefix or "root": json.dumps(d, ensure_ascii=False, default=str)[:800]}
    for k, v in d.items():
        path = f"{prefix}.{k}" if prefix else str(k)
        if isinstance(v, dict):
            out.update(_flatten_dict(v, path))
        elif isinstance(v, list):
            out[path] = json.dumps(v, ensure_ascii=False, default=str)[:600]
        else:
            out[path] = "" if v is None else str(v)
    return out


def summarize_dict_changes(before: Dict[str, Any], after: Dict[str, Any], *, max_keys: int = 40) -> str:
    bf = _flatten_dict(before if isinstance(before, dict) else {})
    af = _flatten_dict(after if isinstance(after, dict) else {})
    keys: List[str] = sorted(set(bf) | set(af))
    changed = [k for k in keys if bf.get(k) != af.get(k)]
    if not changed:
        return "(Nenhuma diferenca em campos planeados — pode haver campos omitidos.)"
    lines: List[str] = []
    for k in changed[:max_keys]:
        a, b = bf.get(k, ""), af.get(k, "")
        lines.append(f"- **{k}**: `{a[:120]}` → `{b[:120]}`")
    if len(changed) > max_keys:
        lines.append(f"- … mais **{len(changed) - max_keys}** campos.")
    return "\n".join(lines)


def snapshot_jsonable(obj: Any) -> Dict[str, Any]:
    try:
        return json.loads(json.dumps(obj, default=str))
    except Exception:
        return {}
