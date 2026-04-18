from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _safe_lines(text: str, *, max_len: int = 120) -> List[str]:
    t = _to_text(text)
    if not t:
        return []
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    out: List[str] = []
    for raw in t.split("\n"):
        s = raw.strip()
        if not s:
            continue
        while len(s) > max_len:
            out.append(s[:max_len])
            s = s[max_len:]
        out.append(s)
    return out


def build_os_delivery_pdf_bytes(
    *,
    os_row: Dict[str, Any],
    calc_row: Optional[Dict[str, Any]] = None,
    title: str = "Relatorio de entrega (oficina)",
) -> bytes:
    """
    PDF simples para entrega ao cliente (sem depender de HTML render/PDF engine).
    Requer `fpdf2` (ver requirements.txt).
    """
    from fpdf import FPDF  # lazy import (cloud)

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, title, ln=True)

    pdf.set_font("Helvetica", "", 10)
    os_num = _to_text(os_row.get("numero") or os_row.get("id"))
    motor_id = _to_text(os_row.get("motor_id") or "")
    etapa = _to_text(os_row.get("etapa") or "")
    pdf.cell(0, 6, f"OS: {os_num}  |  Etapa: {etapa}", ln=True)
    if motor_id:
        pdf.cell(0, 6, f"Motor id: {motor_id}", ln=True)
    pdf.cell(0, 6, f"Emitido em: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} (UTC)", ln=True)

    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Resumo do servico", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, _to_text(os_row.get("titulo") or "") or "-")

    if calc_row:
        pdf.ln(1)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, "Calculo aplicado (biblioteca)", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 5, _to_text(calc_row.get("titulo") or "") or "-")

        payload = calc_row.get("payload") if isinstance(calc_row.get("payload"), dict) else {}
        tests = payload.get("testes_bancada")
        if isinstance(tests, list) and tests:
            pdf.ln(1)
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(0, 7, "Testes de bancada (referencia do calculo)", ln=True)
            pdf.set_font("Helvetica", "", 10)
            for g in tests:
                if not isinstance(g, dict):
                    continue
                nome = _to_text(g.get("nome")) or "Teste"
                pdf.set_font("Helvetica", "B", 10)
                pdf.multi_cell(0, 5, f"- {nome}")
                pdf.set_font("Helvetica", "", 10)
                linhas = g.get("linhas") if isinstance(g.get("linhas"), list) else []
                for idx, ln in enumerate(linhas[:40]):
                    if not isinstance(ln, dict):
                        continue
                    lbl = _to_text(ln.get("teste")) or f"Teste {idx+1}"
                    val = _to_text(ln.get("valor")) or "-"
                    pdf.multi_cell(0, 5, f"  {lbl}: {val}")

    pl_os = os_row.get("payload") if isinstance(os_row.get("payload"), dict) else {}
    ficha = pl_os.get("ficha_mecanica") if isinstance(pl_os.get("ficha_mecanica"), dict) else {}
    if ficha and any(_to_text(v) for v in ficha.values()):
        pdf.ln(1)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, "Ficha mecanica (registro)", ln=True)
        pdf.set_font("Helvetica", "", 10)
        for k in [
            "rolamento_drive",
            "rolamento_oposto",
            "alinhamento",
            "torque_carcaca",
            "vibracao",
            "temperatura_teste",
        ]:
            v = _to_text(ficha.get(k))
            if v:
                pdf.multi_cell(0, 5, f"- {k}: {v}")
        for k in ["obs_antes", "obs_depois"]:
            v = _to_text(ficha.get(k))
            if v:
                pdf.ln(1)
                pdf.set_font("Helvetica", "B", 10)
                pdf.multi_cell(0, 5, k.replace("_", " ").title())
                pdf.set_font("Helvetica", "", 10)
                for line in _safe_lines(v, max_len=140):
                    pdf.multi_cell(0, 5, line)

    eventos = pl_os.get("eventos")
    if isinstance(eventos, list) and eventos:
        pdf.ln(1)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, "Linha do tempo (ultimos eventos)", ln=True)
        pdf.set_font("Helvetica", "", 10)
        for e in eventos[-30:]:
            if not isinstance(e, dict):
                continue
            dt = _to_text(e.get("data"))
            et = _to_text(e.get("etapa"))
            nota = _to_text(e.get("nota"))
            pdf.multi_cell(0, 5, f"- {dt} | {et} | {nota}")

    return bytes(pdf.output(dest="S"))

