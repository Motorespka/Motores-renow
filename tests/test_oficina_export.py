from __future__ import annotations

from services.oficina_export import build_os_csv_row_bytes, build_os_json_snapshot_bytes


def test_os_json_export() -> None:
    os_row = {"id": "x", "numero": "OS-1", "titulo": "T", "payload": {"a": 1}}
    b = build_os_json_snapshot_bytes(os_row=os_row, calc_row=None)
    assert b.startswith(b"{")
    assert b'"ordem_servico"' in b


def test_os_csv_export() -> None:
    os_row = {"id": "i1", "numero": "OS-1", "titulo": "T", "motor_id": "", "etapa": "teste", "payload": {}}
    b = build_os_csv_row_bytes(os_row=os_row)
    assert b.startswith(b"\xef\xbb\xbf") or b"numero" in b
