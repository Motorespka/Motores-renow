#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cruza PDF/JPG físicos nas raízes de armazenamento vs SHAs OFICIAIS do master_release_v2.
Gera relatório JSON/MD e opcionalmente fila pass1_v2_block_NN.csv com massa inédita.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
REVIEW_DIR = (REPO_ROOT / "exports" / "review").resolve()
MONO_ROOT = REPO_ROOT.parent

MEDIA_EXTS = {".pdf", ".jpg", ".jpeg"}


def _t(v) -> str:
    return "" if v is None else str(v).strip()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().lower()


def discover_storage_roots(mono: Path) -> list[tuple[Path, str]]:
    roots: list[tuple[Path, str]] = []
    candidates = [
        (mono / "_extraidos_motor", "_extraidos_motor"),
        (mono / "backup_bruto", "backup_bruto"),
        (mono / "data", "data"),
        (REPO_ROOT / "data", "Motores-renow/data"),
        (REPO_ROOT / "backup_bruto", "Motores-renow/backup_bruto"),
        (mono / "audit_reports", "audit_reports"),
    ]
    seen: set[Path] = set()
    for p, label in candidates:
        rp = p.resolve()
        if rp in seen or not rp.is_dir():
            continue
        seen.add(rp)
        roots.append((rp, label))
    return roots


def load_oficial_shas(manifest_path: Path) -> set[str]:
    shas: set[str] = set()
    with manifest_path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if _t(row.get("status_release")).upper() != "OFICIAL":
                continue
            sh = _t(row.get("sha256_arquivo")).lower()
            if sh:
                shas.add(sh)
    return shas


def load_index_shas(index_path: Path) -> dict[str, str]:
    """rel_norm -> sha"""
    m: dict[str, str] = {}
    if not index_path.is_file():
        return m
    with index_path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            ip = _t(row.get("image_path")).replace("/", "\\")
            sh = _t(row.get("sha256_arquivo")).lower()
            if ip and sh:
                m[ip.lower()] = sh
    return m


def iter_media_files(root: Path):
    for fp in root.rglob("*"):
        if fp.is_file() and fp.suffix.lower() in MEDIA_EXTS:
            yield fp


def scan_physical(
    roots: list[tuple[Path, str]],
    primary_base: Path,
    index_by_rel: dict[str, str],
) -> list[dict]:
    rows: list[dict] = []
    for root, label in roots:
        for fp in iter_media_files(root):
            try:
                rel_to_primary = fp.relative_to(primary_base).as_posix().replace("/", "\\")
            except ValueError:
                try:
                    rel_to_primary = str(fp.relative_to(root)).replace("/", "\\")
                    if label != "_extraidos_motor":
                        rel_to_primary = f"{label}\\{rel_to_primary}"
                except ValueError:
                    continue
            rel_key = rel_to_primary.lower()
            idx_sh = index_by_rel.get(rel_key, "")
            digest = idx_sh or sha256_file(fp)
            rows.append(
                {
                    "arquivo_rel": rel_to_primary,
                    "sha256_arquivo": digest,
                    "storage_root": label,
                    "abs_path": str(fp.resolve()),
                    "ext": fp.suffix.lower(),
                    "sha_from_index": bool(idx_sh),
                }
            )
    rows.sort(key=lambda r: (r["storage_root"], r["arquivo_rel"].lower()))
    return rows


