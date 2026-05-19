#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prestação de contas: varre o acervo físico bruto (_extraidos_motor), calcula SHA
e classifica cada arquivo/caminho contra manifestos e artefatos da Fase 7C.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
REVIEW_DIR = REPO_ROOT / "exports" / "review"
MONO_ROOT = REPO_ROOT.parent
PRIMARY_ACERVO = MONO_ROOT / "_extraidos_motor"
MEDIA_EXTS = {".pdf", ".jpg", ".jpeg"}
META_TARGET = 1600


def _t(v) -> str:
    return "" if v is None else str(v).strip()


def _norm_rel(p: str) -> str:
    return p.replace("/", "\\").strip().lower()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().lower()


def load_index_shas(index_path: Path) -> dict[str, str]:
    m: dict[str, str] = {}
    if not index_path.is_file():
        return m
    with index_path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            ip = _t(row.get("image_path")).replace("/", "\\")
            sh = _t(row.get("sha256_arquivo")).lower()
            if ip and sh:
                m[_norm_rel(ip)] = sh
    return m


def load_oficial_manifest(manifest_path: Path) -> tuple[set[str], dict[str, str], dict[str, str]]:
    """oficial_shas, sha->rel canônico, rel->sha"""
    oficial_shas: set[str] = set()
    sha_to_rel: dict[str, str] = {}
    rel_to_sha: dict[str, str] = {}
    with manifest_path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if _t(row.get("status_release")).upper() != "OFICIAL":
                continue
            sh = _t(row.get("sha256_arquivo")).lower()
            rel = _t(row.get("arquivo_rel")).replace("/", "\\")
            if not sh:
                continue
            oficial_shas.add(sh)
            if sh not in sha_to_rel:
                sha_to_rel[sh] = rel
            rel_to_sha[_norm_rel(rel)] = sh
    return oficial_shas, sha_to_rel, rel_to_sha


def _block_num_from_name(name: str) -> int:
    m = re.search(r"block_(\d+)", name, re.I)
    return int(m.group(1)) if m else 0


def load_rel_to_sha_maps(
    review_dir: Path,
    rel_to_sha_scan: dict[str, str],
) -> dict[str, str]:
    """rel_norm -> sha (scan + manifest + índice)."""
    merged = dict(rel_to_sha_scan)
    manifest = review_dir / "master_release_v2_manifest.csv"
    if manifest.is_file():
        with manifest.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                rel = _t(row.get("arquivo_rel")).replace("/", "\\")
                sh = _t(row.get("sha256_arquivo")).lower()
                if rel and sh:
                    merged[_norm_rel(rel)] = sh
    return merged


def load_pipeline_status_by_sha(
    review_dir: Path,
    rel_to_sha: dict[str, str],
) -> dict[str, dict[str, str]]:
    """Último status conhecido por SHA (maior bloco / artefato mais recente)."""
    by_sha: dict[str, dict[str, str]] = {}

    def _merge(sh: str, row: dict[str, str], src: str, prio: int) -> None:
        sh = sh.lower()
        if not sh:
            return
        cur = by_sha.get(sh)
        if cur and int(cur.get("_prio", "0")) > prio:
            return
        by_sha[sh] = {
            "_prio": str(prio),
            "source": src,
            "status_extract": _t(row.get("status_revisao")),
            "status_categoria": _t(row.get("categoria_pos_auditoria") or row.get("categoria")),
            "motivos": _t(row.get("motivos_bloqueio")),
            "arquivo": _t(row.get("arquivo") or row.get("arquivo_rel")).replace("/", "\\"),
        }

    def _row_sha(row: dict[str, str]) -> str:
        sh = _t(row.get("sha256_arquivo")).lower()
        if sh:
            return sh
        ar = _t(row.get("arquivo") or row.get("arquivo_rel")).replace("/", "\\")
        return rel_to_sha.get(_norm_rel(ar), "")

    globs = [
        "extraidos_motor_*_candidates.csv",
        "extraidos_motor_*_flash_candidates.csv",
        "extraidos_motor_*_flash_categorized.csv",
        "extraidos_motor_*_flash_categorized_manual_review.csv",
    ]
    for pattern in globs:
        for pth in sorted(review_dir.glob(pattern)):
            if "safe_green" in pth.name or "reprocess_no_keys" in pth.name:
                continue
            prio = _block_num_from_name(pth.name)
            if "flash" in pth.name:
                prio += 1000
            if "categorized" in pth.name:
                prio += 2000
            with pth.open(encoding="utf-8-sig", newline="") as f:
                for row in csv.DictReader(f):
                    sh = _row_sha(row)
                    if not sh:
                        continue
                    _merge(sh, row, pth.name, prio)

    excl = review_dir / "master_release_v2_excluidos.csv"
    if excl.is_file():
        with excl.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                sh = _t(row.get("sha256_arquivo")).lower()
                if not sh:
                    rel = _t(row.get("arquivo_rel"))
                    sh = rel_to_sha.get(_norm_rel(rel), "")
                if sh:
                    _merge(
                        sh,
                        {
                            "status_revisao": "VERMELHO_REVISAR",
                            "categoria_pos_auditoria": "VERMELHO_DADO_RUIM",
                            "motivos_bloqueio": _t(row.get("motivos") or row.get("motivo_exclusao")),
                            "arquivo_rel": _t(row.get("arquivo_rel")),
                        },
                        excl.name,
                        3000,
                    )

    return by_sha


