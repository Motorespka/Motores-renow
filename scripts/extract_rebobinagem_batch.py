from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import io
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from PIL import Image, ImageOps
from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[0]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from services.gemini_key_manager import GeminiKeyManager, redact_secrets_in_text  # noqa: E402
from services.gemini_env_parse import dedupe_entries_first_wins, parse_gemini_key_entries_from_file  # noqa: E402
from services.motor_rebobinagem.schema_sidecar import (  # noqa: E402
    build_schema_sidecar_from_parsed,
    merge_gemini_nested_into_sidecar,
    sidecar_to_json_safe,
)

_EASYOCR_READER: Any = None


def _get_easyocr_reader() -> Any:
    global _EASYOCR_READER
    if _EASYOCR_READER is None:
        import easyocr  # type: ignore

        _EASYOCR_READER = easyocr.Reader(["pt", "en"], gpu=False)
    return _EASYOCR_READER


ALLOWED_EXTS = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}


def gemini_api_call_allowed(args: Any, gemini_api_calls: int) -> bool:
    """
    Indica se a *próxima* chamada HTTP à API Gemini é permitida.
    Hits de cache não passam aqui (não consomem API).

    FASE 5D:
    - --no-gemini: nunca permite API (independente de --force-gemini-on-retry).
    - --max-gemini-calls omitido (None): sem limite superior.
    - --max-gemini-calls 0: zero chamadas API (explicitamente não é „sem limite“).
    - --max-gemini-calls N > 0: permite enquanto gemini_api_calls < N.
    """
    if getattr(args, "no_gemini", False):
        return False
    mc = getattr(args, "max_gemini_calls", None)
    if mc is None:
        return True
    try:
        n = int(mc)
    except (TypeError, ValueError):
        return True
    if n <= 0:
        return False
    return int(gemini_api_calls) < n


def apply_quota_friendly_max_gemini_cap(args: Any) -> None:
    """
    Com --quota-friendly, se o utilizador não especificou --max-gemini-calls,
    aplica um teto modesto de chamadas API. **Nunca** reescreve 0 explícito (FASE 5D).
    """
    if not getattr(args, "quota_friendly", False):
        return
    if getattr(args, "max_gemini_calls", None) is not None:
        return
    args.max_gemini_calls = 5


def _load_dotenv_candidates() -> None:
    mono_root = REPO_ROOT.parent
    candidates = [
        mono_root / ".env",
        mono_root / "Calculos" / ".env",
        REPO_ROOT / ".env",
    ]
    for p in candidates:
        if p.exists():
            load_dotenv(p, override=False)


def _load_unique_keys_from_env_file(env_file: Path) -> List[Tuple[str, str]]:
    entries = parse_gemini_key_entries_from_file(env_file)
    unique_pairs, _h2a = dedupe_entries_first_wins(entries)
    out: List[Tuple[str, str]] = []
    for i, (_a, k) in enumerate(unique_pairs, start=1):
        out.append((f"UQ_{i}", k))
    return out


def _refresh_key_status_before_run(km: GeminiKeyManager, *, sleep_seconds: float) -> Dict[str, int]:
    import google.generativeai as genai  # local import

    model_name = (km.model_default or "gemini-2.5-flash").strip()
    stats = {
        "total": 0,
        "ok": 0,
        "invalid": 0,
        "permission_denied": 0,
        "quota_exhausted": 0,
        "unavailable": 0,
        "unknown_error": 0,
    }
    items = sorted(list(km._keys_by_alias.items()), key=lambda x: x[0])  # noqa: SLF001
    for idx, (alias, key) in enumerate(items):
        stats["total"] += 1
        if idx > 0:
            time.sleep(max(0.5, float(sleep_seconds)))
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel(model_name)
            model.generate_content("ping", generation_config={"max_output_tokens": 1, "temperature": 0})
            km.mark_success(alias)
            stats["ok"] += 1
        except Exception as exc:  # noqa: BLE001
            info = km.mark_failure(alias, exc)
            st = str(info.get("status") or "unknown_error")
            if st in stats:
                stats[st] += 1
            else:
                stats["unknown_error"] += 1
        km.save_status()
    return stats


def _refresh_key_status_from_snapshot(km: GeminiKeyManager, snapshot_path: Path) -> bool:
    """
    Atualiza km._status a partir de logs/gemini_keys_check_snapshot.json (sem API).
    Objetivo: alinhar “eligible_ok” com o último check sem queimar quota num refresh.
    """
    if not snapshot_path.is_file():
        return False
    try:
        raw = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except Exception:
        return False
    results = raw.get("results") or []
    if not isinstance(results, list) or not results:
        return False

    for r in results:
        alias = _t(r.get("key_alias"))
        st = _t(r.get("status")) or "unknown_error"
        if not alias:
            continue
        ks = km._status.get(alias)  # noqa: SLF001
        if not ks:
            # se o alias não existe no km (ex.: KEY_* vs UQ_*), ignora
            continue
        ks.status = st
        ks.http_code = r.get("http_code")
        ks.error_code = _t(r.get("error_code"))
        ks.error_message_resumida = _t(r.get("error_message_resumida"))
        ks.tested_at = _t(r.get("tested_at"))
        if st == "ok":
            ks.eligible_ok = True
            ks.cooldown_until = ""
            ks.cooldown_until_epoch = 0
        elif st in {"invalid", "permission_denied"}:
            ks.eligible_ok = False
        elif st == "quota_exhausted":
            # quota não invalida a chave; mantém eligible_ok e respeita cooldown do arquivo
            ks.eligible_ok = True
        else:
            # unknown/unavailable: não derrubar elegibilidade automaticamente
            ks.eligible_ok = bool(ks.eligible_ok)

    km.save_status()
    return True


def _t(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def ensure_dirs(base_out: Path) -> Dict[str, Path]:
    review = base_out / "exports" / "review"
    logs = base_out / "logs"
    review.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)
    return {"review": review, "logs": logs}


def list_input_files(input_dir: Path) -> List[Path]:
    files: List[Path] = []
    for p in sorted(input_dir.rglob("*")):
        if p.is_file() and p.suffix.lower() in ALLOWED_EXTS:
            files.append(p)
    return files


def pdf_text_extract(path: Path) -> str:
    try:
        import fitz  # type: ignore
    except Exception:
        return ""
    try:
        doc = fitz.open(str(path))
        text = ""
        # poucas páginas pra ser barato
        for i in range(min(2, doc.page_count)):
            text += "\n" + (doc.load_page(i).get_text("text") or "")
        doc.close()
        return text.strip()
    except Exception:
        return ""


def pdf_render_first_page(path: Path, *, dpi: int) -> Optional[Image.Image]:
    try:
        import fitz  # type: ignore
    except Exception:
        return None
    try:
        doc = fitz.open(str(path))
        page = doc.load_page(0)
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        doc.close()
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        return img
    except Exception:
        return None


def preprocess_image(img: Image.Image) -> Image.Image:
    # pré-processamento seguro (leve)
    g = ImageOps.grayscale(img)
    # autocontrast melhora OCR
    g = ImageOps.autocontrast(g)
    return g


def _optimize_image_for_gemini(
    img: Image.Image,
    *,
    max_side_px: int = 1280,
    jpeg_quality: int = 85,
) -> Tuple[bytes, str]:
    """
    FASE 7C — otimiza a imagem antes do upload Gemini (economia de tokens/banda).

    Regras desta função (nada além disto):
    - mantém aspect ratio: lado maior <= ``max_side_px`` (default 1280).
    - JPEG ``quality=jpeg_quality`` (default 85), ``optimize=True``, não-progressivo.
    - converte para RGB quando necessário (JPEG exige RGB no PIL).
    - NÃO modifica o ``img`` original; usa ``Image.resize`` que devolve nova imagem.

    Retorna ``(bytes, mime_type='image/jpeg')``.

    Notas operacionais (importantes para o pipeline):
    - O cache de respostas usa ``hashlib.sha256(raw_b)``; ao trocar de PNG
      para JPEG redimensionado, o digest muda e respostas em cache PNG não
      terão hit (esperado e seguro — não corrompe artefactos antigos).
    - O contrato JSON do Gemini permanece intacto; apenas o transporte muda.
    - Em fichas A4 a 180 DPI (~1493x2110) o original cai para ~907x1280;
      legibilidade verificada para chapa/tabela. Se a tabela tiver texto
      muito pequeno, considerar passar ``--gemini-image-max-side-px 1600``.
    """
    work = img if img.mode == "RGB" else img.convert("RGB")
    w, h = work.size
    long_side = max(w, h)
    if long_side > max_side_px:
        scale = float(max_side_px) / float(long_side)
        new_w = max(1, int(round(w * scale)))
        new_h = max(1, int(round(h * scale)))
        work = work.resize((new_w, new_h), Image.LANCZOS)
    buf = io.BytesIO()
    work.save(buf, format="JPEG", quality=int(jpeg_quality), optimize=True, progressive=False)
    return buf.getvalue(), "image/jpeg"