def collect_infra_retry_rows(review_dir: Path, oficial_shas: set[str]) -> list[dict]:
    """PAUSA_INFRA / quota — prioridade máxima (ex.: ventiladores B62)."""
    out: list[dict] = []
    seen: set[str] = set()

    def _add(ar: str, sh: str, src: str) -> None:
        sh = _t(sh).lower()
        ar = _t(ar).replace("/", "\\")
        if not sh or not ar or sh in oficial_shas or sh in seen:
            return
        seen.add(sh)
        out.append(
            {
                "arquivo_rel": ar,
                "sha256_arquivo": sh,
                "storage_root": "infra_retry",
                "abs_path": "",
                "ext": Path(ar).suffix.lower(),
                "sha_from_index": False,
                "queue_type": "PENDENCY_INFRA_RETRY",
                "reason": f"from={src}|infra=gemini_quota_or_keys",
            }
        )

    for pth in sorted(review_dir.glob("extraidos_motor_fase7a_pass1_v2_block_*_flash_candidates.csv")):
        with pth.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                st = _t(row.get("status_revisao")).upper()
                mot = _t(row.get("motivos_bloqueio")).lower()
                if st != "PAUSA_INFRA_SEM_CHAVE" and "infra:" not in mot:
                    continue
                ar = _t(row.get("arquivo") or row.get("arquivo_rel"))
                sh = _t(row.get("sha256_arquivo"))
                if not ar:
                    continue
                _add(ar, sh, pth.name)

    # ventiladores e demais com SHA na fila B62/B63 mas PAUSA no último extract
    for pth in sorted(review_dir.glob("pass1_v2_block_6*.csv")):
        with pth.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                ar = _t(row.get("arquivo_rel"))
                sh = _t(row.get("sha256_arquivo"))
                if not ar or "ventilador" not in ar.lower():
                    continue
                if sh in oficial_shas or sh in seen:
                    continue
                _add(ar, sh, f"{pth.name}|ventilador_priority")

    for pth in sorted(review_dir.glob("extraidos_motor_fase7a_pass1_v2_block_*_flash_categorized_reprocess_no_keys.csv")):
        with pth.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                ar = _t(row.get("arquivo") or row.get("arquivo_rel"))
                sh = _t(row.get("sha256_arquivo"))
                _add(ar, sh, pth.name)

    return out


def collect_pendency_rows(review_dir: Path, oficial_shas: set[str]) -> list[dict]:
    """
    SHAs de blocos PASS1-v2 ainda não OFICIAIS (manual / alert / categorized ≠ VERDE_SEGURO).
    Prioridade para raspagem da cauda profunda quando --force-include-pendencies.
    """
    out: list[dict] = []
    seen: set[str] = set()

    def _add(ar: str, sh: str, queue_type: str, reason: str) -> None:
        sh = _t(sh).lower()
        ar = _t(ar).replace("/", "\\")
        if not sh or not ar or sh in oficial_shas or sh in seen:
            return
        seen.add(sh)
        out.append(
            {
                "arquivo_rel": ar,
                "sha256_arquivo": sh,
                "storage_root": "pendency",
                "abs_path": "",
                "ext": Path(ar).suffix.lower(),
                "sha_from_index": False,
                "queue_type": queue_type,
                "reason": reason,
            }
        )

    def _block_num(p: Path) -> int:
        m = re.search(r"block_(\d+)", p.name, re.I)
        return int(m.group(1)) if m else 0

    cat_paths = sorted(
        review_dir.glob("extraidos_motor_fase7a_pass1_v2_block_*_flash_categorized_manual_review.csv"),
        key=_block_num,
        reverse=True,
    )
    for pth in cat_paths:
        with pth.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                cat = _t(row.get("categoria")).upper()
                if cat in ("VERDE_SEGURO", ""):
                    continue
                ar = _t(row.get("arquivo") or row.get("arquivo_rel"))
                sh = _t(row.get("sha256_arquivo"))
                _add(ar, sh, "PENDENCY_RETRY_PASS1", f"from={pth.name}|categoria={cat}")

    man_paths = sorted(
        review_dir.glob("extraidos_motor_fase7a_pass1_v2_block_*_manual_review.csv"),
        key=_block_num,
        reverse=True,
    )
    for pth in man_paths:
        with pth.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                ar = _t(row.get("arquivo_rel") or row.get("arquivo"))
                sh = _t(row.get("sha256_arquivo"))
                _add(ar, sh, "PENDENCY_MANUAL_PASS1", f"from={pth.name}")

    for pth in sorted(review_dir.glob("pass1_v2_block_*.csv")):
        if "mutirao" in pth.name.lower():
            continue
        with pth.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                sh = _t(row.get("sha256_arquivo")).lower()
                if not sh or sh in oficial_shas or sh in seen:
                    continue
                qt = _t(row.get("queue_type")).upper()
                if qt and qt not in ("NEW_UNPROCESSED_PASS1", "PENDENCY_RETRY_PASS1", "PENDENCY_MANUAL_PASS1"):
                    continue
                ar = _t(row.get("arquivo_rel")).replace("/", "\\")
                if ar:
                    _add(ar, sh, "PENDENCY_PRIOR_QUEUE", f"from={pth.name}")

    return out


