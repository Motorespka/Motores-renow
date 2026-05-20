#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Descompacta o cofre (ZIP/RAR/7Z) do monorepo para _extraidos_motor/lote2_descompactados/.
Extrai apenas PDF, JPG/JPEG e PNG; ignora __MACOSX e lixo de sistema.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import zipfile
from collections import Counter
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
MONO_ROOT = REPO_ROOT.parent
DEFAULT_OUT = MONO_ROOT / "_extraidos_motor" / "lote2_descompactados"

ARCHIVE_EXTS = {".zip", ".rar", ".7z"}
MEDIA_EXTS = {".pdf", ".jpg", ".jpeg", ".png"}
SKIP_DIR_PARTS = {"__MACOSX", ".git", "node_modules", "__pycache__", ".venv", "venv"}
SKIP_FILE_NAMES = {".ds_store", "thumbs.db", "desktop.ini"}


def _should_skip_member(name: str) -> bool:
    norm = name.replace("\\", "/").strip("/")
    if not norm:
        return True
    parts = Path(norm).parts
    if any(p in SKIP_DIR_PARTS for p in parts):
        return True
    base = Path(norm).name
    if base.startswith("._"):
        return True
    if base.lower() in SKIP_FILE_NAMES:
        return True
    return False


def _is_media(name: str) -> bool:
    return Path(name).suffix.lower() in MEDIA_EXTS


def discover_archives(mono: Path, *, include_audit: bool) -> list[Path]:
    """Localiza compactados em Calculos/, raiz do monorepo e Motores-renow."""
    roots: list[Path] = [
        mono / "Calculos",
        mono,
        REPO_ROOT,
    ]
    found: dict[Path, Path] = {}
    for root in roots:
        if not root.is_dir():
            continue
        try:
            it = root.rglob("*")
        except OSError:
            continue
        for fp in it:
            if not fp.is_file():
                continue
            if fp.suffix.lower() not in ARCHIVE_EXTS:
                continue
            low = str(fp).lower()
            if any(x in low for x in ("\\node_modules\\", "\\.git\\", "\\__pycache__\\")):
                continue
            if not include_audit and "audit_reports" in low and "cursor_package" in low:
                continue
            found[fp.resolve()] = fp
    return sorted(found.values(), key=lambda p: str(p).lower())


def _dest_path(out_dir: Path, archive: Path, member_name: str) -> Path:
    norm = member_name.replace("\\", "/").lstrip("/")
    parts = [p for p in Path(norm).parts if p not in ("", ".", "..")]
    return out_dir / archive.stem / Path(*parts)


def extract_zip(archive: Path, out_dir: Path, stats: Counter) -> None:
    with zipfile.ZipFile(archive) as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            name = info.filename
            if _should_skip_member(name) or not _is_media(name):
                stats["archive_members_skipped"] += 1
                continue
            dest = _dest_path(out_dir, archive, name)
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.is_file():
                stats["media_already_present"] += 1
                continue
            with zf.open(info) as src, dest.open("wb") as dst:
                shutil.copyfileobj(src, dst)
            ext = dest.suffix.lower()
            stats["media_extracted"] += 1
            stats[f"extracted_{ext}"] += 1


def _extract_via_7z(archive: Path, out_dir: Path, stats: Counter) -> bool:
    seven = shutil.which("7z") or shutil.which("7z.exe")
    if not seven:
        return False
    staging = out_dir / "_staging" / archive.stem
    staging.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            [seven, "x", "-y", f"-o{staging}", str(archive)],
            check=True,
            capture_output=True,
        )
    except (subprocess.CalledProcessError, OSError):
        return False
    for fp in staging.rglob("*"):
        if not fp.is_file() or not _is_media(fp.name):
            continue
        rel = fp.relative_to(staging)
        if _should_skip_member(str(rel)):
            continue
        dest = out_dir / archive.stem / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.is_file():
            stats["media_already_present"] += 1
            continue
        shutil.copy2(fp, dest)
        stats["media_extracted"] += 1
        stats[f"extracted_{dest.suffix.lower()}"] += 1
    shutil.rmtree(staging, ignore_errors=True)
    return True