def ocr_with_tesseract(img: Image.Image) -> Tuple[str, float]:
    try:
        import pytesseract  # type: ignore
    except Exception:
        return "", 0.0
    try:
        text = pytesseract.image_to_string(img, lang="por")
        return (text or "").strip(), 0.55 if text else 0.0
    except Exception:
        return "", 0.0


def ocr_with_easyocr(img: Image.Image) -> Tuple[str, float]:
    try:
        reader = _get_easyocr_reader()
        result = reader.readtext(img, detail=0)
        text = " ".join([str(x) for x in result if str(x).strip()])
        return text.strip(), 0.65 if text else 0.0
    except Exception:
        return "", 0.0


def _ocr_score(text: str, conf: float) -> Tuple[int, float]:
    return (len((text or "").strip()), float(conf or 0.0))


def run_local_ocr_on_image(img: Image.Image) -> Tuple[str, float, str]:
    """Tesseract primeiro (mais leve); EasyOCR como reforço. Retorna (texto, conf, fonte)."""
    img_p = preprocess_image(img)
    t_te, c_te = ocr_with_tesseract(img_p)
    t_ez, c_ez = ocr_with_easyocr(img_p)
    if _ocr_score(t_te, c_te) >= _ocr_score(t_ez, c_ez) and t_te.strip():
        return t_te.strip(), float(c_te or 0.55), "tesseract"
    if t_ez.strip():
        return t_ez.strip(), float(c_ez or 0.65), "easyocr"
    if t_te.strip():
        return t_te.strip(), float(c_te or 0.55), "tesseract"
    return "", 0.0, "local"


def normalize_tipo_motor(raw: str) -> str:
    t = _t(raw).lower()
    if "trif" in t or "3" in t and "fase" in t:
        return "trifasico"
    if "mono" in t or "1" in t and "fase" in t:
        return "monofasico"
    if t in {"monofasico", "trifasico"}:
        return t
    if not t:
        return "desconhecido"
    return "outro"


def _extract_first(pattern: str, text: str, flags: int = re.IGNORECASE) -> str:
    m = re.search(pattern, text or "", flags=flags)
    return m.group(1).strip() if m else ""


def parse_fields_from_text(text: str) -> Dict[str, str]:
    """
    Extração local heurística (conservadora).
    """
    t = (text or "").replace("\n", " ")
    t = re.sub(r"\s+", " ", t).strip()
    out: Dict[str, str] = {}

    # tipo motor
    if re.search(r"\btrif[aá]sico\b|\btri\s*f[aá]sico\b|\b3\s*~\b", t, flags=re.IGNORECASE):
        out["tipo_motor"] = "trifasico"
    elif re.search(r"\bmonof[aá]sico\b|\bmono\s*f[aá]sico\b|\b1\s*~\b", t, flags=re.IGNORECASE):
        out["tipo_motor"] = "monofasico"
    else:
        out["tipo_motor"] = "desconhecido"

    # tensao
    out["tensao"] = _extract_first(r"(\d{2,4}\s*/\s*\d{2,4}\s*V?)", t) or _extract_first(r"\b(\d{2,4})\s*V\b", t)
    # rpm
    out["rpm"] = _extract_first(r"\b(\d{3,5})\s*RPM\b", t)
    # polos
    out["polos"] = _extract_first(r"\b(\d)\s*P\b", t) or _extract_first(r"\b(\d)\s*POLOS?\b", t)
    # potencia cv
    out["potencia_cv"] = _extract_first(r"(\d+(?:[.,]\d+)?)\s*CV\b", t)

    # capacitor
    out["capacitor"] = _extract_first(r"(\d+(?:[.,]\d+)?)\s*U?F(?:\s*/\s*\d+\s*V(?:AC|DC)?)?", t)

    # padrões de fio e passo/espiras (muito conservador)
    out["fio_principal"] = _extract_first(r"\b(\d+\s*[xX]\s*\d+(?:[.,]\d+)?)\b", t).replace(" ", "").upper()
    out["fio_auxiliar"] = ""

    # passo: tenta capturar "1:4:6" ou sequências separadas
    passo = _extract_first(r"\b(\d{1,2}\s*[:;/\-]\s*\d{1,2}(?:\s*[:;/\-]\s*\d{1,2}){1,5})\b", t)
    passo = re.sub(r"\s+", "", passo).replace(";", ":").replace("/", ":").replace("-", ":")
    out["passo_principal"] = passo
    out["passo_auxiliar"] = ""

    # espiras: sequências 2+ números (ex: 57:114, 24:40:48)
    esp = _extract_first(r"\b(\d{1,3}(?:\s*[:+]\s*\d{1,3})+)\b", t)
    esp = re.sub(r"\s+", "", esp).replace("+", ":")
    out["espiras_principal"] = esp
    out["espiras_auxiliar"] = ""

    return out


def required_fields_status(data: Dict[str, str]) -> Tuple[str, List[str]]:
    tipo = normalize_tipo_motor(_t(data.get("tipo_motor")))
    missing: List[str] = []

    def need(k: str) -> None:
        if not _t(data.get(k)):
            missing.append(k)

    if tipo == "monofasico":
        need("tipo_motor")
        need("tensao")
        need("fio_principal")
        need("espiras_principal")
        need("passo_principal")
        need("fio_auxiliar")
        need("espiras_auxiliar")
        need("passo_auxiliar")
    elif tipo == "trifasico":
        need("tipo_motor")
        need("tensao")
        need("fio_principal")
        need("espiras_principal")
        need("passo_principal")
    else:
        # desconhecido: mínimo para revisão
        need("tensao")

    return tipo, missing


def _apply_gemini_data_to_parsed(parsed: Dict[str, Any], g: Dict[str, Any]) -> float:
    parsed["tipo_motor"] = normalize_tipo_motor(_t(g.get("tipo_motor") or parsed.get("tipo_motor")))
    parsed["potencia_cv"] = _t(g.get("potencia_cv") or parsed.get("potencia_cv"))
    parsed["rpm"] = _t(g.get("rpm") or parsed.get("rpm"))
    parsed["tensao"] = _t(g.get("tensao") or parsed.get("tensao"))
    parsed["polos"] = _t(g.get("polos") or parsed.get("polos"))
    parsed["frequencia"] = _t(g.get("frequencia") or parsed.get("frequencia"))
    parsed["carcaca"] = _t(g.get("carcaca") or parsed.get("carcaca"))
    parsed["ranhuras"] = _t(g.get("ranhuras") or parsed.get("ranhuras"))
    parsed["pacote_mm"] = _t(g.get("pacote_mm") or parsed.get("pacote_mm"))
    parsed["diametro_mm"] = _t(g.get("diametro_mm") or parsed.get("diametro_mm"))
    parsed["capacitor"] = _t(g.get("capacitor") or parsed.get("capacitor"))
    pr = g.get("principal") or {}
    ax = g.get("auxiliar") or {}
    if isinstance(pr, dict):
        parsed["fio_principal"] = _t(pr.get("fio") or parsed.get("fio_principal"))
        parsed["espiras_principal"] = _t(pr.get("espiras") or parsed.get("espiras_principal"))
        parsed["passo_principal"] = _t(pr.get("passo") or parsed.get("passo_principal"))
    if isinstance(ax, dict):
        parsed["fio_auxiliar"] = _t(ax.get("fio") or parsed.get("fio_auxiliar"))
        parsed["espiras_auxiliar"] = _t(ax.get("espiras") or parsed.get("espiras_auxiliar"))
        parsed["passo_auxiliar"] = _t(ax.get("passo") or parsed.get("passo_auxiliar"))
    return _safe_float(g.get("confianca"), 0.70)