def classify_non_oficial_sha(sh: str, pipe: dict[str, dict[str, str]] | None) -> str:
    info = (pipe or {}).get(sh.lower(), {})
    cat = _t(info.get("status_categoria")).upper()
    ext = _t(info.get("status_extract")).upper()
    blob = f"{cat} {ext} {_t(info.get('motivos'))}".upper()

    if "VERMELHO" in cat or "VERMELHO" in ext:
        return "rejeitado_vermelho"
    if "AMARELO" in cat or "AMARELO" in ext:
        return "quarentena_amarelo"
    if "VERDE" in cat and "VERDE_SEGURO" not in cat:
        return "quarentena_amarelo"
    if any(x in blob for x in ("PAUSA_INFRA", "NO_KEYS", "QUOTA")):
        return "quarentena_amarelo"
    if info:
        return "quarentena_amarelo"
    return "nao_processado"


def scan_acervo(primary: Path, index_by_rel: dict[str, str]) -> list[dict]:
    rows: list[dict] = []
    for fp in primary.rglob("*"):
        if not fp.is_file() or fp.suffix.lower() not in MEDIA_EXTS:
            continue
        rel = str(fp.relative_to(primary)).replace("/", "\\")
        rel_k = _norm_rel(rel)
        sh = index_by_rel.get(rel_k) or sha256_file(fp)
        rows.append(
            {
                "arquivo_rel": rel,
                "sha256_arquivo": sh,
                "ext": fp.suffix.lower(),
                "sha_from_index": bool(index_by_rel.get(rel_k)),
            }
        )
    return rows


