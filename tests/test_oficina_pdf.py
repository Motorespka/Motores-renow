from __future__ import annotations

from services.oficina_pdf import build_os_delivery_pdf_bytes


def test_build_os_delivery_pdf_smoke() -> None:
    os_row = {
        "numero": "OS-CI",
        "titulo": "Teste rebobinagem",
        "etapa": "entrega",
        "motor_id": "00000000-0000-0000-0000-000000000001",
        "payload": {
            "texto_relatorio_entrega": "Texto ao cliente com acentuacao (teste).",
            "anexos_urls": ["https://example.com/foto1.jpg"],
            "capa_responsavel": "Oficina Teste",
            "eventos": [{"data": "2026-01-02", "etapa": "teste", "nota": "OK"}],
        },
    }
    b = build_os_delivery_pdf_bytes(os_row=os_row, calc_row=None)
    assert isinstance(b, (bytes, bytearray))
    assert len(b) > 800
    assert bytes(b[:4]) == b"%PDF"
