"""
JOIN manifesto oficial + banco técnico bruto e estatísticas de cluster (auditoria física).
Usado pelo Streamlit para selo de validação, quarentena dos suspeitos e caixa de referência.
"""
from __future__ import annotations

import csv
import html
import json
import os
import re
import statistics
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st

# SHAs dos 6 motores "Suspeitos" — auditoria_fisica_motores_700.md (Top 6)
SUSPECT_SHA256_MANIFEST: frozenset[str] = frozenset(
    {
        "1e54f45ed0581938a443dccc9ad8130b28e14ae1fcaa3b085caadc2f7badda78",
        "cc134e5e7a4b4b0b3b6521f2e591ded628ec1a4c4623f8d0fcccfa0343dd2b93",
        "e7d22e1e4d8d892ce526ae87e9ba51c0f32d5b23bc9ed2a9345acf42632ef413",
        "5781cd06d07eeadb733fb26d5d7d2c75466c1f8c4178aad2c78ea3ca792de71d",
        "7e05b0c30eaf585155b4ce0038bd985e27fe5b2e0b2f0359c906ab583c7a95e2",
        "91b18dab1e681a9dfab58daa7a4202c2162d102e49f978c6ed78b8b387f21161",
    }
)

CLUSTER_MIN_MOTORS = 2

# Textos de interface (PT-BR formal, acentuado)
AUDIT_WARNING_QUARENTENA = "Dados em revisão técnica — Use como referência aproximada."
AUDIT_TOOLTIP_SEL_VALIDADO = (
    "Este motor foi validado através de cálculos de densidade magnética "
    "e análise estatística de cluster."
)


def audit_status_chips_html(audit_state: dict[str, Any]) -> str:
    """Fragmento HTML para a faixa de chips (consulta / detalhe / teaser)."""
    if audit_state.get("quarantine"):
        return (
            '<div class="motor-chip motor-chip--quarantine" '
            'title="Motor sinalizado na auditoria física do índice; conferir antes de usar como referência definitiva.">'
            "Índice: revisão física (auditoria)</div>"
        )
    if audit_state.get("validated"):
        tip = html.escape(AUDIT_TOOLTIP_SEL_VALIDADO, quote=True)
        return (
            f'<div class="motor-chip motor-chip--audit-valid" title="{tip}">'
            "✅ Dados auditados</div>"
        )
    return ""

AWG_MM2 = {
    10: 5.26,
    11: 4.17,
    12: 3.31,
    13: 2.62,
    14: 2.08,
    15: 1.65,
    16: 1.31,
    17: 1.04,
    18: 0.823,
    19: 0.653,
    20: 0.518,
    21: 0.410,
    22: 0.326,
    23: 0.258,
    24: 0.205,
    25: 0.162,
    26: 0.129,
    27: 0.102,
    28: 0.0810,
    29: 0.0642,
    30: 0.0509,
}


def fnum(v: Any) -> Optional[float]:
    if v is None:
        return None
    s = str(v).strip().lower().replace(",", ".")
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    return float(m.group()) if m else None


def awg_area(v: Any) -> Optional[float]:
    s = (
        str(v or "")
        .lower()
        .replace("'", "")
        .replace('"', "")
        .replace("[", " ")
        .replace("]", " ")
    )
    m = re.search(r"awg\s*(\d{1,2})", s) or re.search(r"\b(\d{1,2})\s*awg\b", s)
    if m:
        return AWG_MM2.get(int(m.group(1)))
    m = re.search(r"#\s*(\d{1,2})\b", s)
    if m:
        return AWG_MM2.get(int(m.group(1)))
    m = re.search(r"\b(\d+)\s*[x×]\s*(\d{1,2})\b", s)
    if m:
        n_par = int(m.group(1))
        unit = AWG_MM2.get(int(m.group(2)))
        return n_par * unit if unit is not None else None
    mm2 = fnum(s) if "mm" in s else None
    return mm2


def poles_from_rpm(rpm: Optional[float], freq: int = 60) -> Optional[int]:
    if not rpm or rpm <= 0:
        return None
    p = round((120 * freq) / rpm)
    return p if p in {2, 4, 6, 8, 10, 12} else None