def build_report(
    file_rows: list[dict],
    oficial_shas: set[str],
    sha_to_rel: dict[str, str],
    rel_to_sha: dict[str, str],
    pipe: dict[str, dict[str, str]],
) -> dict:
    unique_shas = {r["sha256_arquivo"] for r in file_rows}
    paths_by_sha: dict[str, list[str]] = defaultdict(list)
    for r in file_rows:
        paths_by_sha[r["sha256_arquivo"]].append(r["arquivo_rel"])

    duplicate_paths = 0
    oficial_canonical_paths = 0
    path_bucket = Counter()

    for r in file_rows:
        sh = r["sha256_arquivo"]
        rel = r["arquivo_rel"]
        rel_k = _norm_rel(rel)
        if sh in oficial_shas:
            canon = sha_to_rel.get(sh, "")
            if canon and _norm_rel(canon) == rel_k:
                path_bucket["oficial_canonical_path"] += 1
                oficial_canonical_paths += 1
            else:
                path_bucket["duplicate_clone_path"] += 1
                duplicate_paths += 1
        else:
            bucket = classify_non_oficial_sha(sh, pipe)
            path_bucket[bucket + "_path"] += 1

    sha_bucket = Counter()
    for sh in unique_shas:
        if sh in oficial_shas:
            sha_bucket["oficial_sha"] += 1
        else:
            sha_bucket[classify_non_oficial_sha(sh, pipe)] += 1

    total_paths = len(file_rows)
    total_unique_sha = len(unique_shas)
    n_oficial = len(oficial_shas & unique_shas)
    n_dup_sha = sum(1 for sh, paths in paths_by_sha.items() if len(paths) > 1)
    n_dup_extra_paths = sum(len(paths) - 1 for paths in paths_by_sha.values() if len(paths) > 1)

    n_rejeitado = sha_bucket.get("rejeitado_vermelho", 0)
    n_quarentena = sha_bucket.get("quarentena_amarelo", 0)
    n_cauda = sha_bucket.get("nao_processado", 0)

    checksum_sha = n_oficial + n_rejeitado + n_quarentena + n_cauda

    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "acervo_root": str(PRIMARY_ACERVO.resolve()),
        "meta_target_1600": META_TARGET,
        "total_paths": total_paths,
        "total_unique_sha": total_unique_sha,
        "paths_duplicate_clones": duplicate_paths,
        "paths_oficial_canonical": oficial_canonical_paths,
        "paths_non_oficial": total_paths - duplicate_paths - oficial_canonical_paths,
        "sha_oficial": n_oficial,
        "sha_oficial_manifest_count": len(oficial_shas),
        "sha_rejeitado_vermelho": n_rejeitado,
        "sha_quarentena_amarelo": n_quarentena,
        "sha_nao_processado_cauda": n_cauda,
        "sha_with_multiple_paths": n_dup_sha,
        "extra_paths_from_duplication": n_dup_extra_paths,
        "checksum_unique_sha_buckets": checksum_sha,
        "sha_bucket": dict(sha_bucket),
        "path_bucket": dict(path_bucket),
        "gap_vs_meta_1600_paths": META_TARGET - total_paths,
        "gap_vs_meta_1600_unique_sha": META_TARGET - total_unique_sha,
    }