def extract_archive(archive: Path, out_dir: Path, stats: Counter) -> None:
    ext = archive.suffix.lower()
    stats["archives_processed"] += 1
    try:
        if ext == ".zip":
            extract_zip(archive, out_dir, stats)
            return
        if _extract_via_7z(archive, out_dir, stats):
            return
        stats["archives_unsupported"] += 1
        print(f"AVISO: sem extrator para {archive} (.rar/.7z requer 7z no PATH)", file=sys.stderr)
    except zipfile.BadZipFile as e:
        stats["archives_failed"] += 1
        print(f"ERRO ZIP: {archive}: {e}", file=sys.stderr)
    except OSError as e:
        stats["archives_failed"] += 1
        print(f"ERRO: {archive}: {e}", file=sys.stderr)


def print_report(
    archives: list[Path],
    out_dir: Path,
    stats: Counter,
    *,
    pdf_jpg_only: bool,
) -> None:
    pdf = stats.get("extracted_.pdf", 0)
    jpg = stats.get("extracted_.jpg", 0) + stats.get("extracted_.jpeg", 0)
    png = stats.get("extracted_.png", 0)
    headline = pdf + jpg if pdf_jpg_only else stats["media_extracted"]

    print("=" * 72)
    print("INGESTÃO COFRE OCULTO — lote2_descompactados")
    print("=" * 72)
    print(f"Destino: {out_dir.resolve()}")
    print(f"Arquivos compactados encontrados: {len(archives)}")
    print(f"Arquivos compactados processados: {stats['archives_processed']}")
    print()
    print("## Mídia extraída (novos ficheiros no disco)")
    print(f"| Métrica | Valor |")
    print(f"| :--- | ---: |")
    print(f"| **Total PDF+JPG+JPEG novos** | **{pdf + jpg}** |")
    print(f"| PDF | {pdf} |")
    print(f"| JPG/JPEG | {jpg} |")
    print(f"| PNG | {png} |")
    print(f"| **Total mídia (incl. PNG)** | **{stats['media_extracted']}** |")
    print(f"| Já existiam no destino (ignorados) | {stats['media_already_present']} |")
    print(f"| Membros não-mídia/lixo ignorados no ZIP | {stats['archive_members_skipped']} |")
    if stats["archives_failed"]:
        print(f"| ZIPs com falha | {stats['archives_failed']} |")
    if stats["archives_unsupported"]:
        print(f"| Compactados sem extrator | {stats['archives_unsupported']} |")
    print()
    print("## Compactados processados")
    for arch in archives:
        try:
            rel = arch.relative_to(MONO_ROOT)
        except ValueError:
            rel = arch
        mb = arch.stat().st_size / (1024 * 1024)
        print(f"- `{rel}` ({mb:.2f} MB)")
    print("=" * 72)
    print(f"RESUMO: {headline} novo(s) PDF/JPG extraido(s) dos ZIPs -> {out_dir.name}/")
    print("=" * 72)


def main() -> int:
    ap = argparse.ArgumentParser(description="Extrai PDF/JPG/PNG de ZIPs do monorepo.")
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    ap.add_argument(
        "--include-audit-zip",
        action="store_true",
        help="Inclui audit_reports/cursor_package_*.zip (default: só cofre Calculos/Drive).",
    )
    ap.add_argument("--dry-run", action="store_true", help="Só lista ZIPs e membros mídia, não escreve.")
    args = ap.parse_args()

    out_dir = args.out_dir.expanduser().resolve()
    archives = discover_archives(MONO_ROOT, include_audit=bool(args.include_audit_zip))
    if not archives:
        print("Nenhum .zip/.rar/.7z encontrado no monorepo.", file=sys.stderr)
        return 1

    stats: Counter = Counter()
    if args.dry_run:
        for arch in archives:
            if arch.suffix.lower() != ".zip":
                stats["archives_unsupported"] += 1
                continue
            with zipfile.ZipFile(arch) as zf:
                for info in zf.infolist():
                    if info.is_dir() or _should_skip_member(info.filename):
                        continue
                    if _is_media(info.filename):
                        stats["media_extracted"] += 1
        print_report(archives, out_dir, stats, pdf_jpg_only=True)
        print("(dry-run: nada foi escrito no disco)")
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    for arch in archives:
        print(f"Extraindo: {arch.name} …", flush=True)
        extract_archive(arch, out_dir, stats)

    print_report(archives, out_dir, stats, pdf_jpg_only=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