def pick(row: dict, *names: str) -> str:
    keys = {k.lower(): k for k in row.keys()}
    for n in names:
        if n.lower() in keys:
            return str(row[keys[n.lower()]] or "")
    return ""


def normalize_tension_token(s: str) -> str:
    t = str(s or "").lower().replace("v", " ")
    t = re.sub(r"\s+", " ", t).strip()
    t = t.replace("/", "-").replace("_", "-")
    return t


NOMINAL_VOLTAGES = frozenset(
    {
        100,
        110,
        115,
        120,
        127,
        200,
        208,
        220,
        230,
        240,
        254,
        277,
        380,
        400,
        415,
        440,
        460,
        480,
        500,
        575,
        600,
    }
)


def parse_volts_tuple_from_string(s: str) -> Tuple[float, ...]:
    t = normalize_tension_token(s)
    seen: set[float] = set()
    for m in re.finditer(r"\b(\d{2,3})\b", t):
        v = float(m.group(1))
        if v in NOMINAL_VOLTAGES:
            seen.add(v)
    return tuple(sorted(seen))


def basename_arquivo(row: str) -> str:
    rel = str(row or "").strip().strip('"').strip("'")
    if not rel:
        return ""
    parts = re.split(r"[\\/]+", rel)
    return parts[-1] if parts else ""


def infer_phases_from_name(low: str) -> int:
    if "mono" in low or "monof" in low:
        return 1
    return 3


def parse_axis_from_manifest_row(row: dict) -> dict:
    rel = pick(row, "arquivo_rel", "arquivo_origem", "path", "file", "nome_arquivo")
    bn = basename_arquivo(rel)
    low = bn.lower()

    cv = fnum(pick(row, "cv", "potencia_cv", "potencia", "pot_kw", "kw"))
    polos = fnum(pick(row, "polos", "poles"))
    rpm = fnum(pick(row, "rpm", "rotacao"))
    tensao_raw = pick(row, "tensao", "voltagem", "v", "tensao_nominal")

    volts_tuple: Tuple[float, ...] = tuple()
    if tensao_raw:
        volts_tuple = parse_volts_tuple_from_string(tensao_raw)

    vm = re.search(r"-\s*(\d+(?:[-/]\d+)*)\s*-\s*(\d+)\s*p\.pdf\s*$", low)
    if vm:
        raw_v, polos_s = vm.group(1), vm.group(2)
        polos = float(polos_s)
        parts = re.split(r"[-/]", raw_v)
        nums: List[float] = []
        for p in parts:
            p = p.strip().replace(",", ".")
            if not p:
                continue
            if re.match(r"^\d", p):
                nums.append(float(fnum(p) or 0))
        volts_tuple = tuple(sorted({x for x in nums if x > 0}))
        head = low[: vm.start()]
        cv_m = None
        for m in re.finditer(r"(\d+(?:[.,]\d+)?)\s*cv", head):
            cv_m = float(m.group(1).replace(",", "."))
        if cv_m is not None:
            cv = cv_m

    if cv is None:
        for m in re.finditer(r"(\d+(?:[.,]\d+)?)\s*cv", low):
            cv = float(m.group(1).replace(",", "."))

    if cv is None:
        m = re.search(r"(\d+(?:[.,]\d+)?)\s*kw", low)
        if m:
            kw = float(m.group(1).replace(",", "."))
            cv = kw * 1000.0 / 735.5

    if polos is None:
        pm = re.search(r"\b(\d+)\s*p\.(?:pdf)?", low)
        if pm:
            polos = float(pm.group(1))
    if polos is None:
        m = re.search(r"cv.*?(\d+)\s*p\b", low)
        if m:
            polos = float(m.group(1))

    if polos is None and rpm:
        polos = float(poles_from_rpm(rpm) or 0) or None

    if not volts_tuple and tensao_raw:
        volts_tuple = parse_volts_tuple_from_string(tensao_raw)

    if not volts_tuple and re.search(
        r"\b(110|115|127|220|230|254|380|400|440|460)\s*[-/]\s*(110|115|127|220|230|254|380|400|440|460)\b",
        low,
    ):
        volts_tuple = parse_volts_tuple_from_string(low)

    phases = infer_phases_from_name(low)
    if fnum(pick(row, "fases", "phases")) is not None:
        phases = int(fnum(pick(row, "fases", "phases")) or phases)

    v_line = min(volts_tuple) if volts_tuple else None

    return {
        "basename": bn,
        "cv": cv,
        "polos": int(polos) if polos else None,
        "volts_tuple": volts_tuple,
        "v_line": v_line,
        "rpm": rpm,
        "phases": phases,
    }