def render_markdown(rep: dict) -> str:
    o = rep
    lines = [
        "# Prestação de Contas — Acervo Físico vs Manifesto OFICIAL",
        "",
        f"Gerado em: `{o['generated_at']}`",
        f"Raiz varrida: `{o['acervo_root']}`",
        "",
        "## Tabela de Prestação de Contas",
        "",
        "| Métrica | Quantidade | Notas |",
        "| :--- | ---: | :--- |",
        f"| **Total de Arquivos Físicos no HD (acervo `_extraidos_motor`)** | **{o['total_paths']:,}** | PDF/JPG/JPEG em toda a árvore |",
        f"| SHAs únicos no disco | **{o['total_unique_sha']:,}** | Motores distintos por hash |",
        f"| Arquivos Duplicados/Clones (mesmo SHA, 2ª+ cópia) | **{o['paths_duplicate_clones']:,}** | Aglutinados — não geram motor repetido |",
        f"| Caminhos canônicos OFICIAIS (1 por motor no manifesto) | **{o['paths_oficial_canonical']:,}** | Alinhado ao path do manifesto |",
        f"| **Motores OFICIAIS (SHA únicos no manifesto)** | **{o['sha_oficial_manifest_count']:,}** | `master_release_v2_manifest.csv` |",
        f"| Rejeitados/Lixo (**VERMELHO**, SHA não oficial) | **{o['sha_rejeitado_vermelho']:,}** | Reguladores, esquemas vazios, dado ruim |",
        f"| Quarentena (**AMARELO**, SHA não oficial) | **{o['sha_quarentena_amarelo']:,}** | Ventiladores pendentes, dados incompletos |",
        f"| **Não Processados (cauda restante, SHA)** | **{o['sha_nao_processado_cauda']:,}** | Nunca passaram no pipeline 7C |",
        "",
        "### Verificação matemática (SHAs únicos no acervo)",
        "",
        f"- OFICIAL + Rejeitados + Quarentena + Cauda = "
        f"{o['sha_oficial']} + {o['sha_rejeitado_vermelho']} + {o['sha_quarentena_amarelo']} + "
        f"{o['sha_nao_processado_cauda']} = **{o['checksum_unique_sha_buckets']}** "
        f"(total único no disco: **{o['total_unique_sha']}**)",
        "",
        "### Verificação matemática (caminhos físicos)",
        "",
        f"- Canônicos OFICIAIS + Clones duplicados + Caminhos não-oficiais = "
        f"{o['paths_oficial_canonical']} + {o['paths_duplicate_clones']} + {o['paths_non_oficial']} "
        f"= **{o['total_paths']}**",
        "",
        "## Meta ~1.600 (referência de negócio)",
        "",
        f"- Meta declarada no master build: **{o['meta_target_1600']}** cálculos úteis.",
        f"- Diferença meta − arquivos físicos: **{o['gap_vs_meta_1600_paths']:+d}**",
        f"- Diferença meta − SHAs únicos: **{o['gap_vs_meta_1600_unique_sha']:+d}**",
        "",
        "> O acervo físico tem **mais caminhos** que 1.600 porque inclui pastas Drive (`drive-download-*`), "
        "réplicas do mesmo PDF e fotos auxiliares. A base **OFICIAL** conta **motores únicos por SHA**, não cópias de pasta.",
        "",
        "## Detalhe por bucket (SHA)",
        "",
    ]
    for k, v in sorted(o.get("sha_bucket", {}).items()):
        lines.append(f"- `{k}`: {v}")
    lines.append("")
    lines.append("## Detalhe por bucket (caminhos)")
    lines.append("")
    for k, v in sorted(o.get("path_bucket", {}).items()):
        lines.append(f"- `{k}`: {v}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="Auditoria prestação de contas acervo ~1600 vs OFICIAL.")
    ap.add_argument(
        "--acervo-root",
        type=Path,
        default=PRIMARY_ACERVO,
        help="Raiz do acervo bruto (default: _extraidos_motor).",
    )
    ap.add_argument(
        "--manifest",
        type=Path,
        default=REVIEW_DIR / "master_release_v2_manifest.csv",
    )
    ap.add_argument(
        "--out-md",
        type=Path,
        default=REVIEW_DIR / "audit_1600_prestacao_contas.md",
    )
    ap.add_argument(
        "--out-json",
        type=Path,
        default=REVIEW_DIR / "audit_1600_prestacao_contas.json",
    )
    ap.add_argument("--no-print", action="store_true", help="Não imprimir tabela no stdout.")
    args = ap.parse_args()

    acervo = args.acervo_root.expanduser().resolve()
    if not acervo.is_dir():
        print(f"ERRO: acervo inexistente: {acervo}", file=sys.stderr)
        return 2

    index_path = REVIEW_DIR / "processed_image_index.csv"
    index_by_rel = load_index_shas(index_path)
    oficial_shas, sha_to_rel, rel_to_sha_manifest = load_oficial_manifest(args.manifest.resolve())

    print(f"Varrendo {acervo} …", flush=True)
    file_rows = scan_acervo(acervo, index_by_rel)
    rel_to_sha_scan = {_norm_rel(r["arquivo_rel"]): r["sha256_arquivo"] for r in file_rows}
    rel_to_sha = load_rel_to_sha_maps(REVIEW_DIR, rel_to_sha_scan)
    rel_to_sha.update(rel_to_sha_manifest)
    pipe = load_pipeline_status_by_sha(REVIEW_DIR, rel_to_sha)
    rep = build_report(file_rows, oficial_shas, sha_to_rel, rel_to_sha, pipe)

    md = render_markdown(rep)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(md, encoding="utf-8")
    args.out_json.write_text(json.dumps(rep, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if not args.no_print:
        start = md.find("## Tabela de Prestação de Contas")
        end = md.find("## Meta ~1.600")
        if start >= 0 and end > start:
            print(md[start:end].strip())
        else:
            print(md)

    print(f"\nRelatório: {args.out_md}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