def pick_queue_rows(loose: list[dict], take: int, unique_sha: bool) -> list[dict]:
    if not unique_sha:
        return loose[:take]
    seen: set[str] = set()
    out: list[dict] = []
    for r in loose:
        sh = r["sha256_arquivo"]
        if sh in seen:
            continue
        seen.add(sh)
        out.append(r)
        if len(out) >= take:
            break
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Delta físico vs master OFICIAL.")
    ap.add_argument("--manifest", default=str(REVIEW_DIR / "master_release_v2_manifest.csv"))
    ap.add_argument("--index", default=str(REVIEW_DIR / "processed_image_index.csv"))
    ap.add_argument("--primary-base", default=str(MONO_ROOT / "_extraidos_motor"))
    ap.add_argument("--emit-queue-csv", type=int, default=46, help="Ex.: 46 → pass1_v2_block_46.csv")
    ap.add_argument("--take", type=int, default=14)
    ap.add_argument(
        "--force-include-pendencies",
        action="store_true",
        help="Prioriza pendências PASS1-v2 (manual/alert/filas) antes do slice físico; ignora travas de blocos falhados.",
    )
    ap.add_argument("--out-json", default=str(REVIEW_DIR / "physical_delta_vs_oficial_report.json"))
    ap.add_argument("--out-md", default=str(REVIEW_DIR / "physical_delta_vs_oficial_report.md"))
    args = ap.parse_args()

    utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    manifest_path = Path(args.manifest).resolve()
    primary_base = Path(args.primary_base).resolve()
    roots = discover_storage_roots(MONO_ROOT)

    if not primary_base.is_dir():
        print(f"ERRO: primary-base inexistente: {primary_base}", file=sys.stderr)
        return 2

    oficial_shas = load_oficial_shas(manifest_path)
    index_by_rel = load_index_shas(Path(args.index).resolve())

    print(f"Varrendo {len(roots)} raiz(ns); base primária: {primary_base}", flush=True)
    physical = scan_physical(roots, primary_base, index_by_rel)

    oficial_set = oficial_shas
    all_shas = {r["sha256_arquivo"] for r in physical}
    loose = [r for r in physical if r["sha256_arquivo"] not in oficial_set]
    loose_shas = {r["sha256_arquivo"] for r in loose}
    paths_in_oficial = [r for r in physical if r["sha256_arquivo"] in oficial_set]
    index_sha_values = set(index_by_rel.values())

    by_ext = Counter(r["ext"] for r in physical)
    loose_by_ext = Counter(r["ext"] for r in loose)
    loose_by_root = Counter(r["storage_root"] for r in loose)

    report = {
        "generated_at": utc,
        "storage_roots_scanned": [{"path": str(p), "label": lab} for p, lab in roots],
        "primary_base": str(primary_base),
        "oficial_sha_count": len(oficial_shas),
        "physical_files_total": len(physical),
        "physical_unique_sha_on_disk": len(all_shas),
        "physical_paths_sha_in_oficial": len(paths_in_oficial),
        "physical_paths_sha_not_oficial": len(loose),
        "physical_unique_sha_not_oficial": len(loose_shas),
        "physical_unique_sha_in_oficial_on_disk": len(all_shas & oficial_set),
        "loose_paths_indexed_sha": sum(1 for r in loose if r["sha_from_index"]),
        "loose_unique_sha_in_index": len(loose_shas & index_sha_values),
        "duplicate_paths_same_sha_as_oficial": len(paths_in_oficial) - len({r["sha256_arquivo"] for r in paths_in_oficial}),
        "by_ext_all": dict(by_ext),
        "by_ext_loose": dict(loose_by_ext),
        "by_root_loose": dict(loose_by_root),
        "preview_loose_first_20": [
            {"arquivo_rel": r["arquivo_rel"], "sha256_arquivo": r["sha256_arquivo"][:16] + "…"}
            for r in loose[:20]
        ],
    }

    out_json = Path(args.out_json)
    out_md = Path(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    md_lines = [
        f"# Delta físico vs OFICIAL (`{utc}`)",
        "",
        f"- **Raízes varridas:** {len(roots)}",
        f"- **SHAs OFICIAIS (manifest):** {report['oficial_sha_count']}",
        f"- **Ficheiros físicos (pdf/jpg/jpeg):** {report['physical_files_total']}",
        f"- **SHAs únicos no disco:** {report['physical_unique_sha_on_disk']}",
        f"- **Caminhos cujo SHA já é OFICIAL:** {report['physical_paths_sha_in_oficial']}",
        f"- **Caminhos soltos (SHA nunca promovido a OFICIAL):** **{report['physical_paths_sha_not_oficial']}**",
        f"- **SHAs únicos soltos:** **{report['physical_unique_sha_not_oficial']}**",
        f"- **Soltos com SHA vindo do índice (já processados, não OFICIAL):** {report['loose_paths_indexed_sha']} caminhos",
        f"- **Cópias duplicadas no disco (mesmo SHA que OFICIAL):** {report['duplicate_paths_same_sha_as_oficial']}",
        "",
        "## Por extensão (todos / soltos)",
        f"- Todos: {report['by_ext_all']}",
        f"- Soltos: {report['by_ext_loose']}",
        "",
        "## Por raiz (soltos)",
        *[f"- `{k}`: {v}" for k, v in sorted(report["by_root_loose"].items())],
    ]
    out_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    queue_path = None
    if args.emit_queue_csv:
        bn = int(args.emit_queue_csv)
        take = max(1, int(args.take))
        pool: list[dict] = []
        pendency_n = 0
        infra_n = 0
        if args.force_include_pendencies:
            infra_rows = collect_infra_retry_rows(REVIEW_DIR, oficial_set)
            infra_n = len(infra_rows)
            pool.extend(infra_rows)
            pendencies = collect_pendency_rows(REVIEW_DIR, oficial_set)
            pendency_n = len(pendencies)
            pool.extend(pendencies)
        pool.extend(loose)
        slice_rows = pick_queue_rows(pool, take, unique_sha=True)
        queue_path = REVIEW_DIR / f"pass1_v2_block_{bn:02d}.csv"
        policy = "sha_not_in_master_oficial"
        if args.force_include_pendencies:
            policy += "|force_include_pendencies"
        reason_base = (
            f"massa_inedita_fisica_block_{bn:02d}|from=scan_physical_delta_vs_oficial|"
            f"policy={policy}|generated_offline"
        )
        with queue_path.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["arquivo_rel", "sha256_arquivo", "queue_type", "reason", "sort"])
            for i, r in enumerate(slice_rows, start=1):
                qt = _t(r.get("queue_type")) or "NEW_UNPROCESSED_PASS1"
                rs = _t(r.get("reason")) or reason_base
                if args.force_include_pendencies and qt.startswith("PENDENCY"):
                    rs = f"{rs}|{reason_base}"
                w.writerow([r["arquivo_rel"], r["sha256_arquivo"], qt, rs, i])
        report["pendency_candidates"] = pendency_n
        report["infra_retry_candidates"] = infra_n
        report["queue_csv"] = str(queue_path.relative_to(REPO_ROOT))
        report["queue_lines"] = len(slice_rows)
        out_json.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps({k: report[k] for k in report if k != "preview_loose_first_20"}, ensure_ascii=False, indent=2))
    if queue_path:
        print(f"Fila: {queue_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
