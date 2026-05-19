#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reprocessa blocos PASS1-v2 da cauda (B58/B59…) aplicando tail_mutirao_correcoes.json:
  audit → categorize → reconcile (por bloco).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
REVIEW_DIR = REPO_ROOT / "exports" / "review"
DEFAULT_CORRECOES = REPO_ROOT / "metadata" / "sidecars" / "tail_mutirao_correcoes.json"


def _run(cmd: list[str], *, label: str) -> int:
    print(f"\n=== {label} ===", flush=True)
    print(" ".join(cmd), flush=True)
    r = subprocess.run(cmd, cwd=str(REPO_ROOT))
    if r.returncode != 0:
        print(f"ERRO: {label} exit={r.returncode}", file=sys.stderr)
    return r.returncode


def _block_paths(bn: int) -> dict[str, Path]:
    stem = f"extraidos_motor_fase7a_pass1_v2_block_{bn:02d}_flash"
    return {
        "candidates": REVIEW_DIR / f"{stem}_candidates.csv",
        "jsonl": REVIEW_DIR / f"{stem}_candidates.jsonl",
        "quality": REVIEW_DIR / f"gemini_extraction_quality_{stem}.csv",
        "categorized": REVIEW_DIR / f"{stem}_categorized.csv",
        "queue": REVIEW_DIR / f"pass1_v2_block_{bn:02d}.csv",
    }


def _count_csv_rows(path: Path) -> int:
    if not path.is_file():
        return 0
    import csv

    with path.open(encoding="utf-8-sig", newline="") as f:
        return sum(1 for _ in csv.DictReader(f))


def _basename(rel: str) -> str:
    return Path(rel.replace("\\", "/")).name


def _norm_rel(rel: str) -> str:
    return rel.replace("/", "\\").strip().lower()


def _load_rel_sha_map(*paths: Path) -> dict[str, str]:
    import csv

    m: dict[str, str] = {}
    for p in paths:
        if not p.is_file():
            continue
        with p.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                rel = _t(row.get("arquivo_rel") or row.get("arquivo", "")).replace("/", "\\")
                sh = _t(row.get("sha256_arquivo") or row.get("sha", "")).lower()
                if rel and sh:
                    m[_norm_rel(rel)] = sh
                    m[_basename(rel).lower()] = sh
    return m


def _t(v) -> str:
    return "" if v is None else str(v).strip()


def _ensure_queue_csv(bn: int, correcoes: Path, candidates: Path) -> Path:
    """Garante CSV fila com rel→sha para reconcile (B59 vinha vazio)."""
    import csv
    import json

    out = REVIEW_DIR / f"pass1_v2_block_{bn:02d}_mutirao_queue.csv"
    default_q = REVIEW_DIR / f"pass1_v2_block_{bn:02d}.csv"
    fallback_q = REVIEW_DIR / f"pass1_v2_block_{bn - 1:02d}.csv" if bn > 1 else default_q

    sha_map = _load_rel_sha_map(default_q, fallback_q)
    raw = json.loads(correcoes.read_text(encoding="utf-8"))
    for key, ent in raw.items():
        if key.startswith("_") or not isinstance(ent, dict):
            continue
        sh = _t(ent.get("sha")).lower()
        if sh:
            fn = _basename(_t(ent.get("file_name") or key))
            if fn:
                sha_map[fn.lower()] = sh

    rows_out: list[dict[str, str]] = []
    if candidates.is_file():
        with candidates.open(encoding="utf-8-sig", newline="") as f:
            for i, row in enumerate(csv.DictReader(f), start=1):
                ar = _t(row.get("arquivo")).replace("/", "\\")
                if not ar:
                    continue
                nk = _norm_rel(ar)
                sh = sha_map.get(nk) or sha_map.get(_basename(ar).lower(), "")
                if not sh:
                    continue
                rows_out.append(
                    {
                        "arquivo_rel": ar,
                        "sha256_arquivo": sh,
                        "queue_type": "MUTIRAO_TAIL_REPROCESS",
                        "reason": f"mutirao_sidecar_block_{bn:02d}",
                        "sort": str(i),
                    }
                )

    if not rows_out:
        print(f"ERRO: não foi possível montar fila mutirão bloco {bn}", file=sys.stderr)
        raise SystemExit(2)

    with out.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["arquivo_rel", "sha256_arquivo", "queue_type", "reason", "sort"],
        )
        w.writeheader()
        w.writerows(rows_out)
    return out


