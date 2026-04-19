from __future__ import annotations

import csv
import io
import json
from typing import Any, Dict, Optional


def build_os_json_snapshot_bytes(*, os_row: Dict[str, Any], calc_row: Optional[Dict[str, Any]] = None) -> bytes:
    """Snapshot UTF-8 para arquivo interno (inclui payload completo)."""
    blob: Dict[str, Any] = {"ordem_servico": os_row}
    if calc_row:
        blob["calculo_biblioteca"] = calc_row
    return json.dumps(blob, ensure_ascii=False, indent=2, default=str).encode("utf-8")


def build_os_csv_row_bytes(*, os_row: Dict[str, Any]) -> bytes:
    """Uma linha CSV com campos principais + JSON do payload (coluna unica)."""
    pl = os_row.get("payload") if isinstance(os_row.get("payload"), dict) else {}
    payload_s = json.dumps(pl, ensure_ascii=False, default=str)
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(
        [
            "id",
            "numero",
            "titulo",
            "motor_id",
            "etapa",
            "calc_id",
            "created_by",
            "created_at",
            "updated_at",
            "payload_json",
        ]
    )
    w.writerow(
        [
            str(os_row.get("id") or ""),
            str(os_row.get("numero") or ""),
            str(os_row.get("titulo") or ""),
            str(os_row.get("motor_id") or ""),
            str(os_row.get("etapa") or ""),
            str(os_row.get("calc_id") or ""),
            str(os_row.get("created_by") or ""),
            str(os_row.get("created_at") or ""),
            str(os_row.get("updated_at") or ""),
            payload_s,
        ]
    )
    return buf.getvalue().encode("utf-8-sig")
