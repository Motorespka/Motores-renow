#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Operação Resgate PASS1-v2 — gera `pass1_v2_block_N.csv` a partir do funil elegível do 6V
sem aplicar filtros `NO_AUTO` nem exclusão por SHAs já listados em `pass1_v2_block_*.csv`.

Uso típico (B36 com 14 linhas):

  python scripts/pass1_v2_rescue_queue_emit.py --block-csv-num 36 --take 14 --resolved-through-block 35
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
REVIEW_DIR = (REPO_ROOT / "exports" / "review").resolve()

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from pass1_v2_chain_reconcile_helpers import build_eligible_pass1_funnel  # noqa: E402


def _t(v) -> str:
    return "" if v is None else str(v).strip()


def main() -> int:
    ap = argparse.ArgumentParser(description="PASS1-v2 Operação Resgate — emite CSV de fila forçando top-N do funil 6V.")
    ap.add_argument("--block-csv-num", type=int, required=True, help="Ex.: 36 para pass1_v2_block_36.csv")
    ap.add_argument("--take", type=int, default=14, help="Máximo de PDFs na fila (default 14).")
    ap.add_argument(
        "--resolved-through-block",
        type=int,
        default=35,
        help="exclusive: merged PASS1 resolved até este bloco (default 35).",
    )
    ap.add_argument(
        "--reason",
        default="",
        help="Coluna reason; default automático operacao_rescue.",
    )
    ap.add_argument(
        "--audit-json",
        default="",
        help="Opcional: path relativo repo para JSON de relatório do resgate.",
    )
    args = ap.parse_args()

    bn = max(1, int(args.block_csv_num))
    take = max(1, int(args.take))
    through = max(1, int(args.resolved_through_block))

    utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    reason = _t(args.reason) or (
        f"operacao_rescue_pass1_block_{bn:02d}|from=eligible_funnel_fase6v|policy=relax_NO_AUTO_QUEUE_HISTORY"
        "|audit_admin|generated_offline"
    )

    eligible, funnel = build_eligible_pass1_funnel(
        REVIEW_DIR,
        prior_pass1_completed_verde_shas=set(),
        b01_through_resolved_exclusive=through,
    )

    if not eligible:
        print(json.dumps({"ok": False, "error": "funil_eligible_vazio", "eligible": 0}, ensure_ascii=False))
        return 2

    slice_rows = eligible[:take]
    out_csv = REVIEW_DIR / f"pass1_v2_block_{bn:02d}.csv"

    with out_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["arquivo_rel", "sha256_arquivo", "queue_type", "reason", "sort"])
        for i, r in enumerate(slice_rows, start=1):
            rel = _t(r.get("arquivo_rel")).replace("/", "\\")
            sha = _t(r.get("sha256_arquivo")).lower()
            w.writerow([rel, sha, "NEW_UNPROCESSED_PASS1", reason, i])

    report = {
        "ok": True,
        "generated_at": utc,
        "next_queue_csv": str(out_csv.relative_to(REPO_ROOT)),
        "eligible_funnel_tail_count": len(eligible),
        "emitted_lines": len(slice_rows),
        "resolved_through_exclusive": through,
        "reason": reason,
        "preview": [{"arquivo_rel": _t(x.get("arquivo_rel")), "sha256_arquivo": _t(x.get("sha256_arquivo"))[:16] + "…"} for x in slice_rows],
        "funnel_steps": funnel,
    }

    aj = _t(args.audit_json)
    if aj:
        p = Path(aj)
        dest = p if p.is_absolute() else (REPO_ROOT / p)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
