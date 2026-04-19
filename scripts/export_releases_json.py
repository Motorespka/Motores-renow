"""
Valida `data/releases.json` (fonte única de release notes para Streamlit + Next.js).

Executar na raiz do repositório: python scripts/export_releases_json.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    path = root / "data" / "releases.json"
    if not path.is_file():
        print("MISSING:", path, file=sys.stderr)
        sys.exit(1)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print("INVALID JSON:", exc, file=sys.stderr)
        sys.exit(1)
    if not isinstance(raw.get("changelog"), list):
        print("MISSING key: changelog", file=sys.stderr)
        sys.exit(1)
    dev = raw.get("dev_preview_changelog")
    if dev is not None and not isinstance(dev, list):
        print("INVALID dev_preview_changelog", file=sys.stderr)
        sys.exit(1)
    print("OK:", path, "| entries:", len(raw["changelog"]), "| dev:", len(dev or []))


if __name__ == "__main__":
    main()