def cluster_key_from_row(axis: dict, cv: Optional[float], polos: Optional[int]) -> Optional[Tuple]:
    if cv is None or polos is None:
        return None
    vt = axis["volts_tuple"]
    if not vt:
        vt_t = ("?",)
    else:
        vt_t = tuple(round(v, 1) for v in vt)
    return (round(float(cv), 2), int(polos), vt_t)


def format_volts_label(vt: tuple) -> str:
    if vt == ("?",):
        return "tensão não inferida no nome"
    return "/".join(str(int(v)) if v == int(v) else str(v) for v in vt)


def norm_join_key(rel: str) -> str:
    bn = basename_arquivo(rel)
    bn = bn.lower()
    bn = re.sub(r"\s+", " ", bn).strip()
    return bn


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _resolve_csv_paths() -> Tuple[Optional[Path], Optional[Path]]:
    env_m = os.environ.get("MRW_MANIFEST_CSV", "").strip()
    env_b = os.environ.get("MRW_BANCO_MOTORES_CSV", "").strip()
    if env_m and env_b:
        pm, pb = Path(env_m), Path(env_b)
        if pm.is_file() and pb.is_file():
            return pm, pb

    root = _repo_root()
    candidates_m: List[Path] = [
        root / "data" / "master_release_v2_manifest.csv",
        root.parent / "Calculos" / "master_release_v2_manifest.csv",
    ]
    candidates_b: List[Path] = [
        root / "data" / "backup_bruto" / "banco_motores_completos.csv",
        root.parent / "Calculos" / "backup_bruto" / "banco_motores_completos.csv",
    ]
    pm = next((p for p in candidates_m if p.is_file()), None)
    pb = next((p for p in candidates_b if p.is_file()), None)
    return pm, pb


