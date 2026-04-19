from __future__ import annotations

import os
import unicodedata
from io import BytesIO
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from services.oficina_os_operacao import linhas_resumo_operacao_pdf


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _flatten_latin_pdf(text: str) -> str:
    """Helvetica WinAnsi: remove combining marks and cedilla where NFKD does not."""
    if not text:
        return ""
    t = unicodedata.normalize("NFKD", text)
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return t.replace("ç", "c").replace("Ç", "C")


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


def _font_candidates() -> List[Tuple[str, str]]:
    """
    (path_regular, path_bold_or_empty). Prefer DejaVu on Linux (Streamlit Cloud),
    Arial/Calibri on Windows; optional drop-in next to this file.
    """
    here = Path(__file__).resolve().parent
    env = os.environ.get("MOTORES_PDF_FONT_REGULAR")
    env_b = os.environ.get("MOTORES_PDF_FONT_BOLD")
    if env:
        return [(env, env_b or "")]

    out: List[Tuple[str, str]] = []
    for reg, bol in [
        (here / "DejaVuSans.ttf", here / "DejaVuSans-Bold.ttf"),
        (Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")),
        (Path("/usr/share/fonts/TTF/DejaVuSans.ttf"), Path("/usr/share/fonts/TTF/DejaVuSans-Bold.ttf")),
    ]:
        if reg.exists():
            out.append((str(reg), str(bol) if bol.exists() else ""))

    windir = os.environ.get("WINDIR", "C:/Windows")
    for reg, bol in [
        (Path(windir) / "Fonts" / "arial.ttf", Path(windir) / "Fonts" / "arialbd.ttf"),
        (Path(windir) / "Fonts" / "calibri.ttf", Path(windir) / "Fonts" / "calibrib.ttf"),
    ]:
        if reg.exists():
            out.append((str(reg), str(bol) if bol.exists() else ""))

    return out


def _setup_body_font(pdf: Any) -> Tuple[str, bool]:
    """
    Returns (family, unicode_ok). If unicode_ok, use UTF-8 as-is; else flatten user text for Helvetica.
    """
    for reg, bol in _font_candidates():
        try:
            pdf.add_font("MRBody", "", reg)
            if bol:
                pdf.add_font("MRBody", "B", bol)
            else:
                pdf.add_font("MRBody", "B", reg)
            return "MRBody", True
        except Exception:
            continue
    return "Helvetica", False


def _set(pdf: Any, family: str, style: str, size: int) -> None:
    pdf.set_font(family, style, size)


def _txt(s: str, unicode_ok: bool) -> str:
    return s if unicode_ok else _flatten_latin_pdf(s)


class _DeliveryPDF:
    """Factory: build a subclass of FPDF with header/footer — avoids importing FPDF at module load."""

    @staticmethod
    def build(*, header_line1: str, header_line2: str, footer_left: str):
        from fpdf import FPDF
        from fpdf.enums import XPos, YPos

        h1 = header_line1
        h2 = header_line2
        fl = footer_left

        class DeliveryPDF(FPDF):
            def header(self) -> None:
                _set(self, self._mr_family, "B", 11)
                self.cell(0, 6, h1, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                _set(self, self._mr_family, "", 9)
                self.cell(0, 5, h2, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
                self.ln(2)

            def footer(self) -> None:
                self.set_y(-12)
                _set(self, self._mr_family, "", 8)
                w = self.w - self.l_margin - self.r_margin
                self.cell(w * 0.62, 5, fl, align="L", new_x=XPos.RIGHT, new_y=YPos.TOP)
                self.cell(w * 0.38, 5, f"Pag. {self.page_no()}/{{nb}}", align="R", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        return DeliveryPDF


REPO_ROOT = Path(__file__).resolve().parent.parent


def _first_logo_path() -> Optional[Path]:
    d = REPO_ROOT / "assets"
    if not d.is_dir():
        return None
    for name in ("logo.png", "logo_mrw.png", "brand.png", "logo.jpg"):
        p = d / name
        if p.is_file():
            return p
    return None


def build_os_delivery_pdf_bytes(
    *,
    os_row: Dict[str, Any],
    calc_row: Optional[Dict[str, Any]] = None,
    title: str = "Relatorio de entrega (oficina)",
) -> bytes:
    """
    PDF para entrega ao cliente. Usa ``fpdf2``; tenta DejaVu (Linux) ou Arial (Windows) para PT-BR;
    senão Helvetica + texto sem acentos.
    """
    os_num = _to_text(os_row.get("numero") or os_row.get("id"))
    etapa = _to_text(os_row.get("etapa") or "")
    motor_id = _to_text(os_row.get("motor_id") or "")
    issued = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    header_line1 = _flatten_latin_pdf("Moto-Renow - Oficina / rebobinagem")
    header_line2 = _flatten_latin_pdf(f"{title}  |  OS {os_num}  |  {issued}")

    DeliveryPDF = _DeliveryPDF.build(
        header_line1=header_line1,
        header_line2=header_line2,
        footer_left=_flatten_latin_pdf("Uso interno / referencia de servico"),
    )
    pdf = DeliveryPDF(orientation="P", unit="mm", format="A4")
    family, unicode_ok = _setup_body_font(pdf)
    pdf._mr_family = family
    pdf.set_margins(14, 18, 14)
    pdf.set_auto_page_break(auto=True, margin=14)
    try:
        pdf.alias_nb_pages()
    except Exception:
        pass

    pdf.add_page()
    _set(pdf, family, "", 10)

    from fpdf.enums import XPos, YPos

    def mc(w: float, h: float, t: str) -> None:
        pdf.multi_cell(w, h, t, new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pl_os = os_row.get("payload") if isinstance(os_row.get("payload"), dict) else {}

    logo = _first_logo_path()
    if logo:
        try:
            pdf.image(str(logo), x=pdf.l_margin, w=min(48.0, float(pdf.w - pdf.l_margin - pdf.r_margin)))
            pdf.ln(2)
        except Exception:
            pass

    empresa = _to_text(os.environ.get("MOTORES_PDF_EMPRESA")) or "Moto-Renow"
    ender = _to_text(os.environ.get("MOTORES_PDF_ENDERECO"))
    resp = _to_text(pl_os.get("capa_responsavel")) or _to_text(os.environ.get("MOTORES_PDF_RESPONSAVEL"))

    _set(pdf, family, "B", 17)
    mc(0, 8, _txt(f"OS {os_num}", unicode_ok))
    _set(pdf, family, "", 10)
    mc(0, 5, _txt(empresa, unicode_ok))
    if ender:
        mc(0, 4, _txt(ender, unicode_ok))
    if resp:
        _set(pdf, family, "", 9)
        mc(0, 4, _txt(f"Responsavel / oficina: {resp}", unicode_ok))
        _set(pdf, family, "", 10)
    pdf.ln(2)

    notas_cliente = _to_text(pl_os.get("texto_relatorio_entrega"))
    if notas_cliente:
        _set(pdf, family, "B", 11)
        mc(0, 5, _txt("Notas para o cliente (entrega)", unicode_ok))
        _set(pdf, family, "", 10)
        for line in _safe_lines(notas_cliente, max_len=110):
            mc(0, 5, _txt(line, unicode_ok))
        pdf.ln(2)

    anexos = pl_os.get("anexos_urls")
    if isinstance(anexos, list) and anexos:
        _set(pdf, family, "B", 11)
        mc(0, 5, _txt("Anexos / referencias (URLs — nao embutidos no PDF)", unicode_ok))
        _set(pdf, family, "", 9)
        for u in anexos[:35]:
            line = _to_text(u)
            if line:
                for chunk in _safe_lines(line, max_len=100):
                    mc(0, 4, _txt(chunk, unicode_ok))
        pdf.ln(1)

    _set(pdf, family, "B", 11)
    pdf.cell(0, 6, _txt("Resumo do servico", unicode_ok), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    _set(pdf, family, "", 10)
    mc(0, 5, _txt(_to_text(os_row.get("titulo") or "") or "-", unicode_ok))

    pdf.ln(1)
    _set(pdf, family, "", 9)
    mc(
        0,
        4,
        _txt(f"Etapa atual: {etapa}" + (f"  |  Motor id: {motor_id}" if motor_id else ""), unicode_ok),
    )

    op_lines = linhas_resumo_operacao_pdf(pl_os)
    if op_lines:
        pdf.ln(1)
        _set(pdf, family, "B", 11)
        mc(0, 5, _txt("Operacao interna (sem dados de cliente)", unicode_ok))
        _set(pdf, family, "", 9)
        for line in op_lines:
            mc(0, 4, _txt(line, unicode_ok))

    if calc_row:
        pdf.ln(1)
        _set(pdf, family, "B", 11)
        mc(0, 5, _txt("Calculo aplicado (biblioteca)", unicode_ok))
        _set(pdf, family, "", 10)
        mc(0, 5, _txt(_to_text(calc_row.get("titulo") or "") or "-", unicode_ok))

        payload = calc_row.get("payload") if isinstance(calc_row.get("payload"), dict) else {}
        tests = payload.get("testes_bancada")
        if isinstance(tests, list) and tests:
            pdf.ln(1)
            _set(pdf, family, "B", 11)
            mc(0, 5, _txt("Testes de bancada (referencia do calculo)", unicode_ok))
            for g in tests:
                if not isinstance(g, dict):
                    continue
                nome = _to_text(g.get("nome")) or "Teste"
                _set(pdf, family, "B", 10)
                mc(0, 5, _txt(f"- {nome}", unicode_ok))
                _set(pdf, family, "", 10)
                linhas = g.get("linhas") if isinstance(g.get("linhas"), list) else []
                for idx, ln in enumerate(linhas[:40]):
                    if not isinstance(ln, dict):
                        continue
                    lbl = _to_text(ln.get("teste")) or f"Teste {idx+1}"
                    val = _to_text(ln.get("valor")) or "-"
                    suf = ""
                    res = _to_text(ln.get("resultado")).upper()
                    if res in ("OK", "FORA", "NOK", "FALHA"):
                        suf += f"  [{res}]"
                    lim = _to_text(ln.get("limite_ref"))
                    if lim:
                        suf += f"  ref: {lim}"
                    mc(0, 5, _txt(f"  {lbl}: {val}{suf}", unicode_ok))

    ficha = pl_os.get("ficha_mecanica") if isinstance(pl_os.get("ficha_mecanica"), dict) else {}
    if ficha and any(_to_text(v) for v in ficha.values()):
        pdf.ln(1)
        _set(pdf, family, "B", 11)
        mc(0, 5, _txt("Ficha mecanica (registro)", unicode_ok))
        _set(pdf, family, "", 10)
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
                mc(0, 5, _txt(f"- {k}: {v}", unicode_ok))
        for k in ["obs_antes", "obs_depois"]:
            v = _to_text(ficha.get(k))
            if v:
                pdf.ln(1)
                _set(pdf, family, "B", 10)
                mc(0, 5, _txt(k.replace("_", " ").title(), unicode_ok))
                _set(pdf, family, "", 10)
                for line in _safe_lines(v, max_len=140):
                    mc(0, 5, _txt(line, unicode_ok))

    eventos = pl_os.get("eventos")
    if isinstance(eventos, list) and eventos:
        pdf.ln(1)
        _set(pdf, family, "B", 11)
        mc(0, 5, _txt("Linha do tempo (ultimos eventos)", unicode_ok))
        _set(pdf, family, "", 10)
        for e in eventos[-30:]:
            if not isinstance(e, dict):
                continue
            dt = _to_text(e.get("data"))
            et = _to_text(e.get("etapa"))
            nota = _to_text(e.get("nota"))
            mc(0, 5, _txt(f"- {dt} | {et} | {nota}", unicode_ok))

    buf = BytesIO()
    try:
        pdf.output(buf)
        raw = buf.getvalue()
    except TypeError:
        out = pdf.output(dest="S")
        if isinstance(out, (bytes, bytearray)):
            return bytes(out)
        return str(out).encode("latin-1")
    else:
        return bytes(raw)