def reprocess_block(bn: int, correcoes: Path, *, dry_run: bool = False) -> int:
    paths = _block_paths(bn)
    for key in ("candidates", "jsonl"):
        if not paths[key].is_file():
            print(f"ERRO: falta {key} para bloco {bn}: {paths[key]}", file=sys.stderr)
            return 2

    n = _count_csv_rows(paths["candidates"])
    if n <= 0:
        print(f"ERRO: candidates vazio bloco {bn}", file=sys.stderr)
        return 2

    py = sys.executable
    corr_arg = ["--tail-correcoes-json", str(correcoes)]
    queue_mutirao = _ensure_queue_csv(bn, correcoes, paths["candidates"])

    steps = [
        (
            "audit",
            [
                py,
                str(SCRIPT_DIR / "audit_gemini_extraction_quality.py"),
                "--input",
                str(paths["candidates"]),
                "--jsonl-evidence",
                str(paths["jsonl"]),
                "--last",
                str(n),
                "--out",
                str(paths["quality"].with_suffix("")),
                *corr_arg,
            ],
        ),
        (
            "categorize",
            [
                py,
                str(SCRIPT_DIR / "categorize_lote_100_quality.py"),
                "--last",
                str(n),
                "--bundle-csv",
                str(paths["candidates"]),
                "--jsonl",
                str(paths["jsonl"]),
                "--quality-csv",
                str(paths["quality"]),
                "--out-prefix",
                str(paths["categorized"].with_suffix("")),
                *corr_arg,
            ],
        ),
        (
            "reconcile",
            [
                py,
                str(SCRIPT_DIR / "pass1_v2_chain_reconcile_block_offline.py"),
                "--block",
                str(bn),
                "--fase-meta",
                f"pass1_v2_mutirao_block_{bn:02d}",
                "--next-block-csv-num",
                str(bn + 1),
                "--reason-next-queue",
                f"mutirao_cauda_block_{bn + 1:02d}|from=tail_mutirao_correcoes|policy=reprocess_sidecar",
                "--queue-csv",
                str(queue_mutirao),
            ],
        ),
    ]

    if dry_run:
        print(
            json.dumps(
                {"block": bn, "rows": n, "queue": str(queue_mutirao), "steps": [s[0] for s in steps]},
                indent=2,
            )
        )
        return 0

    for label, cmd in steps:
        rc = _run(cmd, label=f"B{bn:02d} {label}")
        if rc != 0:
            return rc
    return 0


def _lift_no_auto_ban(correcoes: Path) -> list[str]:
    """Remove basenames do mutirão de NO_AUTO_PASS1_V2 (regra c do master)."""
    import json

    raw = json.loads(correcoes.read_text(encoding="utf-8"))
    basenames: set[str] = set()
    for key, ent in raw.items():
        if key.startswith("_") or not isinstance(ent, dict):
            continue
        basenames.add(_basename(_t(ent.get("file_name") or key)).lower())

    pj = REVIEW_DIR / "pass1_v2_progress.json"
    if not pj.is_file():
        return []
    j = json.loads(pj.read_text(encoding="utf-8"))
    no_auto = list(j.get("NO_AUTO_PASS1_V2_QUEUE_BASENAMES") or [])
    removed = [x for x in no_auto if _basename(_t(x)).lower() in basenames]
    if not removed:
        return []
    kept = [x for x in no_auto if _basename(_t(x)).lower() not in basenames]
    j["NO_AUTO_PASS1_V2_QUEUE_BASENAMES"] = kept
    lifted = list(j.get("MUTIRAO_TAIL_LIFTED_NO_AUTO") or [])
    for x in removed:
        if x not in lifted:
            lifted.append(x)
    j["MUTIRAO_TAIL_LIFTED_NO_AUTO"] = lifted
    pj.write_text(json.dumps(j, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return removed


def main() -> int:
    ap = argparse.ArgumentParser(description="Reprocesso mutirão cauda (audit→categorize→reconcile).")
    ap.add_argument("--blocks", default="58,59", help="Blocos separados por vírgula (ex: 58,59).")
    ap.add_argument(
        "--correcoes-json",
        type=Path,
        default=DEFAULT_CORRECOES,
        help="JSON de overrides (default: metadata/sidecars/tail_mutirao_correcoes.json).",
    )
    ap.add_argument("--dry-run", action="store_true", help="Só imprime plano, não executa.")
    args = ap.parse_args()

    correcoes = args.correcoes_json.expanduser().resolve()
    if not correcoes.is_file():
        print(f"ERRO: correcoes inexistente: {correcoes}", file=sys.stderr)
        return 2

    blocks = [int(x.strip()) for x in args.blocks.split(",") if x.strip()]
    if not blocks:
        print("ERRO: --blocks vazio", file=sys.stderr)
        return 2

    summary = {"blocks": blocks, "correcoes": str(correcoes), "results": {}}
    for bn in blocks:
        rc = reprocess_block(bn, correcoes, dry_run=args.dry_run)
        summary["results"][str(bn)] = rc
        if rc != 0:
            print(json.dumps(summary, indent=2, ensure_ascii=False))
            return rc

    if not args.dry_run:
        lifted = _lift_no_auto_ban(correcoes)
        summary["no_auto_lifted"] = lifted

    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
