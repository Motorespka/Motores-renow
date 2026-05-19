#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Varre o acervo físico em busca de formatos que o pipeline 7C não processa
(ZIP/RAR/7Z, DOC/DOCX) e imprime relatório no terminal.
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
MONO_ROOT = REPO_ROOT.parent
DEFAULT_ROOT = MONO_ROOT / "_extraidos_motor"

ARCHIVE_EXTS = {".zip", ".rar", ".7z"}
DOC_EXTS = {".doc", ".docx"}
MEDIA_READABLE = {".pdf", ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}


def _fmt_size(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    if n < 1024 * 1024 * 1024:
        return f"{n / (1024 * 1024):.1f} MB"
    return f"{n / (1024 * 1024 * 1024):.2f} GB"


def scan_root(root: Path) -> dict:
    archives: list[tuple[str, int]] = []
    docs: list[tuple[str, int]] = []
    readable: list[str] = []
    other: list[tuple[str, str]] = []
    total_bytes_arch = 0
    total_bytes_doc = 0

    for fp in root.rglob("*"):
        if not fp.is_file():
            continue
        ext = fp.suffix.lower()
        try:
            rel = str(fp.relative_to(root)).replace("/", "\\")
            size = fp.stat().st_size
        except OSError:
            continue

        if ext in ARCHIVE_EXTS:
            archives.append((rel, size))
            total_bytes_arch += size
        elif ext in DOC_EXTS:
            docs.append((rel, size))
            total_bytes_doc += size
        elif ext in MEDIA_READABLE:
            readable.append(rel)
        elif ext:
            other.append((rel, ext))

    return {
        "root": str(root.resolve()),
        "archives": archives,
        "docs": docs,
        "readable": readable,
        "other": other,
        "total_bytes_arch": total_bytes_arch,
        "total_bytes_doc": total_bytes_doc,
    }


def print_report(data: dict, *, max_paths: int) -> None:
    arch = data["archives"]
    docs = data["docs"]
    ignored_n = len(arch) + len(docs)
    ignored_bytes = data["total_bytes_arch"] + data["total_bytes_doc"]

    print("=" * 72)
    print("RADAR DE FORMATOS IGNORADOS — Acervo físico")
    print("=" * 72)
    print(f"Raiz: {data['root']}")
    print()
    print("## Resumo")
    print(f"| Tipo | Quantidade | Volume |")
    print(f"| :--- | ---: | ---: |")
    print(f"| Arquivos compactados (.zip, .rar, .7z) | **{len(arch)}** | {_fmt_size(data['total_bytes_arch'])} |")
    print(f"| Documentos Word (.doc, .docx) | **{len(docs)}** | {_fmt_size(data['total_bytes_doc'])} |")
    print(f"| **Total formatos não lidos pelo pipeline** | **{ignored_n}** | **{_fmt_size(ignored_bytes)}** |")
    print(f"| Arquivos legíveis pelo pipeline (pdf/jpg/…) | {len(data['readable'])} | — |")
    print(f"| Outras extensões no acervo | {len(data['other'])} | — |")
    print()

    by_arch_ext: dict[str, int] = defaultdict(int)
    for rel, _ in arch:
        by_arch_ext[Path(rel).suffix.lower()] += 1
    if by_arch_ext:
        print("### Compactados por extensão")
        for ext, n in sorted(by_arch_ext.items()):
            print(f"- `{ext}`: {n}")
        print()

    def _print_paths(title: str, items: list[tuple[str, int]]) -> None:
        print(f"## {title} ({len(items)})")
        if not items:
            print("(nenhum)")
            print()
            return
        show = items if max_paths <= 0 else items[:max_paths]
        for rel, size in sorted(show, key=lambda x: x[0].lower()):
            print(f"- `{rel}` ({_fmt_size(size)})")
        if max_paths > 0 and len(items) > max_paths:
            print(f"- … e mais **{len(items) - max_paths}** arquivo(s)")
        print()

    _print_paths("Arquivos .zip / .rar / .7z", arch)
    _print_paths("Arquivos .doc / .docx", docs)

    if data["other"]:
        by_other = defaultdict(int)
        for _, ext in data["other"]:
            by_other[ext] += 1
        print("## Outras extensões (amostra)")
        for ext, n in sorted(by_other.items(), key=lambda x: -x[1])[:15]:
            print(f"- `{ext}`: {n}")
        print()

    print("=" * 72)
    if ignored_n:
        print(
            f"NOTA: Existem **{ignored_n}** arquivo(s) em formatos que o extrator 7C "
            "não abre diretamente. Podem explicar parte do gap vs. meta ~1.600 "
            "se ainda estiverem compactados ou só em Word."
        )
    else:
        print("Nenhum ZIP/RAR/7Z ou DOC/DOCX encontrado na raiz varrida.")
    print("=" * 72)


def main() -> int:
    ap = argparse.ArgumentParser(description="Lista ZIP/RAR/7Z e DOC/DOCX no acervo físico.")
    ap.add_argument(
        "--root",
        type=Path,
        default=DEFAULT_ROOT,
        help="Raiz do acervo (default: _extraidos_motor).",
    )
    ap.add_argument(
        "--max-paths",
        type=int,
        default=40,
        help="Máximo de caminhos listados por categoria (0 = todos).",
    )
    args = ap.parse_args()
    root = args.root.expanduser().resolve()
    if not root.is_dir():
        print(f"ERRO: diretório inexistente: {root}", file=sys.stderr)
        return 2
    data = scan_root(root)
    print_report(data, max_paths=int(args.max_paths))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