def decide_status(
    local_conf: float,
    missing: List[str],
    tipo: str,
    used_gemini: bool,
    gem_conf: float,
    *,
    gemini_failed: bool = False,
    gemini_error: str = "",
    gemini_error_status: str = "",
    pause_motivo: str = "",
) -> Tuple[str, str, float, bool]:
    if pause_motivo:
        if str(pause_motivo).strip() == "limite_chamadas":
            return "PAUSA_LIMITE_CHAMADAS", "infra:max_gemini_calls_atingido", local_conf, True
        return "PAUSA_LOTE_INTERROMPIDO", pause_motivo, local_conf, True

    motivos = []
    if missing:
        motivos.append("faltando_obrigatorio")
    if local_conf < 0.55:
        motivos.append("baixa_confianca_local")
    ge = redact_secrets_in_text((gemini_error or "").strip())
    if gemini_failed and ge:
        motivos.append(f"gemini_falhou:{ge[:120]}")
    motivo = ";".join(motivos)

    if not used_gemini:
        if not missing and local_conf >= 0.75:
            return "VERDE_AUTO_LOCAL", motivo, local_conf, False
        if local_conf >= 0.55:
            return "AMARELO_REVISAR", motivo, local_conf, True
        return "VERMELHO_REVISAR", motivo, local_conf, True

    if used_gemini and gemini_failed:
        if (gemini_error_status or "").strip().startswith("no_keys") or _is_infra_gemini_error(
            gemini_error_status, gemini_error or ""
        ):
            return "PAUSA_INFRA_SEM_CHAVE", "infra:gemini_indisponivel_ou_quota", max(local_conf, gem_conf), True
        conf = max(local_conf, gem_conf)
        if not missing and local_conf >= 0.75:
            return "VERDE_AUTO_LOCAL", motivo, local_conf, False
        if conf >= 0.55:
            return "AMARELO_REVISAR", motivo, conf, True
        return "VERMELHO_REVISAR", motivo, conf, True

    conf = max(local_conf, gem_conf)
    if not missing and conf >= 0.75:
        return "VERDE_AUTO_GEMINI", motivo, conf, False
    if conf >= 0.55:
        return "AMARELO_REVISAR", motivo, conf, True
    return "VERMELHO_REVISAR", motivo, conf, True