def _read_csv(path: Path) -> List[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _merge_manifest_banco(manifest_rows: List[dict], banco_rows: List[dict]) -> List[dict]:
    banco_by_key: dict[str, dict] = {}
    for r in banco_rows:
        k = norm_join_key(r.get("arquivo_origem", ""))
        if not k:
            continue
        if k not in banco_by_key:
            banco_by_key[k] = r

    merged: List[dict] = []
    tech_fields = (
        "espiras",
        "fio",
        "polos",
        "potencia",
        "tensao",
        "rpm",
        "passo",
        "cv",
        "fases",
    )
    for mr in manifest_rows:
        out = dict(mr)
        k = norm_join_key(mr.get("arquivo_rel", ""))
        br = banco_by_key.get(k)
        if br:
            for field in tech_fields:
                val = br.get(field)
                if val is not None and str(val).strip():
                    out[field] = val
        merged.append(out)
    return merged


def _serial_cluster_key(ck: Tuple) -> str:
    cv, polos, vt = ck
    return f"{cv}|{polos}|{vt}"


@dataclass(frozen=True)
class ClusterSummary:
    n_motors: int
    mean_espiras: Optional[float]
    mean_mm2: Optional[float]
    cv: float
    polos: int
    volts_label: str


@dataclass(frozen=True)
class AuditQualityBundle:
    join_key_to_sha: dict[str, str]
    all_manifest_shas: frozenset[str]
    suspect_shas: frozenset[str]
    cluster_by_key: dict[str, ClusterSummary]
    sha_to_cluster_key: dict[str, str]


def _build_bundle_from_paths(manifest_path: Path, banco_path: Path) -> AuditQualityBundle:
    manifest_rows = _read_csv(manifest_path)
    banco_rows = _read_csv(banco_path)
    merged = _merge_manifest_banco(manifest_rows, banco_rows)

    join_key_to_sha: dict[str, str] = {}
    all_shas: set[str] = set()
    for mr in manifest_rows:
        sh = pick(mr, "sha256_arquivo", "sha", "registro_chave", "hash").strip().lower()
        if len(sh) == 64 and all(c in "0123456789abcdef" for c in sh):
            all_shas.add(sh)
            jk = norm_join_key(mr.get("arquivo_rel", ""))
            if jk:
                join_key_to_sha[jk] = sh

    data: List[dict] = []
    for r in merged:
        axis = parse_axis_from_manifest_row(r)
        sha = pick(r, "sha256_arquivo", "sha", "registro_chave", "id", "hash") or ""
        sha = sha.strip().lower()
        if len(sha) != 64:
            continue
        cv = axis["cv"] or fnum(pick(r, "cv", "potencia_cv", "potencia"))
        polos = axis["polos"] if axis["polos"] is not None else None
        if polos is None and axis["rpm"]:
            polos = poles_from_rpm(axis["rpm"])
        esp = fnum(pick(r, "espiras", "numero_espiras", "n_espiras"))
        fio = pick(r, "fio", "bitola", "wire_gauge")
        area = awg_area(fio)
        passo = fnum(pick(r, "passo", "passos"))
        phases = axis["phases"]
        v_line = axis["v_line"] or fnum(pick(r, "tensao", "voltagem", "v"))
        ck = cluster_key_from_row(axis, cv, int(polos) if polos is not None else None)
        data.append(
            {
                "sha": sha,
                "cv": cv,
                "volts_tuple": axis["volts_tuple"],
                "v_line": v_line,
                "polos": int(polos) if polos else None,
                "esp": esp,
                "area": area,
                "passo": passo,
                "rpm": axis["rpm"],
                "phases": phases,
                "fio": fio,
                "cluster_key": ck,
            }
        )

    clusters: dict[Tuple, List[dict]] = defaultdict(list)
    for d in data:
        if d["cluster_key"] is not None and d["cv"] and d["polos"]:
            clusters[d["cluster_key"]].append(d)

    cluster_by_key: dict[str, ClusterSummary] = {}
    for key, items in clusters.items():
        if len(items) < CLUSTER_MIN_MOTORS:
            continue
        esp = [x["esp"] for x in items if x["esp"] is not None]
        area = [x["area"] for x in items if x["area"] is not None]
        common_esp = round(statistics.mean(esp), 1) if esp else None
        common_area = round(statistics.mean(area), 3) if area else None
        vlab = format_volts_label(key[2])
        cluster_by_key[_serial_cluster_key(key)] = ClusterSummary(
            n_motors=len(items),
            mean_espiras=common_esp,
            mean_mm2=common_area,
            cv=float(key[0]),
            polos=int(key[1]),
            volts_label=vlab,
        )

    sha_to_cluster_key: dict[str, str] = {}
    for d in data:
        ck = d["cluster_key"]
        if ck is None:
            continue
        sk = _serial_cluster_key(ck)
        if sk in cluster_by_key:
            sha_to_cluster_key[d["sha"]] = sk

    return AuditQualityBundle(
        join_key_to_sha=join_key_to_sha,
        all_manifest_shas=frozenset(all_shas),
        suspect_shas=SUSPECT_SHA256_MANIFEST,
        cluster_by_key=cluster_by_key,
        sha_to_cluster_key=sha_to_cluster_key,
    )


def _build_audit_quality_bundle_impl() -> Optional[AuditQualityBundle]:
    pm, pb = _resolve_csv_paths()
    if pm is None or pb is None:
        return None
    try:
        return _build_bundle_from_paths(pm, pb)
    except Exception:
        return None


@st.cache_data(ttl=120, show_spinner=False)
def load_audit_quality_bundle_cached() -> Optional[AuditQualityBundle]:
    return _build_audit_quality_bundle_impl()


def clear_audit_quality_bundle_cache() -> None:
    load_audit_quality_bundle_cached.clear()


def _norm_sha64(s: str) -> Optional[str]:
    t = s.strip().lower()
    if len(t) == 64 and all(c in "0123456789abcdef" for c in t):
        return t
    return None


def _json_dict(raw: Any) -> dict:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip().startswith("{"):
        try:
            o = json.loads(raw)
            return o if isinstance(o, dict) else {}
        except Exception:
            return {}
    return {}


def resolve_motor_manifest_sha256(raw_row: dict, bundle: AuditQualityBundle) -> Optional[str]:
    for k in (
        "sha256_arquivo",
        "Sha256Arquivo",
        "sha256",
        "SHA256_ARQUIVO",
        "hash_pdf_sha256",
    ):
        hit = _norm_sha64(str(raw_row.get(k) or ""))
        if hit:
            return hit

    variaveis = raw_row.get("variaveis_site") or raw_row.get("VariaveisSite")
    vd = _json_dict(variaveis)
    for k in ("sha256_arquivo", "Sha256Arquivo", "registro_chave"):
        hit = _norm_sha64(str(vd.get(k) or ""))
        if hit and len(hit) == 64:
            return hit

    for ao_key in ("arquivo_origem", "ArquivoOrigem"):
        ao = str(raw_row.get(ao_key) or "").strip()
        if ao:
            for part in re.split(r"[,;]", ao):
                jk = norm_join_key(part)
                sh = bundle.join_key_to_sha.get(jk)
                if sh:
                    return sh

    dj = _json_dict(raw_row.get("dados_tecnicos_json") or raw_row.get("leitura_gemini_json"))
    ao2 = str(dj.get("arquivo_origem") or "").strip()
    if ao2:
        for part in re.split(r"[,;]", ao2):
            jk = norm_join_key(part)
            sh = bundle.join_key_to_sha.get(jk)
            if sh:
                return sh

    imgs = raw_row.get("imagens_urls") or raw_row.get("ImagemUrls")
    if isinstance(imgs, str):
        imgs = [x.strip() for x in imgs.replace(";", ",").split(",") if x.strip()]
    if isinstance(imgs, list):
        for u in imgs:
            s = str(u).strip()
            if s.lower().endswith(".pdf") or "/" in s or "\\" in s:
                jk = norm_join_key(s)
                sh = bundle.join_key_to_sha.get(jk)
                if sh:
                    return sh
    return None


def get_audit_ui_state(raw_row: dict, bundle: Optional[AuditQualityBundle]) -> dict[str, Any]:
    out: dict[str, Any] = {
        "quarantine": False,
        "validated": False,
        "cluster": None,
        "sha256": None,
        "in_release_index": False,
    }
    if bundle is None:
        return out
    sha = resolve_motor_manifest_sha256(raw_row, bundle)
    out["sha256"] = sha
    if not sha:
        return out
    out["in_release_index"] = sha in bundle.all_manifest_shas
    out["quarantine"] = sha in bundle.suspect_shas
    out["validated"] = sha in bundle.all_manifest_shas and sha not in bundle.suspect_shas
    ck = bundle.sha_to_cluster_key.get(sha)
    if ck:
        out["cluster"] = bundle.cluster_by_key.get(ck)
    return out


def format_engineering_reference_line(cs: ClusterSummary) -> str:
    esp_txt = f"{cs.mean_espiras:g} espiras" if cs.mean_espiras is not None else "espiras sem média numérica"
    if cs.mean_mm2 is not None:
        fio_txt = f"fio ~{cs.mean_mm2:g} mm² (bitola média no cluster)"
    else:
        fio_txt = "bitola média indisponível (OCR ou colunas vazias no agregado)"
    return (
        f"Neste cluster ({cs.cv:g} CV, {cs.polos}P, {cs.volts_label}), com base em **{cs.n_motors}** motores do índice, "
        f"a média é de ~**{esp_txt}** e **{fio_txt}**."
    )