def load_checkpoint(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {"done": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"done": {}}


def save_checkpoint(path: Path, state: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def write_jsonl(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def _load_gemini_response_cache(cache_dir: Path, digest: str) -> Optional[Dict[str, Any]]:
    if not digest:
        return None
    p = cache_dir / f"{digest}.json"
    if not p.exists():
        return None
    try:
        raw = json.loads(p.read_text(encoding="utf-8"))
        data = raw.get("data") if isinstance(raw, dict) else None
        if isinstance(data, dict):
            return data
    except Exception:
        return None
    return None


def _save_gemini_response_cache(cache_dir: Path, digest: str, data: Dict[str, Any]) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = cache_dir / f"{digest}.json"
    payload = {"data": data, "saved_at": _now_str()}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _list_cache_lookup_dirs(
    logs_dir: Path,
    output_tag: str,
    extra: List[str],
) -> List[Path]:
    out: List[Path] = [logs_dir / "gemini_response_cache"]
    if output_tag:
        out.append(logs_dir / f"{output_tag}_gemini_cache")
    for e in extra:
        t = str(e or "").strip()
        if t:
            out.append(Path(t).expanduser().resolve())
    return out


def _load_gemini_cache_multi(
    dirs: List[Path], digest: str
) -> Tuple[Optional[Dict[str, Any]], Optional[Path]]:
    for d in dirs:
        if d is None:
            continue
        data = _load_gemini_response_cache(d, digest)
        if data is not None:
            return data, d
    return None, None


def _is_infra_gemini_error(gemini_error_status: str, gemini_error: str) -> bool:
    s = f"{gemini_error_status} {gemini_error}".lower()
    if (gemini_error_status or "").strip().startswith("no_keys"):
        return True
    for n in (
        "no_keys",
        "nenhuma chave",
        "429",
        "quota",
        "resource_exhausted",
        "resource exhausted",
        "rate",
        "exhausted",
        "billing",
    ):
        if n in s:
            return True
    return False


def _monorepo_root() -> Path:
    return REPO_ROOT.parent


def resolve_output_paths(
    review_dir: Path,
    logs_dir: Path,
    output_tag: str,
) -> Dict[str, Path]:
    """Ficheiros com prefixo dedicado (não sobrescreve bundle_review_candidates)."""
    t = output_tag.strip()
    if not t:
        raise ValueError("output_tag vazio")
    return {
        "csv": review_dir / f"{t}_candidates.csv",
        "jsonl": review_dir / f"{t}_candidates.jsonl",
        "summary_md": review_dir / f"{t}_summary.md",
        "checkpoint": logs_dir / f"{t}_checkpoint.json",
        "log": logs_dir / f"{t}.log",
    }


def _norm_arq(s: str) -> str:
    return s.replace("/", "\\").strip().lower()


def _load_processed_index_map(path: Path) -> Dict[str, Dict[str, str]]:
    if not path.is_file():
        return {}
    m: Dict[str, Dict[str, str]] = {}
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            k = _norm_arq(_t(row.get("image_path") or ""))
            if k:
                m[k] = {a: _t(b) for a, b in row.items()}
    return m


def load_work_queue_csv(
    wq: Path,
    base_dir: Path,
    *,
    only_reprocess: bool,
    only_new: bool,
    no_reprocess_manual: bool,
) -> Tuple[List[Path], Dict[str, str]]:
    if not wq.is_file():
        raise FileNotFoundError(f"work queue: {wq}")
    if not base_dir.is_dir():
        raise NotADirectoryError(f"images base: {base_dir}")
    out: List[Path] = []
    qt_by_rel: Dict[str, str] = {}
    allowed_newish = (
        "NEW_UNPROCESSED",
        "NEW_UNPROCESSED_PASS1",
        "PENDENCY_RETRY_PASS1",
        "PENDENCY_MANUAL_PASS1",
        "PENDENCY_PRIOR_QUEUE",
        "PENDENCY_INFRA_RETRY",
        "PENDENCY_JSON_PARSE_RETRY",
    )
    with open(wq, "r", encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            qt = _t(row.get("queue_type") or "")
            if no_reprocess_manual and qt not in ("REPROCESS_QUOTA", *allowed_newish):
                continue
            if only_reprocess and qt != "REPROCESS_QUOTA":
                continue
            if only_new and qt not in allowed_newish:
                continue
            rel = _t(row.get("arquivo_rel") or row.get("arquivo") or "")
            if not rel:
                continue
            rel = rel.replace("/", "\\")
            ap = (base_dir / rel).resolve()
            if not ap.is_file():
                continue
            out.append(ap)
            qt_by_rel[_norm_arq(rel)] = qt
    return out, qt_by_rel


def load_paths_from_manifest_csv(manifest_csv: Path, base_dir: Path) -> List[Path]:
    if not manifest_csv.exists():
        raise FileNotFoundError(f"Manifest inexistente: {manifest_csv}")
    if not base_dir.is_dir():
        raise NotADirectoryError(f"Base_dir não é pasta: {base_dir}")

    with open(manifest_csv, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("CSV do manifest sem cabeçalho.")

        col: Optional[str] = None
        if "arquivo" in reader.fieldnames:
            col = "arquivo"
        elif "arquivo_rel" in reader.fieldnames:
            col = "arquivo_rel"
        else:
            for fn in reader.fieldnames:
                lfn = (fn or "").lower()
                if "caminho" in lfn or "path" in lfn or "file" in lfn or "imagem" in lfn:
                    col = fn
                    break
        if not col:
            raise ValueError(
                f"Não encontrei coluna de caminho (esperado: 'arquivo' ou 'arquivo_rel'). Colunas: {reader.fieldnames}"
            )

        paths: List[Path] = []
        seen: Set[str] = set()
        for row in reader:
            rel = _t(row.get(col))
            if not rel:
                continue
            rel = rel.replace("/", "\\")
            abs_path = (base_dir / rel).resolve()
            if not abs_path.is_file():
                raise FileNotFoundError(f"Arquivo não existe para manifest [{col}]={rel!r} -> {abs_path}")
            key = str(abs_path).lower()
            if key not in seen:
                seen.add(key)
                paths.append(abs_path)

        if not paths:
            raise ValueError(f"Manifest sem linhas válidas com ficheiros existentes ({col}).")

        paths.sort(key=lambda p: str(p).lower())
        return paths


def main() -> int:
    ap = argparse.ArgumentParser(description="Extrai dados de rebobinagem (local OCR primeiro; Gemini fallback opcional).")
    ap.add_argument(
        "--input",
        default="",
        help="Pasta com PDFs/imagens (se não usar --manifest-csv).",
    )
    ap.add_argument(
        "--manifest-csv",
        default="",
        help="CSV com coluna 'arquivo' (caminho relativo) — reprocessa só essa fila; requer --manifest-base-dir.",
    )
    ap.add_argument(
        "--manifest-base-dir",
        default="",
        help="Pasta raiz comum para caminhos do manifest (ex.: .../chatgpt_visual_batches).",
    )
    ap.add_argument(
        "--output-tag",
        default="",
        help="Prefixo de ficheiros (candidatos, jsonl, summary, checkpoint, log) em exports/review e logs/.",
    )
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--emit-schema-sidecar",
        action="store_true",
        help="FASE 5B: adiciona objeto schema_sidecar apenas no JSONL por linha (opt-in; CSV inalterado).",
    )
    ap.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Máx. ficheiros: padrão 20 se omitido. Com work queue, 0 = sem teto (cuidado com custo).",
    )
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--no-gemini", action="store_true")
    ap.add_argument("--env-file", default="", help="Caminho do .env a usar para --only-unique-keys.")
    ap.add_argument(
        "--only-unique-keys",
        action="store_true",
        help="Deduplica por SHA-256 e usa aliases UQ_* a partir de --env-file (alinha com check --only-unique).",
    )
    ap.add_argument(
        "--refresh-key-status-before-run",
        action="store_true",
        help="Antes do lote, faz ping barato em todas as chaves carregadas e atualiza logs/gemini_keys_status.json.",
    )
    ap.add_argument(
        "--key-rotation-strategy",
        default="",
        help="Estratégia de rotação do KeyManager: round_robin | least_recently_used | random. Padrão: round_robin quando --only-unique-keys.",
    )
    ap.add_argument(
        "--max-calls-per-key-per-run",
        type=int,
        default=0,
        help="Limite de uso por chave nesta execução (0 = sem limite). Ajuda a distribuir quota.",
    )
    ap.add_argument(
        "--quota-friendly",
        action="store_true",
        help="Modo ultra econômico: evita queimar chaves em caso de quota global (sleep>=15, max calls baixo, para cedo em 429).",
    )
    ap.add_argument(
        "--gemini-model-default",
        dest="gemini_model_default_cli",
        default="",
        metavar="MODEL",
        help="Opcional: força modelo primário nesta execução (ex.: gemini-2.5-flash). Sobrepõe GEMINI_MODEL_DEFAULT quando não vazio.",
    )
    ap.add_argument(
        "--gemini-model-fallback",
        dest="gemini_model_fallback_cli",
        default="",
        metavar="MODEL",
        help="Opcional: força modelo de fallback nesta execução quando não vazio.",
    )
    ap.add_argument(
        "--gemini-allow-non-ok-keys",
        action="store_true",
        help="Permite chaves sem status 'ok' no JSON (não recomendado). Padrão: só chaves OK.",
    )
    ap.add_argument("--gemini-only-failed", action="store_true")
    ap.add_argument("--min-confidence", type=float, default=0.55)
    ap.add_argument("--output-dir", default=str(REPO_ROOT))
    ap.add_argument(
        "--sleep-seconds",
        type=float,
        default=0.2,
        help="Pausa após cada chamada Gemini (API); também influencia backoff interno do fallback.",
    )
    ap.add_argument(
        "--stop-when-no-keys",
        action="store_true",
        help="Sem chave disponível: interrompe o lote sem gravar linha (ficheiros restantes ficam para próxima execução).",
    )
    ap.add_argument(
        "--max-gemini-calls",
        type=int,
        default=None,
        help=(
            "Limite de chamadas Gemini à API nesta execução. Omitido = sem limite. "
            "0 = nenhuma chamada à API (cache ainda pode ser usado). Cache não conta."
        ),
    )
    ap.add_argument(
        "--gemini-response-cache-dir",
        default="",
        help="Pasta para cache SHA256→JSON das respostas Gemini. Vazio: logs/<tag>_gemini_cache ou logs/gemini_response_cache.",
    )
    # FASE 7C — controlo do payload otimizado (JPEG redimensionado).
    ap.add_argument(
        "--gemini-image-max-side-px",
        type=int,
        default=1280,
        help=(
            "FASE 7C: lado maior (px) da imagem enviada ao Gemini. Default 1280. "
            "Mantém aspect ratio; só faz downscale se exceder. Para chapas com texto muito pequeno, "
            "considerar 1600."
        ),
    )
    ap.add_argument(
        "--gemini-image-jpeg-quality",
        type=int,
        default=85,
        help="FASE 7C: qualidade JPEG (default 85). Faixa segura para chapas técnicas: 80–90.",
    )
    ap.add_argument(
        "--work-queue-csv",
        default="",
        help="Fila (ex. next_gemini_work_queue.csv) com coluna queue_type; requer --output-tag e --images-base-dir ou padrão chatgpt_visual_batches.",
    )
    ap.add_argument(
        "--images-base-dir",
        default="",
        help="Raiz para arquivo_rel da work queue / ignorado sem --work-queue-csv.",
    )
    ap.add_argument(
        "--reuse-cache",
        action="store_true",
        help="Le cache em logs/gemini_response_cache, logs/<tag>_gemini_cache e --cache-dir antes da API.",
    )
    ap.add_argument(
        "--cache-dir",
        action="append",
        default=[],
        metavar="DIR",
        help="Pastas extra de cache JSON (repetível). Com --reuse-cache entram na pesquisa.",
    )
    ap.add_argument(
        "--processed-index-csv",
        default="",
        help="processed_image_index.csv para --skip-existing-green / --skip-existing-success.",
    )
    ap.add_argument("--skip-existing-green", action="store_true", help="Saltar imagens já VERDE_SEGURO no index.")
    ap.add_argument(
        "--skip-existing-success",
        action="store_true",
        help="Saltar verdes / alertas / pipeline verde segundo index.",
    )
    ap.add_argument("--only-reprocess-quota", action="store_true", help="Só linhas REPROCESS_QUOTA da work queue.")
    ap.add_argument("--only-new-unprocessed", action="store_true", help="Só linhas NEW_UNPROCESSED da work queue.")
    ap.add_argument(
        "--force-gemini-on-retry",
        action="store_true",
        help="Obrigatório com --work-queue-csv: força tentativa Gemini (ignora pdf_text/confiança). "
        "Respeita --reuse-cache, --max-gemini-calls e --stop-when-no-keys.",
    )
    ap.add_argument(
        "--gemini-detective-mode",
        action="store_true",
        help="Sufixo 'Modo Detetive' ao prompt Gemini: máximo técnico legível, marca duvidas em campos_incertos/observações (auditoria admin). "
        "Não misturar com --reuse-cache (cache não inclui prompt).",
    )
    args = ap.parse_args()

    # quota-friendly defaults (se o utilizador não definiu explicitamente)
    if getattr(args, "gemini_detective_mode", False) and getattr(args, "reuse_cache", False):
        print(
            "*** AVISO: --gemini-detective-mode com --reuse-cache pode devolver JSON antigo "
            "(cache SHA-only). Preferir SEM --reuse-cache neste lote. ***",
            file=sys.stderr,
        )

    if args.quota_friendly:
        # sleep mínimo
        if float(getattr(args, "sleep_seconds", 0.0) or 0.0) < 15.0:
            args.sleep_seconds = 15.0
        apply_quota_friendly_max_gemini_cap(args)
        # max per key
        if int(getattr(args, "max_calls_per_key_per_run", 0) or 0) == 0:
            args.max_calls_per_key_per_run = 1
    limit_user_specified = args.limit is not None
    if args.limit is None:
        args.limit = 20

    # carregar .env (se existir) — nunca ler chaves de CSV
    _load_dotenv_candidates()

    manifest_csv = _t(args.manifest_csv)
    output_tag = _t(args.output_tag)
    work_queue_csv = _t(args.work_queue_csv)
    default_bases = _monorepo_root() / "audit_reports" / "chatgpt_visual_batches"
    manifest_mode = bool(manifest_csv)
    work_queue_mode = bool(work_queue_csv)
    wq_qt_by_rel: Dict[str, str] = {}

    if bool(getattr(args, "force_gemini_on_retry", False)) and not work_queue_mode:
        print("ERRO: --force-gemini-on-retry requer --work-queue-csv.", file=sys.stderr)
        return 2

    if work_queue_mode:
        wq_path = Path(work_queue_csv).expanduser().resolve()
        ib = _t(args.images_base_dir)
        base_dir = Path(ib).expanduser().resolve() if ib else default_bases.resolve()
        if not base_dir.is_dir():
            print(f"ERRO: --images-base-dir não é pasta: {base_dir}", file=sys.stderr)
            return 2
        if not output_tag:
            print("ERRO: use --output-tag com --work-queue-csv.", file=sys.stderr)
            return 2
        if not limit_user_specified:
            print(
                "\n*** ATENCAO (work queue): nao passou --limit; a usar o default 20 ficheiros. "
                "Para 100, use --limit 100. Para toda a fila, use --limit 0. ***\n",
                file=sys.stderr,
            )
        try:
            batch, wq_qt_by_rel = load_work_queue_csv(
                wq_path,
                base_dir,
                only_reprocess=bool(args.only_reprocess_quota),
                only_new=bool(args.only_new_unprocessed),
                no_reprocess_manual=True,
            )
        except (OSError, ValueError) as exc:
            print(f"ERRO work queue: {exc}", file=sys.stderr)
            return 2
        lim = max(0, int(args.limit))
        if lim:
            batch = batch[:lim]
        input_dir = base_dir
        ordinal_base = 0
        manifest_mode = False
    elif manifest_mode:
        mb = _t(args.manifest_base_dir)
        base_dir = Path(mb).expanduser().resolve() if mb else default_bases.resolve()
        if not base_dir.is_dir():
            print(f"ERRO: manifest-base-dir não é pasta: {base_dir}", file=sys.stderr)
            return 2
        if not output_tag:
            print(
                "ERRO: use --output-tag (ex: reprocess_no_keys_lote_100) com --manifest-csv para não misturar com bundle_review_candidates.",
                file=sys.stderr,
            )
            return 2
        try:
            batch = load_paths_from_manifest_csv(Path(manifest_csv).expanduser().resolve(), base_dir)
        except (OSError, ValueError) as exc:
            print(f"ERRO manifest: {exc}", file=sys.stderr)
            return 2
        input_dir = base_dir
        ordinal_base = 0
    else:
        if not _t(args.input):
            print("ERRO: defina --input, --manifest-csv ou --work-queue-csv.", file=sys.stderr)
            return 2
        input_dir = Path(os.path.abspath(args.input))
        if not input_dir.is_dir():
            print(f"ERRO: input não é pasta: {input_dir}", file=sys.stderr)
            return 2
        offset = max(0, int(args.offset))
        limit = max(0, int(args.limit))
        all_files = list_input_files(input_dir)
        batch = all_files[offset : offset + limit] if limit else all_files[offset:]
        ordinal_base = offset

    out_base = Path(os.path.abspath(args.output_dir))
    paths = ensure_dirs(out_base)
    review_dir = paths["review"]
    logs_dir = paths["logs"]

    status_path = logs_dir / "gemini_keys_status.json"

    if output_tag:
        opaths = resolve_output_paths(review_dir, logs_dir, output_tag)
        csv_path = opaths["csv"]
        jsonl_path = opaths["jsonl"]
        summary_md = opaths["summary_md"]
        checkpoint_path = opaths["checkpoint"]
        log_path = opaths["log"]
    else:
        log_path = logs_dir / "rebobinagem_batch.log"
        checkpoint_path = logs_dir / "rebobinagem_batch_checkpoint.json"
        csv_path = review_dir / "bundle_review_candidates.csv"
        jsonl_path = review_dir / "bundle_review_candidates.jsonl"
        summary_md = review_dir / "bundle_review_summary.md"

    gcache_arg = _t(args.gemini_response_cache_dir)
    if gcache_arg:
        cache_root = Path(gcache_arg).expanduser().resolve()
    else:
        cache_root = logs_dir / (f"{output_tag}_gemini_cache" if output_tag else "gemini_response_cache")
    extra_cd = [str(x) for x in (args.cache_dir or []) if str(x).strip()]
    if args.reuse_cache:
        cache_lookup_dirs = _list_cache_lookup_dirs(logs_dir, output_tag, extra_cd)
        # gravar sempre na pasta principal do extract (tag ou global)
        try:
            cache_lookup_dirs.remove(cache_root.resolve())
        except ValueError:
            pass
        cache_lookup_dirs.insert(0, cache_root)
    else:
        cache_lookup_dirs = [cache_root]
    index_map: Dict[str, Dict[str, str]] = {}
    if _t(args.processed_index_csv):
        index_map = _load_processed_index_map(Path(args.processed_index_csv).expanduser().resolve())

    model_default = (os.environ.get("GEMINI_MODEL_DEFAULT") or "gemini-2.5-flash").strip()
    model_fallback = (os.environ.get("GEMINI_MODEL_FALLBACK") or "gemini-2.5-flash-lite").strip()
    gemini_enabled = (not args.no_gemini) and (os.environ.get("GEMINI_ENABLED", "true").lower() in {"1", "true", "yes", "y"})
    # quota-friendly: forçar modelos econômicos (sem preview) se não estiverem definidos no ambiente
    if args.quota_friendly:
        if not (os.environ.get("GEMINI_MODEL_DEFAULT") or "").strip():
            model_default = "gemini-2.5-flash-lite"
        if not (os.environ.get("GEMINI_MODEL_FALLBACK") or "").strip():
            model_fallback = "gemini-2.5-flash"
    if _t(getattr(args, "gemini_model_default_cli", "")):
        model_default = _t(args.gemini_model_default_cli)
    if _t(getattr(args, "gemini_model_fallback_cli", "")):
        model_fallback = _t(args.gemini_model_fallback_cli)

    km = GeminiKeyManager(status_path=str(status_path), model_default=model_default, enabled=gemini_enabled)
    if args.only_unique_keys:
        env_file = Path(args.env_file or (REPO_ROOT / ".env")).expanduser().resolve()
        if not env_file.is_file():
            print(f"ERRO: --only-unique-keys requer --env-file existente (ou .env no repo): {env_file}", file=sys.stderr)
            return 2
        km.load_keys_from_pairs(_load_unique_keys_from_env_file(env_file))
    else:
        km.load_keys()

    if args.refresh_key_status_before_run and gemini_enabled:
        # Preferir snapshot do check (sem API) para não queimar quota em refresh.
        snap = logs_dir / "gemini_keys_check_snapshot.json"
        ok_snap = _refresh_key_status_from_snapshot(km, snap)
        if not ok_snap:
            # quota-friendly: nunca refresh via API
            if not args.quota_friendly:
                _refresh_key_status_before_run(km, sleep_seconds=float(args.sleep_seconds))

    # configurar rotação
    rot = _t(args.key_rotation_strategy)
    if not rot and args.only_unique_keys:
        rot = "round_robin"
    max_per_key = int(args.max_calls_per_key_per_run or 0)
    if args.quota_friendly and max_per_key <= 0:
        max_per_key = 1
    km.configure_rotation(strategy=rot or "random", max_calls_per_key_per_run=max_per_key)
    gem: Optional[Any] = None
    if gemini_enabled:
        from services.gemini_ocr_fallback import (  # noqa: E402 — lazy quando Gemini desligado
            DETECTIVE_MODE_PROMPT_SUFFIX,
            GeminiOcrFallback,
        )

        detective_suffix = DETECTIVE_MODE_PROMPT_SUFFIX if bool(getattr(args, "gemini_detective_mode", False)) else ""

        gem = GeminiOcrFallback(
            key_manager=km,
            model_default=model_default,
            model_fallback=model_fallback,
            enabled=True,
            max_attempts_per_image=2,
            require_status_ok=not bool(args.gemini_allow_non_ok_keys),
            quota_friendly=bool(args.quota_friendly),
            extra_prompt_suffix=detective_suffix,
        )

    checkpoint = load_checkpoint(checkpoint_path)
    done = checkpoint.get("done") or {}

    csv_cols = [
        "id_local",
        "arquivo",
        "lote",
        "ordem",
        "tipo_motor",
        "potencia_cv",
        "rpm",
        "tensao",
        "polos",
        "frequencia",
        "carcaca",
        "ranhuras",
        "pacote_mm",
        "diametro_mm",
        "capacitor",
        "fio_principal",
        "espiras_principal",
        "passo_principal",
        "fio_auxiliar",
        "espiras_auxiliar",
        "passo_auxiliar",
        "status_revisao",
        "motivos_bloqueio",
        "fonte_extracao",
        "confianca",
        "precisa_humano",
    ]

    if output_tag and args.force:
        for p in (csv_path, jsonl_path):
            if p.exists():
                p.unlink()
        if checkpoint_path.exists():
            checkpoint_path.unlink()
        checkpoint = {"done": {}}
        done = {}

    if not csv_path.exists():
        with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=csv_cols)
            w.writeheader()

    stats: Dict[str, Any] = {
        "processed": 0,
        "local_ocr_attempts": 0,
        "local_ocr_files": 0,
        "gemini_files": 0,
        "gemini_api_calls": 0,
        "gemini_cache_hits": 0,
        "gemini_quota_429": 0,
        "gemini_quota_consecutive": 0,
        "cache_lookup_paths": len(cache_lookup_dirs),
        "skipped_existing_green": 0,
        "skipped_existing_success": 0,
        "VERDE_AUTO_LOCAL": 0,
        "VERDE_AUTO_GEMINI": 0,
        "AMARELO_REVISAR": 0,
        "VERMELHO_REVISAR": 0,
        "PAUSA_INFRA_SEM_CHAVE": 0,
        "PAUSA_LOTE_INTERROMPIDO": 0,
        "PAUSA_LIMITE_CHAMADAS": 0,
        "PAUSA_TODAS_CHAVES_COOLDOWN": 0,
        "PAUSA_LIMITE_POR_CHAVE": 0,
        "PAUSA_SEM_CHAVE_OK": 0,
    }
    top_motivos: Dict[str, int] = {}
    problematic: List[Dict[str, Any]] = []
    keys_used: Dict[str, int] = {}
    good_examples: List[Dict[str, str]] = []
    bad_examples: List[Dict[str, str]] = []
    gemini_api_calls = 0
    batch_stop_reason = ""

    tag_note = ""
    if work_queue_mode:
        tag_note = f"work_queue={work_queue_csv}"
    elif manifest_mode:
        tag_note = f"manifest={manifest_csv}"
    with open(log_path, "a", encoding="utf-8") as lf:
        lf.write(
            f"[{_now_str()}] START dry_run={args.dry_run} input={input_dir} "
            f"batch={len(batch)} output_tag={output_tag or 'default'} {tag_note}\n"
        )

    for idx, path in enumerate(batch, start=1):
        id_local = f"{ordinal_base + idx:06d}"
        rel = str(path.relative_to(input_dir))

        if (not args.force) and rel in done:
            prev = done.get(rel)
            pstatus = _t(prev.get("status")) if isinstance(prev, dict) else ""
            if pstatus == "PAUSA_INFRA_SEM_CHAVE":
                pass
            else:
                continue

        if index_map:
            pr = index_map.get(_norm_arq(rel))
            if pr:
                jv = _t(pr.get("ja_deu_verde_seguro", "")).lower()
                if args.skip_existing_green and jv in ("1", "true", "yes", "sim"):
                    stats["skipped_existing_green"] += 1
                    continue
                if args.skip_existing_success:
                    ms = _t(pr.get("melhor_status", "")).upper()
                    if jv in ("1", "true", "yes", "sim") or ms in (
                        "VERDE_COM_ALERTA",
                        "VERDE_SEGURO",
                        "VERDE_AUTO_GEMINI",
                        "VERDE_AUTO_LOCAL",
                    ):
                        stats["skipped_existing_success"] += 1
                        continue

        local_text = ""
        local_conf = 0.0
        source = "local"
        primary_local_source = "none"
        used_gemini = False
        gemini_failed = False
        gemini_error = ""
        gem_conf = 0.0
        gem_info = {"key_alias": "", "model": ""}
        gemini_payload: Optional[Dict[str, Any]] = None

        img: Optional[Image.Image] = None

        # 1) PDF: texto embutido primeiro
        if path.suffix.lower() == ".pdf":
            stats["local_ocr_attempts"] += 1
            local_text = pdf_text_extract(path)
            if local_text:
                local_conf = 0.72
                source = "pdf_text"
                primary_local_source = "pdf_text"

        # 2) Imagem (arquivo imagem ou render do PDF): OCR local (Tesseract → EasyOCR)
        if not local_text:
            if path.suffix.lower() == ".pdf":
                img = pdf_render_first_page(path, dpi=180)
            else:
                try:
                    img = Image.open(path)
                    img = img.convert("RGB")
                except Exception:
                    img = None

            if img is not None:
                stats["local_ocr_attempts"] += 1
                local_text, local_conf, source = run_local_ocr_on_image(img)
                if local_text:
                    primary_local_source = source

        if primary_local_source != "none":
            stats["local_ocr_files"] += 1

        parsed = parse_fields_from_text(local_text)
        tipo, missing = required_fields_status(parsed)

        # Gemini só se OCR/heurística local fraco ou incompleto (e houver imagem)
        should_try_gemini = gemini_enabled and (local_conf < float(args.min_confidence) or bool(missing))
        if args.gemini_only_failed:
            should_try_gemini = gemini_enabled and (bool(missing) or local_conf < float(args.min_confidence))
        if bool(getattr(args, "force_gemini_on_retry", False)) and work_queue_mode:
            should_try_gemini = bool(gemini_enabled)
        if (
            work_queue_mode
            and wq_qt_by_rel.get(_norm_arq(rel), "") == "NEW_UNPROCESSED_PASS1"
            and gemini_enabled
        ):
            should_try_gemini = True

        if args.no_gemini:
            should_try_gemini = False
        if args.dry_run:
            should_try_gemini = False

        if should_try_gemini and img is None and path.suffix.lower() == ".pdf":
            img = pdf_render_first_page(path, dpi=180)

        if should_try_gemini and img is None and path.suffix.lower() != ".pdf":
            try:
                img = Image.open(path)
                img = img.convert("RGB")
            except Exception:
                img = None

        gemini_error_status = ""
        pause_motivo = ""
        cache_hit = False
        cache_hit_dir_name = ""

        if should_try_gemini and img is not None:
            # FASE 7C: payload otimizado (JPEG q=85, lado maior 1280px configurável).
            # Reduz tokens/banda sem alterar contrato JSON, audit nem categorize.
            # mime_type acompanha o formato real produzido pelo optimizer (não fixar mais "image/png").
            raw_b, _mime_for_gemini = _optimize_image_for_gemini(
                img,
                max_side_px=int(getattr(args, "gemini_image_max_side_px", 1280) or 1280),
                jpeg_quality=int(getattr(args, "gemini_image_jpeg_quality", 85) or 85),
            )
            digest = hashlib.sha256(raw_b).hexdigest()
            if args.reuse_cache:
                cached, hit_dir = _load_gemini_cache_multi(cache_lookup_dirs, digest)
                if hit_dir is not None:
                    cache_hit_dir_name = hit_dir.name
            else:
                cached = _load_gemini_response_cache(cache_root, digest)
                if cached is not None:
                    cache_hit_dir_name = cache_root.name

            if cached is not None:
                used_gemini = True
                cache_hit = True
                stats["gemini_cache_hits"] += 1
                g = cached
                gem_info["key_alias"] = "cache"
                gem_info["model"] = "cache"
                keys_used["cache"] = keys_used.get("cache", 0) + 1
                gem_conf = _apply_gemini_data_to_parsed(parsed, g)
                gemini_payload = copy.deepcopy(g) if isinstance(g, dict) else None
                source = "gemini_cache"
            else:
                if not gemini_api_call_allowed(args, gemini_api_calls):
                    mc_disp = getattr(args, "max_gemini_calls", None)
                    pause_motivo = "limite_chamadas"
                    with open(log_path, "a", encoding="utf-8") as lf:
                        lf.write(
                            f"[{_now_str()}] interrompido: max-gemini-calls={mc_disp if mc_disp is not None else 'ilimitado'} "
                            f"api_so_far={gemini_api_calls} em {rel}\n"
                        )
                    rem = [str(batch[j].relative_to(input_dir)) for j in range(idx - 1, len(batch))]
                    qpath = review_dir / (
                        f"{output_tag}_interrupted_remaining.txt" if output_tag else "batch_interrupted_remaining.txt"
                    )
                    qpath.write_text("\n".join(rem), encoding="utf-8")
                    batch_stop_reason = "max_gemini_calls"
                elif gem is None:
                    gemini_failed = True
                    gemini_error = "gemini_client_nao_inicializado"
                else:
                    used_gemini = True
                    stats["gemini_files"] += 1
                    res = gem.extract_from_image_bytes(
                        image_bytes=raw_b,
                        mime_type=_mime_for_gemini,  # FASE 7C: image/jpeg vindo do optimizer
                        file_hint=rel,
                        sleep_between_attempts_s=float(args.sleep_seconds),
                    )
                    gemini_api_calls += 1
                    stats["gemini_api_calls"] += 1
                    time.sleep(float(args.sleep_seconds))

                    if res.ok:
                        gem_info["key_alias"] = res.key_alias
                        gem_info["model"] = res.model
                        keys_used[res.key_alias] = keys_used.get(res.key_alias, 0) + 1
                        g = res.data or {}
                        _save_gemini_response_cache(cache_root, digest, g)
                        gem_conf = _apply_gemini_data_to_parsed(parsed, g)
                        gemini_payload = copy.deepcopy(g) if isinstance(g, dict) else None
                        source = "gemini"
                    else:
                        gemini_failed = True
                        gemini_error = redact_secrets_in_text(f"{res.error_status}:{res.error_message}")[:200]
                        gemini_error_status = _t(res.error_status)
                        # quota-friendly: parar cedo em sinais fortes de quota global
                        if args.quota_friendly:
                            if _t(res.error_status) == "quota_exhausted" or "429" in _t(res.error_message):
                                stats["gemini_quota_429"] += 1
                                stats["gemini_quota_consecutive"] += 1
                            else:
                                stats["gemini_quota_consecutive"] = 0

                            # 2 quotas seguidas: parar
                            if stats["gemini_quota_consecutive"] >= 2:
                                batch_stop_reason = "PAUSA_TODAS_CHAVES_COOLDOWN"
                                break

                            # >30% chaves em cooldown: parar
                            info = km.explain_no_keys(require_status_ok=not bool(args.gemini_allow_non_ok_keys))
                            try:
                                total_loaded = int((info.get("counts") or {}).get("total_loaded") or 0)
                                cd = int((info.get("counts") or {}).get("cooldown_active") or 0)
                                if total_loaded and (cd / total_loaded) > 0.30:
                                    batch_stop_reason = "PAUSA_TODAS_CHAVES_COOLDOWN"
                                    break
                            except Exception:
                                pass
                        if _t(res.error_status).startswith("no_keys") and args.stop_when_no_keys:
                            with open(log_path, "a", encoding="utf-8") as lf:
                                lf.write(f"[{_now_str()}] STOP batch: no_keys em {rel}\n")
                            rem = [str(batch[j].relative_to(input_dir)) for j in range(idx - 1, len(batch))]
                            qpath = review_dir / (
                                f"{output_tag}_interrupted_remaining.txt" if output_tag else "batch_interrupted_remaining.txt"
                            )
                            qpath.write_text("\n".join(rem), encoding="utf-8")
                            es = _t(res.error_status)
                            if "all_in_cooldown_or_blocked" in es:
                                batch_stop_reason = "PAUSA_TODAS_CHAVES_COOLDOWN"
                            elif "per_key_limit" in es:
                                batch_stop_reason = "PAUSA_LIMITE_POR_CHAVE"
                            elif "no_ok_from_start" in es:
                                batch_stop_reason = "PAUSA_SEM_CHAVE_OK"
                            else:
                                batch_stop_reason = "no_keys"
                            break
        elif should_try_gemini:
            gemini_failed = True
            gemini_error = "sem_imagem_para_gemini"

        tipo, missing = required_fields_status(parsed)
        status, motivo, conf, precisa_humano = decide_status(
            local_conf,
            missing,
            tipo,
            used_gemini,
            gem_conf,
            gemini_failed=gemini_failed,
            gemini_error=gemini_error,
            gemini_error_status=gemini_error_status,
            pause_motivo=pause_motivo,
        )

        if status.startswith("AMARELO"):
            stats["AMARELO_REVISAR"] += 1
        elif status == "VERDE_AUTO_LOCAL":
            stats["VERDE_AUTO_LOCAL"] += 1
        elif status == "VERDE_AUTO_GEMINI":
            stats["VERDE_AUTO_GEMINI"] += 1
        elif status == "PAUSA_INFRA_SEM_CHAVE":
            stats["PAUSA_INFRA_SEM_CHAVE"] += 1
        elif status == "PAUSA_LOTE_INTERROMPIDO":
            stats["PAUSA_LOTE_INTERROMPIDO"] += 1
        elif status == "PAUSA_LIMITE_CHAMADAS":
            stats["PAUSA_LIMITE_CHAMADAS"] += 1
        elif status == "PAUSA_TODAS_CHAVES_COOLDOWN":
            stats["PAUSA_TODAS_CHAVES_COOLDOWN"] += 1
        elif status == "PAUSA_LIMITE_POR_CHAVE":
            stats["PAUSA_LIMITE_POR_CHAVE"] += 1
        elif status == "PAUSA_SEM_CHAVE_OK":
            stats["PAUSA_SEM_CHAVE_OK"] += 1
        else:
            stats["VERMELHO_REVISAR"] += 1

        if motivo:
            for tok in motivo.split(";"):
                top_motivos[tok] = top_motivos.get(tok, 0) + 1

        row = {
            "id_local": id_local,
            "arquivo": rel,
            "lote": "",
            "ordem": str(ordinal_base + idx),
            "tipo_motor": normalize_tipo_motor(_t(parsed.get("tipo_motor"))),
            "potencia_cv": _t(parsed.get("potencia_cv")),
            "rpm": _t(parsed.get("rpm")),
            "tensao": _t(parsed.get("tensao")),
            "polos": _t(parsed.get("polos")),
            "frequencia": _t(parsed.get("frequencia")),
            "carcaca": _t(parsed.get("carcaca")),
            "ranhuras": _t(parsed.get("ranhuras")),
            "pacote_mm": _t(parsed.get("pacote_mm")),
            "diametro_mm": _t(parsed.get("diametro_mm")),
            "capacitor": _t(parsed.get("capacitor")),
            "fio_principal": _t(parsed.get("fio_principal")),
            "espiras_principal": _t(parsed.get("espiras_principal")),
            "passo_principal": _t(parsed.get("passo_principal")),
            "fio_auxiliar": _t(parsed.get("fio_auxiliar")),
            "espiras_auxiliar": _t(parsed.get("espiras_auxiliar")),
            "passo_auxiliar": _t(parsed.get("passo_auxiliar")),
            "status_revisao": status,
            "motivos_bloqueio": motivo,
            "fonte_extracao": source,
            "confianca": f"{conf:.2f}",
            "precisa_humano": "1" if precisa_humano else "0",
        }

        event = {
            "generated_at": _now_str(),
            "arquivo": str(path),
            "arquivo_rel": rel,
            "id_local": id_local,
            "dry_run": bool(args.dry_run),
            "local": {
                "confianca": local_conf,
                "texto_ocr_bruto": redact_secrets_in_text(local_text[:4000]),
                "fonte_local": primary_local_source,
            },
            "gemini": {
                "usado": used_gemini,
                "falhou": gemini_failed,
                "erro_resumido": redact_secrets_in_text(gemini_error)[:200],
                "confianca": gem_conf,
                "key_alias": gem_info.get("key_alias", ""),
                "model": gem_info.get("model", ""),
            },
            "cache_hit": bool(cache_hit),
            "cache_dir": cache_hit_dir_name,
            "resultado": row,
            "missing_fields": missing,
        }

        if getattr(args, "emit_schema_sidecar", False):
            src_meta = {
                "fonte_extracao": source,
                "arquivo_rel": rel,
                "id_local": id_local,
            }
            raw_pack = {"texto_ocr_bruto": local_text, "filename": path.name}
            scb = build_schema_sidecar_from_parsed(parsed, raw_pack, src_meta)
            if gemini_payload:
                scb = merge_gemini_nested_into_sidecar(gemini_payload, scb)
            event["schema_sidecar"] = sidecar_to_json_safe(scb)

        # salva outputs (sem gravar em Supabase)
        with open(csv_path, "a", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=csv_cols)
            w.writerow(row)
        write_jsonl(jsonl_path, event)

        # checkpoint (PAUSA_INFRA_* / PAUSA_LIMITE_*: re-tentar noutra execução)
        if status not in ("PAUSA_INFRA_SEM_CHAVE", "PAUSA_LIMITE_CHAMADAS"):
            done[rel] = {"finished_at": _now_str(), "status": status}
            checkpoint["done"] = done
            save_checkpoint(checkpoint_path, checkpoint)

        stats["processed"] += 1
        if len(good_examples) < 5 and status in {"VERDE_AUTO_LOCAL", "VERDE_AUTO_GEMINI"}:
            good_examples.append(
                {
                    "arquivo": rel,
                    "status": status,
                    "tipo_motor": row["tipo_motor"],
                    "tensao": row["tensao"],
                    "fio_principal": row["fio_principal"],
                    "fonte_extracao": row["fonte_extracao"],
                }
            )
        if len(bad_examples) < 5 and status in {"AMARELO_REVISAR", "VERMELHO_REVISAR"}:
            bad_examples.append(
                {
                    "arquivo": rel,
                    "status": status,
                    "motivos_bloqueio": row["motivos_bloqueio"],
                    "fonte_extracao": row["fonte_extracao"],
                }
            )
        if status == "VERMELHO_REVISAR" and len(problematic) < 10:
            problematic.append({"arquivo": rel, "motivos": motivo, "missing": missing})

        with open(log_path, "a", encoding="utf-8") as lf:
            lf.write(f"[{_now_str()}] {rel} -> {status} conf={conf:.2f} source={source}\n")

        if status == "PAUSA_LIMITE_CHAMADAS":
            break

    # summary md
    top20 = sorted(top_motivos.items(), key=lambda x: x[1], reverse=True)[:20]
    top10 = top20[:10]
    md = []
    md.append(f"## Resumo batch rebobinagem ({_now_str()})\n")
    md.append(f"- **input**: `{input_dir}`")
    if work_queue_mode:
        md.append(f"- **work_queue_csv**: `{work_queue_csv}`")
        md.append(f"- **output_tag**: `{output_tag}`")
        if not limit_user_specified:
            md.append(
                "\n> **AVISO — limite de ficheiros:** Nao foi passado `--limit` na linha de comando. "
                "Neste modo, o programa aplica o **default 20** (apenas as primeiras 20 entradas da fila). "
                "Para 100, use `--limit 100`. Para nao cortar a fila, use `--limit 0`.\n"
            )
    if manifest_mode:
        md.append(f"- **manifest_csv**: `{manifest_csv}`")
        md.append(f"- **output_tag**: `{output_tag}`")
    md.append(f"- **dry-run**: `{bool(args.dry_run)}` (sem chamadas Gemini à API)")
    md.append(f"- **processados**: `{stats['processed']}`")
    if batch_stop_reason:
        md.append(f"- **lote interrompido**: `{batch_stop_reason}`")
    md.append(f"- **cache respostas**: `{cache_root}`\n")
    md.append("### Fontes\n")
    md.append(f"- tentativas pipeline local (PDF texto / Tesseract / EasyOCR): {stats['local_ocr_attempts']}")
    md.append(f"- com texto local não vazio: {stats['local_ocr_files']}")
    md.append(f"- chamadas API Gemini: {stats['gemini_api_calls']}")
    md.append(f"- imagens com fallback Gemini (contagem interna): {stats['gemini_files']}")
    md.append(f"- respostas servidas do cache (sem API): {stats['gemini_cache_hits']}\n")
    md.append("### Economia de chaves / cache\n")
    md.append(f"- pastas cache consultadas: {stats.get('cache_lookup_paths', 1)}")
    md.append(f"- **cache_hits**: {stats['gemini_cache_hits']}")
    md.append(f"- **cache_misses** (resolveu por API): {stats['gemini_api_calls']}")
    md.append(f"- **gemini_calls_real**: {stats['gemini_api_calls']}")
    md.append(f"- **gemini_calls_avoided_by_cache**: {stats['gemini_cache_hits']}")
    md.append(f"- **quota_429**: {stats.get('gemini_quota_429', 0)}")
    md.append(f"- **quota_429_consecutive_max**: {stats.get('gemini_quota_consecutive', 0)}")
    md.append(f"- skipped_existing_green: {stats.get('skipped_existing_green', 0)}")
    md.append(f"- skipped_existing_success: {stats.get('skipped_existing_success', 0)}\n")
    md.append("### Status\n")
    md.append(f"- VERDE_AUTO_LOCAL: {stats['VERDE_AUTO_LOCAL']}")
    md.append(f"- VERDE_AUTO_GEMINI: {stats['VERDE_AUTO_GEMINI']}")
    md.append(f"- AMARELO_REVISAR: {stats['AMARELO_REVISAR']}")
    md.append(f"- VERMELHO_REVISAR: {stats['VERMELHO_REVISAR']}")
    md.append(f"- PAUSA_INFRA_SEM_CHAVE: {stats.get('PAUSA_INFRA_SEM_CHAVE', 0)}")
    md.append(f"- PAUSA_LIMITE_CHAMADAS: {stats.get('PAUSA_LIMITE_CHAMADAS', 0)}")
    md.append(f"- PAUSA_LOTE_INTERROMPIDO: {stats.get('PAUSA_LOTE_INTERROMPIDO', 0)}\n")
    md.append(f"- PAUSA_TODAS_CHAVES_COOLDOWN: {stats.get('PAUSA_TODAS_CHAVES_COOLDOWN', 0)}")
    md.append(f"- PAUSA_LIMITE_POR_CHAVE: {stats.get('PAUSA_LIMITE_POR_CHAVE', 0)}")
    md.append(f"- PAUSA_SEM_CHAVE_OK: {stats.get('PAUSA_SEM_CHAVE_OK', 0)}\n")
    md.append("### Chaves Gemini usadas (alias)\n")
    for k, n in sorted(keys_used.items(), key=lambda x: x[0]):
        md.append(f"- {k}: {n}")
    # relatório detalhado por chave (usa dados do status JSON em memória; não expõe chave)
    md.append("\n### Uso por chave (detalhado)\n")
    md.append(f"- rotation_strategy: `{getattr(km, 'rotation_strategy', '')}`")
    md.append(f"- max_calls_per_key_per_run: `{getattr(km, 'max_calls_per_key_per_run', 0)}`\n")
    require_ok = not bool(args.gemini_allow_non_ok_keys)
    now = int(time.time())
    for alias in sorted(list(km._keys_by_alias.keys()), key=lambda x: x):  # noqa: SLF001
        st = km._status.get(alias)  # noqa: SLF001
        if not st:
            continue
        cooldown_active = bool(st.cooldown_until_epoch and now < int(st.cooldown_until_epoch) and st.status != "ok")
        soft_limit = bool(getattr(km, "max_calls_per_key_per_run", 0) and st.calls_this_run >= int(getattr(km, "max_calls_per_key_per_run", 0)))
        blocked = []
        if st.status in {"invalid", "permission_denied"}:
            blocked.append(st.status)
        if require_ok and st.status != "ok":
            blocked.append("require_ok")
        if cooldown_active:
            blocked.append("cooldown")
        if soft_limit:
            blocked.append("per_key_limit")
        eligible = len(blocked) == 0
        md.append(
            f"- {alias} | status={st.status} | eligible_end={int(eligible)} | calls={st.calls_this_run} | ok={st.success_this_run} "
            f"| quota={st.quota_this_run} | errors={st.errors_this_run} | cooldown={st.cooldown_until or ''} | blocked={';'.join(blocked)}"
        )
    md.append("\n### Top 10 motivos de bloqueio\n")
    for reason, n in top10:
        md.append(f"- {reason}: {n}")
    md.append("\n### Top 11–20 (extra)\n")
    for reason, n in top20[10:]:
        md.append(f"- {reason}: {n}")
    md.append("\n### Exemplos (até 10) problemáticos\n")
    for ex in problematic:
        md.append(f"- {ex['arquivo']}: {ex['motivos']} missing={ex['missing']}")
    summary_md.write_text("\n".join(md) + "\n", encoding="utf-8")

    # refletir motivo do lote no contador de pausas (1x por execução)
    if batch_stop_reason in stats:
        try:
            stats[batch_stop_reason] += 1
        except Exception:
            pass

    print("Resumo final:")
    if work_queue_mode and not limit_user_specified:
        print(
            "AVISO: work queue sem --limit na CLI — aplicado default 20 (ver bloco no summary.md e stderr no arranque)."
        )
    if batch_stop_reason:
        print(f"- lote interrompido: {batch_stop_reason}")
    print(f"- arquivos processados: {stats['processed']}")
    print(f"- tentativas OCR/texto local: {stats['local_ocr_attempts']}")
    print(f"- com texto local não vazio: {stats['local_ocr_files']}")
    print(f"- chamadas API Gemini: {stats['gemini_api_calls']}")
    print(f"- respostas do cache (sem API): {stats['gemini_cache_hits']}")
    print(f"- cache_hits: {stats['gemini_cache_hits']}; cache_misses (API): {stats['gemini_api_calls']}")
    print(f"- gemini_calls_real: {stats['gemini_api_calls']}; gemini_calls_avoided_by_cache: {stats['gemini_cache_hits']}")
    print(f"- skipped_existing_green: {stats.get('skipped_existing_green', 0)}; skipped_existing_success: {stats.get('skipped_existing_success', 0)}")
    print(f"- fallback Gemini (ficheiros com intento API): {stats['gemini_files']}")
    print(f"- VERDE_AUTO_LOCAL: {stats['VERDE_AUTO_LOCAL']}")
    print(f"- VERDE_AUTO_GEMINI: {stats['VERDE_AUTO_GEMINI']}")
    print(f"- AMARELO_REVISAR: {stats['AMARELO_REVISAR']}")
    print(f"- VERMELHO_REVISAR: {stats['VERMELHO_REVISAR']}")
    print(f"- PAUSA_INFRA_SEM_CHAVE: {stats.get('PAUSA_INFRA_SEM_CHAVE', 0)}")
    print(f"- PAUSA_LIMITE_CHAMADAS: {stats.get('PAUSA_LIMITE_CHAMADAS', 0)}")
    print(f"- PAUSA_TODAS_CHAVES_COOLDOWN: {stats.get('PAUSA_TODAS_CHAVES_COOLDOWN', 0)}")
    print(f"- PAUSA_LIMITE_POR_CHAVE: {stats.get('PAUSA_LIMITE_POR_CHAVE', 0)}")
    print(f"- PAUSA_SEM_CHAVE_OK: {stats.get('PAUSA_SEM_CHAVE_OK', 0)}")
    print("- top 10 motivos bloqueio:")
    for reason, n in top10:
        print(f"  - {reason}: {n}")
    print("- exemplos bons (ate 5):")
    for ex in good_examples:
        print(f"  - {ex}")
    print("- exemplos ruins (ate 5):")
    for ex in bad_examples:
        print(f"  - {ex}")
    print(f"- CSV: {csv_path}")
    print(f"- JSONL: {jsonl_path}")
    print(f"- Summary: {summary_md}")
    print(f"- Log: {log_path}")
    print(f"- Gemini keys status: {status_path}")
    print(f"- Checkpoint: {checkpoint_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

