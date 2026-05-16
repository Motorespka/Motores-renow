#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 7B — Master release consolidado para deploy (100% offline).
7B.1: precedência dos manifests oficiais sobre a regra (d) do índice.
7B.2: PASS1-LITE V2 bloco 02 reconciliado + basenames NO_AUTO PASS1-v2 na regra (c).
7B.3: PASS1-LITE V2 bloco 03 reconciliado + basenames na regra (c).
7B.4: PASS1-LITE V2 bloco 04 reconciliado + basenames PASS1 NO_AUTO (progress).
7B.5–7B.11: blocos PASS1-v2 adicionais (B05…B11) via argumento `--phase` (B11 > B10 > B09 > …).
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
REVIEW_DIR = (REPO_ROOT / "exports" / "review").resolve()

META_DEPLOY_GAP = 1600

ISO_BASENAMES = frozenset(
    (
        "605012237.pdf",
        "605015131.pdf",
        "605016087.pdf",
        "605016201.pdf",
        "605017014.pdf",
        "605017020.pdf",
        "605017021.pdf",
        "605026002.pdf",
        "605028011.pdf",
        "605028105.pdf",
        "605028115.pdf",
        "605028315.pdf",
        "605028711.pdf",
        "605028714.pdf",
        "605028715.pdf",
        "605029010.pdf",
    )
)

PHASE_7B17 = "7b17"
PHASE_7B18 = "7b18"
PHASE_7B19 = "7b19"
PHASE_7B20 = "7b20"
PHASE_7B21 = "7b21"
PHASE_7B22 = "7b22"
PHASE_7B23 = "7b23"
PHASE_7B24 = "7b24"
PHASE_7B25 = "7b25"
PHASE_7B26 = "7b26"
PHASE_7B27 = "7b27"
PHASE_7B28 = "7b28"
PHASE_7B29 = "7b29"
PHASE_7B30 = "7b30"
PHASE_7B31 = "7b31"
PHASE_7B32 = "7b32"
PHASE_7B33 = "7b33"
PHASE_7B34 = "7b34"
PHASE_7B35 = "7b35"
PHASE_7B36 = "7b36"
PHASE_7B37 = "7b37"
PHASE_7B38 = "7b38"
PHASE_7B39 = "7b39"
PHASE_7B40 = "7b40"
PHASE_7B41 = "7b41"
PHASE_7B42 = "7b42"
PHASE_7B43 = "7b43"
PHASE_7B44 = "7b44"
PHASE_7B45 = "7b45"
PHASE_7B46 = "7b46"

# 7B.46: B46 acima de B45 — nova era inéditos (massa física solta)
PRIO_PASS1_B46 = -42
# 7B.45: B45 acima de B44 — encerramento pool resgate (prio mais baixo = ganha)
PRIO_PASS1_B45 = -41
# 7B.44: B44 acima de B43 (prio mais baixo = ganha)
PRIO_PASS1_B44 = -40
# 7B.43: B43 acima de B42 (prio mais baixo = ganha)
PRIO_PASS1_B43 = -39
# 7B.42: B42 acima de B41 (prio mais baixo = ganha)
PRIO_PASS1_B42 = -38
# 7B.41: B41 acima de B40 (prio mais baixo = ganha)
PRIO_PASS1_B41 = -37
# 7B.40: B40 acima de B39 (prio mais baixo = ganha)
PRIO_PASS1_B40 = -36
# 7B.39: B39 acima de B38 (prio mais baixo = ganha)
PRIO_PASS1_B39 = -35
# 7B.38: B38 acima de B37 (prio mais baixo = ganha)
PRIO_PASS1_B38 = -34
# 7B.37: B37 acima de B36 (prio mais baixo = ganha)
PRIO_PASS1_B37 = -33
# 7B.36: B36 acima de B35 (prio mais baixo = ganha)
PRIO_PASS1_B36 = -32
# 7B.35: B35 acima de B34 (prio mais baixo = ganha)
PRIO_PASS1_B35 = -31
# 7B.34: B34 acima de B33 (prio mais baixo = ganha)
PRIO_PASS1_B34 = -30
# 7B.33: B33 acima de B32 (prio mais baixo = ganha)
PRIO_PASS1_B33 = -29
# 7B.32: B32 acima de B31 (prio mais baixo = ganha)
PRIO_PASS1_B32 = -28
# 7B.31: B31 acima de B30 (prio mais baixo = ganha)
PRIO_PASS1_B31 = -27
# 7B.30: B30 acima de B29 (prio mais baixo = ganha)
PRIO_PASS1_B30 = -26
# 7B.29: B29 acima de B28 (prio mais baixo = ganha)
PRIO_PASS1_B29 = -25
# 7B.28: B28 acima de B27 (prio mais baixo = ganha)
PRIO_PASS1_B28 = -24
# 7B.27: B27 acima de B26 (prio mais baixo = ganha)
PRIO_PASS1_B27 = -23
# 7B.26: B26 acima de B25 (prio mais baixo = ganha)
PRIO_PASS1_B26 = -22
# 7B.25: B25 acima de B24 (prio mais baixo = ganha)
PRIO_PASS1_B25 = -21
# 7B.24: B24 acima de B23 (prio mais baixo = ganha)
PRIO_PASS1_B24 = -20
# 7B.23: B23 acima de B22 (prio mais baixo = ganha)
PRIO_PASS1_B23 = -19
# 7B.22: B22 acima de B21 (prio mais baixo = ganha)
PRIO_PASS1_B22 = -18
# Promocao manual humana (pack revisao_manual_amarelos_b14_b20_aprovados.csv).
# Acima de qualquer bloco PASS1-v2: serve para "ressuscitar" SHAs marcados AMARELO_REVISAR
# em B14-B20 cujo unico bloqueio era confianca<0.75 sem alerta blocante.
PRIO_HUMAN_PROMO_AMARELOS = -17
# 7B.21: B21 acima de B20 (prio mais baixo = ganha)
PRIO_PASS1_B21 = -16
# 7B.20: B20 acima de B19 (prio mais baixo = ganha)
PRIO_PASS1_B20 = -15
# 7B.19: B19 acima de B18 (prio mais baixo = ganha)
PRIO_PASS1_B19 = -14
# 7B.18: B18 acima de B17 (prio mais baixo = ganha)
PRIO_PASS1_B18 = -13
# 7B.17: B17 acima de B16 (prio mais baixo = ganha)
PRIO_PASS1_B17 = -12
# 7B.16: B16 acima de B15 (prio mais baixo = ganha)
PRIO_PASS1_B16 = -11
# 7B.15: B15 acima de B14 (prio mais baixo = ganha)
PRIO_PASS1_B15 = -10
# 7B.14: B14 acima de B13 (prio mais baixo = ganha)
PRIO_PASS1_B14 = -9
# 7B.13: B13 acima de B12 (prio mais baixo = ganha)
PRIO_PASS1_B13 = -8
# 7B.12: B12 acima de B11 (prio mais baixo = ganha)
PRIO_PASS1_B12 = -7
# 7B.11: B11 acima de B10 (prio mais baixo = ganha)
PRIO_PASS1_B11 = -6
# 7B.10: B10 acima de B09 (prio mais baixo = ganha)
PRIO_PASS1_B10 = -5
# 7B.9: B09 acima de B08 (prio mais baixo = ganha)
PRIO_PASS1_B09 = -4
# 7B.8: B08 acima de B07 (prio mais baixo = ganha) · B07 > B06 > …
PRIO_PASS1_B08 = -3
# 7B.7: B07 no topo (prio mais baixo = ganha) · B06 > B05 > …
PRIO_PASS1_B07 = -2
PRIO_PASS1_B06 = 2
PRIO_PASS1_B05 = 4
PRIO_PASS1_B04 = 6
PRIO_PASS1_B03 = 7
PRIO_PASS1_B02 = 8
PRIO_PASS1_B01 = 10
PRIO_RELEASE_V1 = 20
PRIO_MANIFEST_RETRY_BASE = 250  # + block_num (maior bloco ganha em desempate)
PRIO_LEGACY = 500

MANIFEST_COLUMNS = [
    "arquivo_rel",
    "sha256_arquivo",
    "melhor_status",
    "fonte_ultimo_processamento",
    "output_tag",
    "status_release",
    "fonte_release",
    "overlap_release_v1",
    "overlap_indice_verde",
    "nota_indice",
    "updated_at_indice",
]

RE_BLOCK = re.compile(r"retry_block_(\d+)", re.IGNORECASE)


def _t(v) -> str:
    return "" if v is None else str(v).strip()


def norm_rel(s: str) -> str:
    return _t(s).replace("/", "\\").lower()


def basename_lower(rel: str) -> str:
    return Path(rel.replace("\\", "/")).name.lower()


def yn_true(v: str) -> bool:
    z = _t(v).lower()
    return z in ("1", "true", "yes", "sim", "y")


def collect_alert_shas_extended(review_dir: Path) -> set[str]:
    sh: set[str] = set()
    for pattern in ("extraidos_motor_fase*_retry_block_*_alert_manifest.csv", "extraidos_motor_fase7a_*_alert_manifest.csv"):
        for pth in sorted(review_dir.glob(pattern)):
            low = pth.name.lower()
            if "extractor_key" in low:
                continue
            # PASS1-LITE V2 bloco N alert_manifest: paralelo ao resolved; A* não retira OFICIAL (regra produto).
            if "pass1_v2_block" in low and "_alert_manifest" in low:
                continue
            if not pth.is_file():
                continue
            with pth.open(encoding="utf-8-sig", newline="") as f:
                for row in csv.DictReader(f):
                    s = _t(row.get("sha256_arquivo")).lower()
                    if s:
                        sh.add(s)
    return sh


def collect_manual_shas_extended(review_dir: Path) -> set[str]:
    sh: set[str] = set()
    patterns = ("extraidos_motor_fase*_retry_block_*_manual_review.csv", "extraidos_motor_fase7a_*_manual_review.csv")
    for pattern in patterns:
        for pth in sorted(review_dir.glob(pattern)):
            low = pth.name.lower()
            if "categorized" in low:
                continue
            if not pth.is_file():
                continue
            with pth.open(encoding="utf-8-sig", newline="") as f:
                for row in csv.DictReader(f):
                    if not (_t(row.get("arquivo_rel")) or _t(row.get("arquivo"))):
                        continue
                    s = _t(row.get("sha256_arquivo")).lower()
                    if s:
                        sh.add(s)
    return sh


def forbidden_basenames_all(review_dir: Path) -> set[str]:
    out: set[str] = {basename_lower(x) for x in ISO_BASENAMES}
    pj = review_dir / "manual_review_pack_fase6w.json"
    if pj.is_file():
        try:
            dj = json.loads(pj.read_text(encoding="utf-8"))
            for it in dj.get("itens") or []:
                bn = basename_lower(_t(it.get("basename")))
                if bn:
                    out.add(bn)
        except json.JSONDecodeError:
            pass
    pj2 = review_dir / "pass1_v2_progress.json"
    if pj2.is_file():
        try:
            j = json.loads(pj2.read_text(encoding="utf-8"))
            for x in j.get("NO_AUTO_PASS1_V2_QUEUE_BASENAMES") or []:
                out.add(Path(_t(x)).name.lower())
        except json.JSONDecodeError:
            pass
    return out


def best_manifest_row(
    current: tuple[int, str, dict] | None, prio: int, tag: str, row: dict
) -> tuple[int, str, dict]:
    if current is None or prio < current[0]:
        return (prio, tag, row)
    return current


def backup_if_exists(review_dir: Path, names: list[str], ts_safe: str, phase_tag: str) -> None:
    suf = f".bak_pre_{phase_tag}_{ts_safe}"
    for name in names:
        p = review_dir / name
        if p.is_file():
            shutil.copy2(p, p.with_name(p.name + suf))


def load_official_manifest_union(review_dir: Path) -> tuple[dict[str, tuple[int, str, dict]], set[str]]:
    """
    Retorna:
      manifest_winners[sha] = (prio, fonte_release, row_base)
      sha_oficial_por_manifest = chaves
    """
    winners: dict[str, tuple[int, str, dict]] = {}

    def add_pass1_resolved(csv_path: Path, prio_val: int, tag_name: str) -> None:
        if not csv_path.is_file():
            return
        with csv_path.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                if _t(row.get("categoria_pos_auditoria")).upper() != "VERDE_SEGURO":
                    continue
                sh = _t(row.get("sha256_arquivo")).lower()
                if not sh:
                    continue
                r = {
                    "arquivo_rel": _t(row.get("arquivo_rel")).replace("/", "\\"),
                    "sha256_arquivo": sh,
                    "melhor_status": "VERDE_SEGURO",
                    "fonte_ultimo_processamento": "",
                    "output_tag": _t(row.get("output_tag") or ""),
                }
                winners[sh] = best_manifest_row(winners.get(sh), prio_val, tag_name, r)

    def add_pass1_resolved_b11_union(csv_path: Path, prio_val: int, tag_name: str) -> None:
        """B11: 11× VERDE_SEGURO + 1× VERDE_COM_ALERTA (oficial); mesmo rótulo fonte_release."""
        if not csv_path.is_file():
            return
        with csv_path.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                cat = _t(row.get("categoria_pos_auditoria")).upper()
                if cat not in ("VERDE_SEGURO", "VERDE_COM_ALERTA"):
                    continue
                sh = _t(row.get("sha256_arquivo")).lower()
                if not sh:
                    continue
                melhor = "VERDE_COM_ALERTA" if cat == "VERDE_COM_ALERTA" else "VERDE_SEGURO"
                r = {
                    "arquivo_rel": _t(row.get("arquivo_rel")).replace("/", "\\"),
                    "sha256_arquivo": sh,
                    "melhor_status": melhor,
                    "fonte_ultimo_processamento": "",
                    "output_tag": _t(row.get("output_tag") or ""),
                }
                winners[sh] = best_manifest_row(winners.get(sh), prio_val, tag_name, r)

    # 7B.46..25: blocos recentes — mesma lógica auto-detect plain/union.
    for _bn, _prio in (
        (46, PRIO_PASS1_B46),
        (45, PRIO_PASS1_B45),
        (44, PRIO_PASS1_B44),
        (43, PRIO_PASS1_B43),
        (42, PRIO_PASS1_B42),
        (41, PRIO_PASS1_B41),
        (40, PRIO_PASS1_B40),
        (39, PRIO_PASS1_B39),
        (38, PRIO_PASS1_B38),
        (37, PRIO_PASS1_B37),
        (36, PRIO_PASS1_B36),
        (35, PRIO_PASS1_B35),
        (34, PRIO_PASS1_B34),
        (33, PRIO_PASS1_B33),
        (32, PRIO_PASS1_B32),
        (31, PRIO_PASS1_B31),
        (30, PRIO_PASS1_B30),
        (29, PRIO_PASS1_B29),
        (28, PRIO_PASS1_B28),
        (27, PRIO_PASS1_B27),
        (26, PRIO_PASS1_B26),
        (25, PRIO_PASS1_B25),
    ):
        _b_csv = review_dir / f"extraidos_motor_fase7a_pass1_v2_block_{_bn:02d}_resolved_manifest.csv"
        _b_has_vca = False
        if _b_csv.is_file():
            with _b_csv.open(encoding="utf-8-sig", newline="") as _f:
                for _r in csv.DictReader(_f):
                    if _t(_r.get("categoria_pos_auditoria")).upper() == "VERDE_COM_ALERTA":
                        _b_has_vca = True
                        break
        _tag = f"PASS1_V2_BLOCO_{_bn:02d}_RECONCILIADO"
        if _b_has_vca:
            add_pass1_resolved_b11_union(_b_csv, _prio, _tag)
        else:
            add_pass1_resolved(_b_csv, _prio, _tag)
    # 7B.24: B24 — mesma lógica auto-detect plain/union.
    _b24_csv = review_dir / "extraidos_motor_fase7a_pass1_v2_block_24_resolved_manifest.csv"
    _b24_has_vca = False
    if _b24_csv.is_file():
        with _b24_csv.open(encoding="utf-8-sig", newline="") as _f:
            for _r in csv.DictReader(_f):
                if _t(_r.get("categoria_pos_auditoria")).upper() == "VERDE_COM_ALERTA":
                    _b24_has_vca = True
                    break
    if _b24_has_vca:
        add_pass1_resolved_b11_union(_b24_csv, PRIO_PASS1_B24, "PASS1_V2_BLOCO_24_RECONCILIADO")
    else:
        add_pass1_resolved(_b24_csv, PRIO_PASS1_B24, "PASS1_V2_BLOCO_24_RECONCILIADO")
    # 7B.23: B23 — mesma lógica auto-detect plain/union.
    _b23_csv = review_dir / "extraidos_motor_fase7a_pass1_v2_block_23_resolved_manifest.csv"
    _b23_has_vca = False
    if _b23_csv.is_file():
        with _b23_csv.open(encoding="utf-8-sig", newline="") as _f:
            for _r in csv.DictReader(_f):
                if _t(_r.get("categoria_pos_auditoria")).upper() == "VERDE_COM_ALERTA":
                    _b23_has_vca = True
                    break
    if _b23_has_vca:
        add_pass1_resolved_b11_union(_b23_csv, PRIO_PASS1_B23, "PASS1_V2_BLOCO_23_RECONCILIADO")
    else:
        add_pass1_resolved(_b23_csv, PRIO_PASS1_B23, "PASS1_V2_BLOCO_23_RECONCILIADO")
    # 7B.22: B22 — mesma lógica auto-detect plain/union.
    _b22_csv = review_dir / "extraidos_motor_fase7a_pass1_v2_block_22_resolved_manifest.csv"
    _b22_has_vca = False
    if _b22_csv.is_file():
        with _b22_csv.open(encoding="utf-8-sig", newline="") as _f:
            for _r in csv.DictReader(_f):
                if _t(_r.get("categoria_pos_auditoria")).upper() == "VERDE_COM_ALERTA":
                    _b22_has_vca = True
                    break
    if _b22_has_vca:
        add_pass1_resolved_b11_union(_b22_csv, PRIO_PASS1_B22, "PASS1_V2_BLOCO_22_RECONCILIADO")
    else:
        add_pass1_resolved(_b22_csv, PRIO_PASS1_B22, "PASS1_V2_BLOCO_22_RECONCILIADO")
    # PROMOCAO MANUAL HUMANA — pack revisao_manual_amarelos_b14_b20_aprovados.csv
    # Le SHAs aprovados manualmente (FALSO_AMARELO_PROVAVEL + AMARELO_COM_ALERTA revisado)
    # e injecta no master com tag PROMOCAO_MANUAL_REVISADA_CURSOR. Prio mais baixo que B21,
    # garante que o SHA entra mesmo se historicamente estava como AMARELO no resolved.
    _human_csv = review_dir / "revisao_manual_amarelos_b14_b20_aprovados.csv"
    if _human_csv.is_file():
        with _human_csv.open(encoding="utf-8-sig", newline="") as _f:
            for _r in csv.DictReader(_f):
                _sh = _t(_r.get("sha256_arquivo")).lower()
                if not _sh:
                    continue
                _row = {
                    "arquivo_rel": _t(_r.get("arquivo_rel")).replace("/", "\\"),
                    "sha256_arquivo": _sh,
                    "melhor_status": "VERDE_SEGURO",
                    "fonte_ultimo_processamento": "",
                    "output_tag": "promocao_manual_revisada_cursor_b14_b20",
                }
                winners[_sh] = best_manifest_row(
                    winners.get(_sh),
                    PRIO_HUMAN_PROMO_AMARELOS,
                    "PROMOCAO_MANUAL_REVISADA_CURSOR",
                    _row,
                )
    # 7B.21: B21 — mesma lógica auto-detect plain/union.
    _b21_csv = review_dir / "extraidos_motor_fase7a_pass1_v2_block_21_resolved_manifest.csv"
    _b21_has_vca = False
    if _b21_csv.is_file():
        with _b21_csv.open(encoding="utf-8-sig", newline="") as _f:
            for _r in csv.DictReader(_f):
                if _t(_r.get("categoria_pos_auditoria")).upper() == "VERDE_COM_ALERTA":
                    _b21_has_vca = True
                    break
    if _b21_has_vca:
        add_pass1_resolved_b11_union(_b21_csv, PRIO_PASS1_B21, "PASS1_V2_BLOCO_21_RECONCILIADO")
    else:
        add_pass1_resolved(_b21_csv, PRIO_PASS1_B21, "PASS1_V2_BLOCO_21_RECONCILIADO")
    # 7B.20: B20 — mesma lógica auto-detect plain/union.
    _b20_csv = review_dir / "extraidos_motor_fase7a_pass1_v2_block_20_resolved_manifest.csv"
    _b20_has_vca = False
    if _b20_csv.is_file():
        with _b20_csv.open(encoding="utf-8-sig", newline="") as _f:
            for _r in csv.DictReader(_f):
                if _t(_r.get("categoria_pos_auditoria")).upper() == "VERDE_COM_ALERTA":
                    _b20_has_vca = True
                    break
    if _b20_has_vca:
        add_pass1_resolved_b11_union(_b20_csv, PRIO_PASS1_B20, "PASS1_V2_BLOCO_20_RECONCILIADO")
    else:
        add_pass1_resolved(_b20_csv, PRIO_PASS1_B20, "PASS1_V2_BLOCO_20_RECONCILIADO")
    # 7B.19: B19 — mesma lógica auto-detect plain/union.
    _b19_csv = review_dir / "extraidos_motor_fase7a_pass1_v2_block_19_resolved_manifest.csv"
    _b19_has_vca = False
    if _b19_csv.is_file():
        with _b19_csv.open(encoding="utf-8-sig", newline="") as _f:
            for _r in csv.DictReader(_f):
                if _t(_r.get("categoria_pos_auditoria")).upper() == "VERDE_COM_ALERTA":
                    _b19_has_vca = True
                    break
    if _b19_has_vca:
        add_pass1_resolved_b11_union(_b19_csv, PRIO_PASS1_B19, "PASS1_V2_BLOCO_19_RECONCILIADO")
    else:
        add_pass1_resolved(_b19_csv, PRIO_PASS1_B19, "PASS1_V2_BLOCO_19_RECONCILIADO")
    # 7B.18: B18 — mesma lógica auto-detect plain/union.
    _b18_csv = review_dir / "extraidos_motor_fase7a_pass1_v2_block_18_resolved_manifest.csv"
    _b18_has_vca = False
    if _b18_csv.is_file():
        with _b18_csv.open(encoding="utf-8-sig", newline="") as _f:
            for _r in csv.DictReader(_f):
                if _t(_r.get("categoria_pos_auditoria")).upper() == "VERDE_COM_ALERTA":
                    _b18_has_vca = True
                    break
    if _b18_has_vca:
        add_pass1_resolved_b11_union(_b18_csv, PRIO_PASS1_B18, "PASS1_V2_BLOCO_18_RECONCILIADO")
    else:
        add_pass1_resolved(_b18_csv, PRIO_PASS1_B18, "PASS1_V2_BLOCO_18_RECONCILIADO")
    # 7B.17: B17 — mesma lógica auto-detect plain/union.
    _b17_csv = review_dir / "extraidos_motor_fase7a_pass1_v2_block_17_resolved_manifest.csv"
    _b17_has_vca = False
    if _b17_csv.is_file():
        with _b17_csv.open(encoding="utf-8-sig", newline="") as _f:
            for _r in csv.DictReader(_f):
                if _t(_r.get("categoria_pos_auditoria")).upper() == "VERDE_COM_ALERTA":
                    _b17_has_vca = True
                    break
    if _b17_has_vca:
        add_pass1_resolved_b11_union(_b17_csv, PRIO_PASS1_B17, "PASS1_V2_BLOCO_17_RECONCILIADO")
    else:
        add_pass1_resolved(_b17_csv, PRIO_PASS1_B17, "PASS1_V2_BLOCO_17_RECONCILIADO")
    # 7B.16: B16 — mesma lógica auto-detect plain/union.
    _b16_csv = review_dir / "extraidos_motor_fase7a_pass1_v2_block_16_resolved_manifest.csv"
    _b16_has_vca = False
    if _b16_csv.is_file():
        with _b16_csv.open(encoding="utf-8-sig", newline="") as _f:
            for _r in csv.DictReader(_f):
                if _t(_r.get("categoria_pos_auditoria")).upper() == "VERDE_COM_ALERTA":
                    _b16_has_vca = True
                    break
    if _b16_has_vca:
        add_pass1_resolved_b11_union(_b16_csv, PRIO_PASS1_B16, "PASS1_V2_BLOCO_16_RECONCILIADO")
    else:
        add_pass1_resolved(_b16_csv, PRIO_PASS1_B16, "PASS1_V2_BLOCO_16_RECONCILIADO")
    # 7B.15: B15 — mesma lógica auto-detect plain/union do B14.
    _b15_csv = review_dir / "extraidos_motor_fase7a_pass1_v2_block_15_resolved_manifest.csv"
    _b15_has_vca = False
    if _b15_csv.is_file():
        with _b15_csv.open(encoding="utf-8-sig", newline="") as _f:
            for _r in csv.DictReader(_f):
                if _t(_r.get("categoria_pos_auditoria")).upper() == "VERDE_COM_ALERTA":
                    _b15_has_vca = True
                    break
    if _b15_has_vca:
        add_pass1_resolved_b11_union(_b15_csv, PRIO_PASS1_B15, "PASS1_V2_BLOCO_15_RECONCILIADO")
    else:
        add_pass1_resolved(_b15_csv, PRIO_PASS1_B15, "PASS1_V2_BLOCO_15_RECONCILIADO")
    # 7B.14: B14 — selecciona automaticamente plain vs union conforme presença de V_C_A.
    # Plain filtra apenas VERDE_SEGURO; union (b11_union) aceita também VERDE_COM_ALERTA.
    # Como o resolved_manifest dos blocos pode evoluir, fazemos um peek leve ao CSV
    # uma única vez e escolhemos a função adequada — sem alterar a lógica de conflitos.
    _b14_csv = review_dir / "extraidos_motor_fase7a_pass1_v2_block_14_resolved_manifest.csv"
    _b14_has_vca = False
    if _b14_csv.is_file():
        with _b14_csv.open(encoding="utf-8-sig", newline="") as _f:
            for _r in csv.DictReader(_f):
                if _t(_r.get("categoria_pos_auditoria")).upper() == "VERDE_COM_ALERTA":
                    _b14_has_vca = True
                    break
    if _b14_has_vca:
        add_pass1_resolved_b11_union(_b14_csv, PRIO_PASS1_B14, "PASS1_V2_BLOCO_14_RECONCILIADO")
    else:
        add_pass1_resolved(_b14_csv, PRIO_PASS1_B14, "PASS1_V2_BLOCO_14_RECONCILIADO")
    # 7B.13: B13 reconciliation.json reportou 13 VERDE_SEGURO + 0 VERDE_COM_ALERTA;
    # plain function suficiente (mesma justificativa do B12).
    add_pass1_resolved(
        review_dir / "extraidos_motor_fase7a_pass1_v2_block_13_resolved_manifest.csv",
        PRIO_PASS1_B13,
        "PASS1_V2_BLOCO_13_RECONCILIADO",
    )
    # 7B.12: B12 reconciliation.json reportou 13 VERDE_SEGURO + 0 VERDE_COM_ALERTA;
    # função plain (filtra só VERDE_SEGURO) é suficiente. Se um futuro bloco tiver V_C_A,
    # promover para add_pass1_resolved_b11_union (que aceita ambos).
    add_pass1_resolved(
        review_dir / "extraidos_motor_fase7a_pass1_v2_block_12_resolved_manifest.csv",
        PRIO_PASS1_B12,
        "PASS1_V2_BLOCO_12_RECONCILIADO",
    )
    add_pass1_resolved_b11_union(
        review_dir / "extraidos_motor_fase7a_pass1_v2_block_11_resolved_manifest.csv",
        PRIO_PASS1_B11,
        "PASS1_V2_BLOCO_11_RECONCILIADO",
    )
    add_pass1_resolved(review_dir / "extraidos_motor_fase7a_pass1_v2_block_10_resolved_manifest.csv", PRIO_PASS1_B10, "PASS1_V2_BLOCO_10_RECONCILIADO")
    add_pass1_resolved(review_dir / "extraidos_motor_fase7a_pass1_v2_block_09_resolved_manifest.csv", PRIO_PASS1_B09, "PASS1_V2_BLOCO_09_RECONCILIADO")
    add_pass1_resolved(review_dir / "extraidos_motor_fase7a_pass1_v2_block_08_resolved_manifest.csv", PRIO_PASS1_B08, "PASS1_V2_BLOCO_08_RECONCILIADO")
    add_pass1_resolved(review_dir / "extraidos_motor_fase7a_pass1_v2_block_07_resolved_manifest.csv", PRIO_PASS1_B07, "PASS1_V2_BLOCO_07_RECONCILIADO")
    add_pass1_resolved(review_dir / "extraidos_motor_fase7a_pass1_v2_block_06_resolved_manifest.csv", PRIO_PASS1_B06, "PASS1_V2_BLOCO_06_RECONCILIADO")
    add_pass1_resolved(review_dir / "extraidos_motor_fase7a_pass1_v2_block_05_resolved_manifest.csv", PRIO_PASS1_B05, "PASS1_V2_BLOCO_05_RECONCILIADO")

    # PASS1 B04 (após top PASS1 incremental)
    pb4 = review_dir / "extraidos_motor_fase7a_pass1_v2_block_04_resolved_manifest.csv"
    if pb4.is_file():
        with pb4.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                if _t(row.get("categoria_pos_auditoria")).upper() != "VERDE_SEGURO":
                    continue
                sh = _t(row.get("sha256_arquivo")).lower()
                if not sh:
                    continue
                r = {
                    "arquivo_rel": _t(row.get("arquivo_rel")).replace("/", "\\"),
                    "sha256_arquivo": sh,
                    "melhor_status": "VERDE_SEGURO",
                    "fonte_ultimo_processamento": "",
                    "output_tag": _t(row.get("output_tag") or ""),
                }
                winners[sh] = best_manifest_row(winners.get(sh), PRIO_PASS1_B04, "PASS1_V2_BLOCO_04_RECONCILIADO", r)

    # PASS1 B03
    pb3 = review_dir / "extraidos_motor_fase7a_pass1_v2_block_03_resolved_manifest.csv"
    if pb3.is_file():
        with pb3.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                if _t(row.get("categoria_pos_auditoria")).upper() != "VERDE_SEGURO":
                    continue
                sh = _t(row.get("sha256_arquivo")).lower()
                if not sh:
                    continue
                r = {
                    "arquivo_rel": _t(row.get("arquivo_rel")).replace("/", "\\"),
                    "sha256_arquivo": sh,
                    "melhor_status": "VERDE_SEGURO",
                    "fonte_ultimo_processamento": "",
                    "output_tag": _t(row.get("output_tag") or ""),
                }
                winners[sh] = best_manifest_row(winners.get(sh), PRIO_PASS1_B03, "PASS1_V2_BLOCO_03_RECONCILIADO", r)

    # PASS1 B02
    pb2 = review_dir / "extraidos_motor_fase7a_pass1_v2_block_02_resolved_manifest.csv"
    if pb2.is_file():
        with pb2.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                if _t(row.get("categoria_pos_auditoria")).upper() != "VERDE_SEGURO":
                    continue
                sh = _t(row.get("sha256_arquivo")).lower()
                if not sh:
                    continue
                r = {
                    "arquivo_rel": _t(row.get("arquivo_rel")).replace("/", "\\"),
                    "sha256_arquivo": sh,
                    "melhor_status": "VERDE_SEGURO",
                    "fonte_ultimo_processamento": "",
                    "output_tag": _t(row.get("output_tag") or ""),
                }
                winners[sh] = best_manifest_row(winners.get(sh), PRIO_PASS1_B02, "PASS1_V2_BLOCO_02_RECONCILIADO", r)

    # PASS1 B01
    pb1 = review_dir / "extraidos_motor_fase7a_pass1_v2_block_01_resolved_manifest.csv"
    if pb1.is_file():
        with pb1.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                if _t(row.get("categoria_pos_auditoria")).upper() != "VERDE_SEGURO":
                    continue
                sh = _t(row.get("sha256_arquivo")).lower()
                if not sh:
                    continue
                r = {
                    "arquivo_rel": _t(row.get("arquivo_rel")).replace("/", "\\"),
                    "sha256_arquivo": sh,
                    "melhor_status": "VERDE_SEGURO",
                    "fonte_ultimo_processamento": "",
                    "output_tag": _t(row.get("output_tag") or ""),
                }
                winners[sh] = best_manifest_row(winners.get(sh), PRIO_PASS1_B01, "PASS1_V2_BLOCO_01_RECONCILIADO", r)

    # RELEASE V1 consolidated
    rv1 = review_dir / "release_retry_flash_fase6_v1_manifest_consolidado.csv"
    if rv1.is_file():
        with rv1.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                if _t(row.get("categoria_pos_auditoria")).upper() not in ("", "VERDE_SEGURO"):
                    if row.get("categoria_pos_auditoria") and _t(row.get("categoria_pos_auditoria")).upper() != "VERDE_SEGURO":
                        continue
                sh = _t(row.get("sha256_arquivo")).lower()
                if not sh:
                    continue
                r = {
                    "arquivo_rel": _t(row.get("arquivo_rel")).replace("/", "\\"),
                    "sha256_arquivo": sh,
                    "melhor_status": "VERDE_SEGURO",
                    "fonte_ultimo_processamento": _t(row.get("fonte") or ""),
                    "output_tag": _t(row.get("output_tag_origem") or ""),
                }
                winners[sh] = best_manifest_row(winners.get(sh), PRIO_RELEASE_V1, "RELEASE_V1_RETRY", r)

    # Retry blocos 01..10 resolved
    for pth in sorted(review_dir.glob("extraidos_motor_fase*_retry_block_*_resolved_manifest.csv")):
        m = RE_BLOCK.search(pth.name)
        if not m:
            continue
        blk = int(m.group(1))
        tag = f"MANIFEST_RETRY_BLOCO_{blk:02d}"
        prio = PRIO_MANIFEST_RETRY_BASE + blk
        with pth.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                if _t(row.get("categoria_pos_auditoria")).upper() != "VERDE_SEGURO":
                    continue
                sh = _t(row.get("sha256_arquivo")).lower()
                if not sh:
                    continue
                r = {
                    "arquivo_rel": _t(row.get("arquivo_rel")).replace("/", "\\"),
                    "sha256_arquivo": sh,
                    "melhor_status": "VERDE_SEGURO",
                    "fonte_ultimo_processamento": "",
                    "output_tag": _t(row.get("output_tag") or ""),
                }
                winners[sh] = best_manifest_row(winners.get(sh), prio, tag, r)

    # Legacy backlog resolved
    leg = review_dir / "extraidos_motor_retry_backlog_resolved_manifest.csv"
    if leg.is_file():
        with leg.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                if _t(row.get("resultado_final")).upper() != "VERDE_SEGURO":
                    continue
                sh = _t(row.get("sha256_arquivo")).lower()
                if not sh:
                    continue
                r = {
                    "arquivo_rel": _t(row.get("arquivo_rel") or row.get("arquivo") or "").replace("/", "\\"),
                    "sha256_arquivo": sh,
                    "melhor_status": "VERDE_SEGURO",
                    "fonte_ultimo_processamento": _t(row.get("fonte") or ""),
                    "output_tag": _t(row.get("output_tag") or row.get("ultimo_output_tag") or ""),
                }
                winners[sh] = best_manifest_row(winners.get(sh), PRIO_LEGACY, "MANIFEST_LEGACY_RETRY_BACKLOG", r)

    return winners, set(winners.keys())


def _read_resolved_verde_shas(path: Path) -> set[str]:
    """SHAs no resolved PASS1-v2: VERDE_SEGURO e VERDE_COM_ALERTA (ex.: bloco 11)."""
    s: set[str] = set()
    if not path.is_file():
        return s
    with path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            cat = _t(row.get("categoria_pos_auditoria")).upper()
            if cat not in ("VERDE_SEGURO", "VERDE_COM_ALERTA"):
                continue
            sh = _t(row.get("sha256_arquivo")).lower()
            if sh:
                s.add(sh)
    return s


_RESCUE_BLOCK_RE = re.compile(r"pass1_v2_block_(\d+)_rescue_emit\.json$", re.I)
_RESCUE_QUEUE_RE = re.compile(r"pass1_v2_block_(\d+)\.csv$", re.I)


def discover_rescue_block_nums(review_dir: Path) -> set[int]:
    """Blocos emitidos pela operacao resgate (JSON emit ou fila com reason operacao_rescue)."""
    nums: set[int] = set()
    for p in review_dir.glob("pass1_v2_block_*_rescue_emit.json"):
        m = _RESCUE_BLOCK_RE.match(p.name)
        if m:
            nums.add(int(m.group(1)))
    for p in review_dir.glob("pass1_v2_block_*.csv"):
        m = _RESCUE_QUEUE_RE.match(p.name)
        if not m:
            continue
        bn = int(m.group(1))
        with p.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                reason = _t(row.get("reason", "")).lower()
                motivo = _t(row.get("motivo_interno", "")).lower()
                if "operacao_rescue" in reason or "operacao_rescue" in motivo:
                    nums.add(bn)
                break
    return nums


def _resolved_row_is_rescue(row: dict) -> bool:
    """Flag no resolved manifest / reconcile outcome indicando bloco de resgate."""
    blob = "|".join(
        _t(row.get(k, "")).lower()
        for k in (
            "motivo_interno",
            "reconcile_outcome",
            "extract_status",
            "reason",
        )
    )
    return "operacao_rescue" in blob or "rescue" in blob and "pass1" in blob


def load_rescue_amnesty_shas(
    review_dir: Path,
    manifest_winners: dict[str, tuple[int, str, dict]],
) -> tuple[set[str], set[str]]:
    """
    Operacao resgate (B36, B37, …): SHAs VERDE reconciliados em blocos de resgate
    cuja fonte vencedora na uniao e PASS1_V2_BLOCO_NN_RECONCILIADO (indulto regras b/c).
    Retorna (shas, fonte_release_tags).
    """
    shas: set[str] = set()
    tags: set[str] = set()
    rescue_bns = discover_rescue_block_nums(review_dir)
    for p in sorted(review_dir.glob("extraidos_motor_fase7a_pass1_v2_block_*_resolved_manifest.csv")):
        m = re.search(r"block_(\d+)_resolved_manifest\.csv$", p.name, re.I)
        if not m:
            continue
        bn = int(m.group(1))
        if bn not in rescue_bns:
            with p.open(encoding="utf-8-sig", newline="") as f:
                has_rescue_flag = any(_resolved_row_is_rescue(r) for r in csv.DictReader(f))
            if not has_rescue_flag:
                continue
            rescue_bns.add(bn)
        tag = _pass1_tag(bn)
        if not p.is_file():
            continue
        with p.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                cat = _t(row.get("categoria_pos_auditoria")).upper()
                if cat not in ("VERDE_SEGURO", "VERDE_COM_ALERTA"):
                    continue
                sh = _t(row.get("sha256_arquivo")).lower()
                if not sh:
                    continue
                winner = manifest_winners.get(sh)
                if winner and winner[1] == tag:
                    shas.add(sh)
                    tags.add(tag)
    return shas, tags


def _pass1_tag(bn: int) -> str:
    return f"PASS1_V2_BLOCO_{bn:02d}_RECONCILIADO"


def main() -> int:
    ap = argparse.ArgumentParser(description="Rebuild master_release_v2 offline (FASE 7B.x).")
    ap.add_argument(
        "--phase",
        choices=("7b4", "7b5", "7b6", "7b7", "7b8", "7b9", "7b10", "7b11", "7b12", "7b13", "7b14", "7b15", "7b16", PHASE_7B17, PHASE_7B18, PHASE_7B19, PHASE_7B20, PHASE_7B21, PHASE_7B22, PHASE_7B23, PHASE_7B24, PHASE_7B25, PHASE_7B26, PHASE_7B27, PHASE_7B28, PHASE_7B29, PHASE_7B30, PHASE_7B31, PHASE_7B32, PHASE_7B33, PHASE_7B34, PHASE_7B35, PHASE_7B36, PHASE_7B37, PHASE_7B38, PHASE_7B39, PHASE_7B40, PHASE_7B41, PHASE_7B42, PHASE_7B43, PHASE_7B44, PHASE_7B45, PHASE_7B46),
        default="7b4",
        help="Fase de promoção incremental.",
    )
    args = ap.parse_args()

    phase_slug = args.phase
    phase_tag = {
        "7b4": "fase7b4",
        "7b5": "fase7b5",
        "7b6": "fase7b6",
        "7b7": "fase7b7",
        "7b8": "fase7b8",
        "7b9": "fase7b9",
        "7b10": "fase7b10",
        "7b11": "fase7b11",
        "7b12": "fase7b12",
        "7b13": "fase7b13",
        "7b14": "fase7b14",
        "7b15": "fase7b15",
        "7b16": "fase7b16",
        PHASE_7B17: "fase7b17",
        PHASE_7B18: "fase7b18",
        PHASE_7B19: "fase7b19",
        PHASE_7B20: "fase7b20",
        PHASE_7B21: "fase7b21",
        PHASE_7B22: "fase7b22",
        PHASE_7B23: "fase7b23",
        PHASE_7B24: "fase7b24",
        PHASE_7B25: "fase7b25",
        PHASE_7B26: "fase7b26",
        PHASE_7B27: "fase7b27",
        PHASE_7B28: "fase7b28",
        PHASE_7B29: "fase7b29",
        PHASE_7B30: "fase7b30",
        PHASE_7B31: "fase7b31",
        PHASE_7B32: "fase7b32",
        PHASE_7B33: "fase7b33",
        PHASE_7B34: "fase7b34",
        PHASE_7B35: "fase7b35",
        PHASE_7B36: "fase7b36",
        PHASE_7B37: "fase7b37",
        PHASE_7B38: "fase7b38",
        PHASE_7B39: "fase7b39",
        PHASE_7B40: "fase7b40",
        PHASE_7B41: "fase7b41",
        PHASE_7B42: "fase7b42",
        PHASE_7B43: "fase7b43",
        PHASE_7B44: "fase7b44",
        PHASE_7B45: "fase7b45",
        PHASE_7B46: "fase7b46",
    }[phase_slug]
    promoted_bn = {"7b4": 4, "7b5": 5, "7b6": 6, "7b7": 7, "7b8": 8, "7b9": 9, "7b10": 10, "7b11": 11, "7b12": 12, "7b13": 13, "7b14": 14, "7b15": 15, "7b16": 16, PHASE_7B17: 17, PHASE_7B18: 18, PHASE_7B19: 19, PHASE_7B20: 20, PHASE_7B21: 21, PHASE_7B22: 22, PHASE_7B23: 23, PHASE_7B24: 24, PHASE_7B25: 25, PHASE_7B26: 26, PHASE_7B27: 27, PHASE_7B28: 28, PHASE_7B29: 29, PHASE_7B30: 30, PHASE_7B31: 31, PHASE_7B32: 32, PHASE_7B33: 33, PHASE_7B34: 34, PHASE_7B35: 35, PHASE_7B36: 36, PHASE_7B37: 37, PHASE_7B38: 38, PHASE_7B39: 39, PHASE_7B40: 40, PHASE_7B41: 41, PHASE_7B42: 42, PHASE_7B43: 43, PHASE_7B44: 44, PHASE_7B45: 45, PHASE_7B46: 46}[phase_slug]
    diff_name = f"master_release_v2_diff_{phase_tag}.md"

    utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ts_safe = utc.replace(":", "").replace("-", "")

    forbidden_bn_all = forbidden_basenames_all(REVIEW_DIR)
    rv1_path = REVIEW_DIR / "release_retry_flash_fase6_v1_manifest_consolidado.csv"
    pb1_path = REVIEW_DIR / "extraidos_motor_fase7a_pass1_v2_block_01_resolved_manifest.csv"
    pb2_path = REVIEW_DIR / "extraidos_motor_fase7a_pass1_v2_block_02_resolved_manifest.csv"
    pb3_path = REVIEW_DIR / "extraidos_motor_fase7a_pass1_v2_block_03_resolved_manifest.csv"
    pb4_path = REVIEW_DIR / "extraidos_motor_fase7a_pass1_v2_block_04_resolved_manifest.csv"
    pb5_path = REVIEW_DIR / "extraidos_motor_fase7a_pass1_v2_block_05_resolved_manifest.csv"
    pb6_path = REVIEW_DIR / "extraidos_motor_fase7a_pass1_v2_block_06_resolved_manifest.csv"
    pb7_path = REVIEW_DIR / "extraidos_motor_fase7a_pass1_v2_block_07_resolved_manifest.csv"
    pb8_path = REVIEW_DIR / "extraidos_motor_fase7a_pass1_v2_block_08_resolved_manifest.csv"
    pb9_path = REVIEW_DIR / "extraidos_motor_fase7a_pass1_v2_block_09_resolved_manifest.csv"
    pb10_path = REVIEW_DIR / "extraidos_motor_fase7a_pass1_v2_block_10_resolved_manifest.csv"
    pb11_path = REVIEW_DIR / "extraidos_motor_fase7a_pass1_v2_block_11_resolved_manifest.csv"
    pb12_path = REVIEW_DIR / "extraidos_motor_fase7a_pass1_v2_block_12_resolved_manifest.csv"
    pb13_path = REVIEW_DIR / "extraidos_motor_fase7a_pass1_v2_block_13_resolved_manifest.csv"
    pb14_path = REVIEW_DIR / "extraidos_motor_fase7a_pass1_v2_block_14_resolved_manifest.csv"
    pb15_path = REVIEW_DIR / "extraidos_motor_fase7a_pass1_v2_block_15_resolved_manifest.csv"
    pb16_path = REVIEW_DIR / "extraidos_motor_fase7a_pass1_v2_block_16_resolved_manifest.csv"
    pb17_path = REVIEW_DIR / "extraidos_motor_fase7a_pass1_v2_block_17_resolved_manifest.csv"
    pb18_path = REVIEW_DIR / "extraidos_motor_fase7a_pass1_v2_block_18_resolved_manifest.csv"
    pb19_path = REVIEW_DIR / "extraidos_motor_fase7a_pass1_v2_block_19_resolved_manifest.csv"
    pb20_path = REVIEW_DIR / "extraidos_motor_fase7a_pass1_v2_block_20_resolved_manifest.csv"
    pb21_path = REVIEW_DIR / "extraidos_motor_fase7a_pass1_v2_block_21_resolved_manifest.csv"
    pb22_path = REVIEW_DIR / "extraidos_motor_fase7a_pass1_v2_block_22_resolved_manifest.csv"
    pb23_path = REVIEW_DIR / "extraidos_motor_fase7a_pass1_v2_block_23_resolved_manifest.csv"
    pb24_path = REVIEW_DIR / "extraidos_motor_fase7a_pass1_v2_block_24_resolved_manifest.csv"
    pb25_path = REVIEW_DIR / "extraidos_motor_fase7a_pass1_v2_block_25_resolved_manifest.csv"
    human_promo_path = REVIEW_DIR / "revisao_manual_amarelos_b14_b20_aprovados.csv"
    safe_b2 = REVIEW_DIR / "extraidos_motor_fase7a_pass1_v2_block_02_flash_categorized_safe_green_candidates.csv"
    qb2 = REVIEW_DIR / "pass1_v2_block_02.csv"
    ix_path = REVIEW_DIR / "processed_image_index.csv"

    chk: list[tuple[Path, str]] = [
        (rv1_path, "release_retry_flash_fase6_v1_manifest_consolidado.csv"),
        (pb1_path, "pass1 b01 resolved"),
        (pb2_path, "pass1 b02 resolved"),
        (pb3_path, "pass1 b03 resolved"),
        (pb4_path, "pass1 b04 resolved"),
        (ix_path, "processed_image_index"),
    ]
    if phase_slug in ("7b5", "7b6", "7b7", "7b8", "7b9", "7b10", "7b11"):
        chk.append((pb5_path, "pass1 b05 resolved"))
    if phase_slug in ("7b6", "7b7", "7b8", "7b9", "7b10", "7b11"):
        chk.append((pb6_path, "pass1 b06 resolved"))
    if phase_slug in ("7b7", "7b8", "7b9", "7b10", "7b11"):
        chk.append((pb7_path, "pass1 b07 resolved"))
    if phase_slug in ("7b8", "7b9", "7b10", "7b11"):
        chk.append((pb8_path, "pass1 b08 resolved"))
    if phase_slug in ("7b9", "7b10", "7b11"):
        chk.append((pb9_path, "pass1 b09 resolved"))
    if phase_slug in ("7b10", "7b11"):
        chk.append((pb10_path, "pass1 b10 resolved"))
    if phase_slug == "7b11":
        chk.append((pb11_path, "pass1 b11 resolved"))

    for pth, label in chk:
        if not pth.is_file():
            print(f"ERRO falta obrigatório {label}: {pth}", file=sys.stderr)
            return 2

    promo_path = REVIEW_DIR / f"extraidos_motor_fase7a_pass1_v2_block_{promoted_bn:02d}_resolved_manifest.csv"
    promoted_resolved_shas = _read_resolved_verde_shas(promo_path)

    old_oficial_sha: set[str] = set()
    old_candidato_b02_sha: set[str] = set()
    old_manifest_fp = REVIEW_DIR / "master_release_v2_manifest.csv"
    if old_manifest_fp.is_file():
        with old_manifest_fp.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                sh = _t(row.get("sha256_arquivo")).lower()
                if not sh:
                    continue
                st = _t(row.get("status_release")).upper()
                fr = _t(row.get("fonte_release"))
                if st == "OFICIAL":
                    old_oficial_sha.add(sh)
                if st == "CANDIDATO_AGUARDA_RECONCILE_7A5" and fr == "PASS1_V2_BLOCO_02_CANDIDATO":
                    old_candidato_b02_sha.add(sh)

    backup_if_exists(
        REVIEW_DIR,
        [
            "master_release_v2_manifest.csv",
            "master_release_v2.json",
            "master_release_v2.md",
            "master_release_v2_excluidos.csv",
        ],
        ts_safe,
        phase_tag,
    )

    alert_shas = collect_alert_shas_extended(REVIEW_DIR)
    manual_csv_shas = collect_manual_shas_extended(REVIEW_DIR)
    manifest_winners, sha_manifest_oficial = load_official_manifest_union(REVIEW_DIR)
    rescue_amnesty_shas, rescue_amnesty_tags = load_rescue_amnesty_shas(REVIEW_DIR, manifest_winners)

    rv1_sha_set: set[str] = set()
    if rv1_path.is_file():
        with rv1_path.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                s = _t(row.get("sha256_arquivo")).lower()
                if s:
                    rv1_sha_set.add(s)

    index_by_sha_last: dict[str, dict[str, str]] = {}
    index_any_precisa_manual: defaultdict[str, list[bool]] = defaultdict(list)
    index_melhor_verde_seguro_sha: set[str] = set()
    with ix_path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            sh = _t(row.get("sha256_arquivo")).lower()
            if not sh:
                continue
            index_any_precisa_manual[sh].append(yn_true(row.get("precisa_revisao_manual") or ""))
            if _t(row.get("melhor_status")).upper() == "VERDE_SEGURO":
                index_melhor_verde_seguro_sha.add(sh)
            ts = _t(row.get("updated_at") or "")
            prev = index_by_sha_last.get(sh)
            if not prev or ts > _t(prev.get("updated_at") or ""):
                index_by_sha_last[sh] = {
                    **{k: _t(row.get(k) or "") for k in ["image_path", "melhor_status", "fonte_ultimo_processamento", "ultimo_output_tag", "updated_at"]},
                    "basename": basename_lower(row.get("image_path", "")),
                }

    conflict_manual_index: set[str] = {sh for sh, flags in index_any_precisa_manual.items() if any(flags)}

    verde_manual_linha_conflict: set[str] = set()
    with ix_path.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            sh = _t(row.get("sha256_arquivo")).lower()
            if not sh:
                continue
            if _t(row.get("melhor_status")).upper() == "VERDE_SEGURO" and _t(row.get("precisa_revisao_manual")) == "1":
                verde_manual_linha_conflict.add(sh)

    # Índice limpo (somente quando NÃO há manifest oficial — será filtrado depois na união manifest)
    rows_ix_limpo: dict[str, dict] = {}
    indice_limpo_input_sha: set[str] = set()
    with ix_path.open(encoding="utf-8-sig", newline="") as f:
        seen_sh: defaultdict[str, str] = defaultdict(str)
        for row in csv.DictReader(f):
            sh = _t(row.get("sha256_arquivo")).lower()
            if not sh:
                continue
            if _t(row.get("melhor_status")).upper() != "VERDE_SEGURO":
                continue
            if _t(row.get("ja_deu_verde_seguro")) != "1":
                continue
            if _t(row.get("precisa_revisao_manual")) != "0":
                continue
            fp = norm_rel(row.get("image_path", ""))
            if fp and (not seen_sh[sh] or fp < seen_sh[sh]):
                seen_sh[sh] = fp
            indice_limpo_input_sha.add(sh)
            rows_ix_limpo[sh] = {
                "arquivo_rel": _t(row.get("image_path")).replace("/", "\\"),
                "sha256_arquivo": sh,
                "melhor_status": _t(row.get("melhor_status")).upper() or "VERDE_SEGURO",
                "fonte_ultimo_processamento": _t(row.get("fonte_ultimo_processamento")),
                "output_tag": _t(row.get("ultimo_output_tag")),
                "updated_at_indice": _t(row.get("updated_at")),
            }

    qb2_rel_to_sha: dict[str, str] = {}
    if qb2.is_file():
        with qb2.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                rel = norm_rel(row.get("arquivo_rel"))
                sh = _t(row.get("sha256_arquivo")).lower()
                if rel and sh:
                    qb2_rel_to_sha[rel] = sh

    rows_cb2: list[dict] = []
    if safe_b2.is_file():
        with safe_b2.open(encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                ar_raw = _t(row.get("arquivo")).replace("/", "\\")
                nk = norm_rel(ar_raw)
                sh = qb2_rel_to_sha.get(nk, "")
                rows_cb2.append(
                    {
                        "arquivo_rel": ar_raw,
                        "sha256_arquivo": sh,
                        "melhor_status": "VERDE_SEGURO",
                        "fonte_ultimo_processamento": "",
                        "output_tag": "extraidos_motor_fase7a_pass1_v2_block_02_flash_categorized_safe_green",
                    }
                )

    excluded: list[dict] = []

    def push_ex(ar: str, sh: str, motivos: list[str]):
        excluded.append({"arquivo_rel": ar, "sha256_arquivo": sh, "motivos": "|".join(sorted(set(motivos)))})

    def apply_abc(ar: str, sh: str, ftag: str = "") -> list[str]:
        # PROMOCAO_MANUAL_REVISADA_CURSOR e' aprovacao humana explicita: ignora a/b/c.
        if ftag == "PROMOCAO_MANUAL_REVISADA_CURSOR":
            return []
        # Resgate PASS1 (B36+): indulto historico NO_AUTO (c) e manual_review (b); regra (a) mantida.
        rescue_bypass_bc = ftag in rescue_amnesty_tags or sh in rescue_amnesty_shas
        bm = basename_lower(ar)
        ms: list[str] = []
        if sh in alert_shas:
            ms.append("IN_ALERT_MANIFEST_a")
        if not rescue_bypass_bc:
            if sh in manual_csv_shas:
                ms.append("IN_MANUAL_REVIEW_b")
            if bm in forbidden_bn_all:
                ms.append("ISOLADO_OU_NO_AUTO_BASENAME_c")
        return ms

    oficial_sha_final: dict[str, dict] = {}

    # --- Caminho manifest oficial: abc apenas; não (d).
    for sh in sha_manifest_oficial:
        _prio, ftag, row_m = manifest_winners[sh]
        ar = row_m["arquivo_rel"]
        motivos = apply_abc(ar, sh, ftag)
        if motivos:
            push_ex(ar, sh, motivos)
            continue
        idx_last = index_by_sha_last.get(sh, {})
        if idx_last.get("fonte_ultimo_processamento") and not row_m.get("fonte_ultimo_processamento"):
            row_m["fonte_ultimo_processamento"] = idx_last["fonte_ultimo_processamento"]
        if idx_last.get("ultimo_output_tag") and not row_m.get("output_tag"):
            row_m["output_tag"] = idx_last["ultimo_output_tag"]
        if not row_m.get("arquivo_rel") and idx_last.get("image_path"):
            row_m["arquivo_rel"] = _t(idx_last.get("image_path")).replace("/", "\\")
        atualizado = rows_ix_limpo.get(sh, {}).get("updated_at_indice") or idx_last.get("updated_at", "")
        nota_idx = (
            "INDEX_FLAG_PRECISA_REVISAO_MANUAL_OBSOLETA_DETECTADA"
            if sh in conflict_manual_index
            else "INDEX_SEM_FLAG_MANUAL_OU_CONSISTENTE"
        )
        oficial_sha_final[sh] = {
            **row_m,
            "status_release": "OFICIAL",
            "fonte_release": ftag,
            "overlap_release_v1": str(sh in rv1_sha_set).lower(),
            "overlap_indice_verde": str(sh in index_melhor_verde_seguro_sha).lower(),
            "nota_indice": nota_idx,
            "updated_at_indice": atualizado,
        }

    # --- Índice limpo apenas para SHA fora da união oficial: abcd incluindo d.
    indice_kept_overlap_manifest = sha_manifest_oficial & indice_limpo_input_sha

    for sh, row_ix in rows_ix_limpo.items():
        if sh in sha_manifest_oficial:
            continue
        ar = row_ix["arquivo_rel"]
        motivos = apply_abc(ar, sh)
        if sh in conflict_manual_index:
            motivos.append("CONFLITO_INDICE_VERDE_MAS_FLAG_MANUAL_d_INDICE_SEM_MANIFEST_OFICIAL")
        if motivos:
            push_ex(ar, sh, motivos)
            continue
        idx_last = index_by_sha_last.get(sh, {})
        nota_idx = "INDICE_VERDE_LIMPO_CRITERIO_ORIGINAL"
        oficial_sha_final[sh] = {
            **row_ix,
            "status_release": "OFICIAL",
            "fonte_release": "INDICE_VERDE_LIMPO",
            "overlap_release_v1": str(sh in rv1_sha_set).lower(),
            "overlap_indice_verde": str(sh in index_melhor_verde_seguro_sha).lower(),
            "nota_indice": nota_idx,
            "updated_at_indice": row_ix.get("updated_at_indice", "") or idx_last.get("updated_at", ""),
        }

    candidatos_raw = [x for x in rows_cb2 if _t(x.get("sha256_arquivo"))]
    cand_keep: list[dict] = []
    for cw in candidatos_raw:
        sh = _t(cw["sha256_arquivo"]).lower()
        ar = cw["arquivo_rel"]
        if sh in oficial_sha_final:
            continue
        motivos = apply_abc(ar, sh)
        if motivos:
            push_ex(ar, sh, motivos)
            continue
        idx_inf = index_by_sha_last.get(sh, {})
        nota_idx = (
            "INDEX_FLAG_PRECISA_REVISAO_MANUAL_OBSOLETA_DETECTADA"
            if sh in conflict_manual_index
            else "INDEX_SEM_FLAG_MANUAL_OU_CONSISTENTE"
        )
        cand_keep.append(
            {
                **cw,
                "status_release": "CANDIDATO_AGUARDA_RECONCILE_7A5",
                "fonte_release": "PASS1_V2_BLOCO_02_CANDIDATO",
                "overlap_release_v1": str(sh in rv1_sha_set).lower(),
                "overlap_indice_verde": str(sh in index_melhor_verde_seguro_sha).lower(),
                "nota_indice": nota_idx,
                "updated_at_indice": rows_ix_limpo.get(sh, {}).get("updated_at_indice") or idx_inf.get("updated_at", ""),
            }
        )

    out_csv = REVIEW_DIR / "master_release_v2_manifest.csv"
    with out_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=MANIFEST_COLUMNS)
        w.writeheader()
        for sh in sorted(oficial_sha_final, key=lambda s: oficial_sha_final[s]["arquivo_rel"].lower()):
            r = oficial_sha_final[sh]
            w.writerow({k: r.get(k, "") for k in MANIFEST_COLUMNS})
        for r in sorted(cand_keep, key=lambda x: x["arquivo_rel"].lower()):
            w.writerow({k: r.get(k, "") for k in MANIFEST_COLUMNS})

    ex_csv = REVIEW_DIR / "master_release_v2_excluidos.csv"
    with ex_csv.open("w", encoding="utf-8-sig", newline="") as xf:
        wex = csv.DictWriter(xf, fieldnames=["sha256_arquivo", "arquivo_rel", "motivos"])
        wex.writeheader()
        for e in excluded:
            wex.writerow(e)

    motivo_tokens = defaultdict(int)
    for e in excluded:
        for mm in _t(e.get("motivos")).split("|"):
            if mm.strip():
                motivo_tokens[mm.strip()] += 1

    new_oficial_sha = set(oficial_sha_final.keys())
    reincorporados = sorted(new_oficial_sha - old_oficial_sha)
    desapareceram = sorted(old_oficial_sha - new_oficial_sha)
    delta = len(new_oficial_sha) - len(old_oficial_sha)

    oficiais = len(oficial_sha_final)
    cands = len(cand_keep)
    br_fonte_of = Counter(oficial_sha_final[s]["fonte_release"] for s in oficial_sha_final)

    apenas_indice_pk = sum(
        1
        for s, v in oficial_sha_final.items()
        if v["fonte_release"] == "INDICE_VERDE_LIMPO"
        and _t(v.get("overlap_release_v1")).lower() == "false"
    )
    overlap_ix_false_pk = sum(1 for s, v in oficial_sha_final.items() if _t(v.get("overlap_indice_verde")).lower() == "false")

    gap = META_DEPLOY_GAP - oficiais
    if oficiais >= 410:
        rec = "ENTREGAVEL_PARA_DEPLOY_PILOTO_AMPLIADO_v2"
    else:
        rec = "REPORTAR_SEM_DECISAO_DEPLOY_VERIFICAR_BASELINE_7B4"

    promo_tag_str = _pass1_tag(promoted_bn)

    pk_oficial_sha = {s for s, v in oficial_sha_final.items() if v.get("fonte_release") == promo_tag_str}
    sha_promo_ord = sorted(pk_oficial_sha, key=lambda s: oficial_sha_final[s]["arquivo_rel"].lower())
    novos_inesperado = sorted(set(reincorporados) - promoted_resolved_shas)

    primeira10_pk = [
        {"sha256_arquivo": sh, "arquivo_rel": oficial_sha_final[sh]["arquivo_rel"], "motivo": promo_tag_str}
        for sh in sha_promo_ord[:10]
    ]
    pk_primeira_linha = (
        f"{oficial_sha_final[sha_promo_ord[0]]['arquivo_rel']} | `{sha_promo_ord[0]}`" if sha_promo_ord else "(vazio)"
    )
    pk_ultima_linha = (
        f"{oficial_sha_final[sha_promo_ord[-1]]['arquivo_rel']} | `{sha_promo_ord[-1]}`" if sha_promo_ord else "(vazio)"
    )

    manifest_src = [
        "extraidos_motor_fase*_retry_block_*_resolved_manifest.csv",
        "extraidos_motor_retry_backlog_resolved_manifest.csv",
        "release_retry_flash_fase6_v1_manifest_consolidado.csv",
        "extraidos_motor_fase7a_pass1_v2_block_01_resolved_manifest.csv",
        "extraidos_motor_fase7a_pass1_v2_block_02_resolved_manifest.csv",
        "extraidos_motor_fase7a_pass1_v2_block_03_resolved_manifest.csv",
        "extraidos_motor_fase7a_pass1_v2_block_04_resolved_manifest.csv",
        "extraidos_motor_fase7a_pass1_v2_block_05_resolved_manifest.csv (opcional até 7B.5)",
        "extraidos_motor_fase7a_pass1_v2_block_06_resolved_manifest.csv (opcional até 7B.6)",
        "extraidos_motor_fase7a_pass1_v2_block_07_resolved_manifest.csv (opcional até 7B.7)",
        "extraidos_motor_fase7a_pass1_v2_block_08_resolved_manifest.csv (opcional até 7B.8)",
        "extraidos_motor_fase7a_pass1_v2_block_09_resolved_manifest.csv (opcional até 7B.9)",
        "extraidos_motor_fase7a_pass1_v2_block_10_resolved_manifest.csv (opcional até 7B.10)",
        "extraidos_motor_fase7a_pass1_v2_block_11_resolved_manifest.csv (opcional até 7B.11)",
        "extraidos_motor_fase7a_pass1_v2_block_12_resolved_manifest.csv (opcional até 7B.12)",
        "extraidos_motor_fase7a_pass1_v2_block_13_resolved_manifest.csv (opcional até 7B.13)",
        "extraidos_motor_fase7a_pass1_v2_block_14_resolved_manifest.csv (opcional até 7B.14)",
        "extraidos_motor_fase7a_pass1_v2_block_15_resolved_manifest.csv (opcional até 7B.15)",
        "extraidos_motor_fase7a_pass1_v2_block_16_resolved_manifest.csv (opcional até 7B.16)",
        "extraidos_motor_fase7a_pass1_v2_block_17_resolved_manifest.csv (opcional até 7B.17)",
        "extraidos_motor_fase7a_pass1_v2_block_18_resolved_manifest.csv (opcional até 7B.18)",
        "extraidos_motor_fase7a_pass1_v2_block_19_resolved_manifest.csv (opcional até 7B.19)",
        "extraidos_motor_fase7a_pass1_v2_block_20_resolved_manifest.csv (opcional até 7B.20)",
        "extraidos_motor_fase7a_pass1_v2_block_21_resolved_manifest.csv (opcional até 7B.21)",
        "extraidos_motor_fase7a_pass1_v2_block_22_resolved_manifest.csv (opcional até 7B.22)",
        "extraidos_motor_fase7a_pass1_v2_block_23_resolved_manifest.csv (opcional até 7B.23)",
        "extraidos_motor_fase7a_pass1_v2_block_24_resolved_manifest.csv (opcional até 7B.24)",
        "extraidos_motor_fase7a_pass1_v2_block_25_resolved_manifest.csv (opcional até 7B.25)",
        "revisao_manual_amarelos_b14_b20_aprovados.csv (PROMOCAO_MANUAL_REVISADA_CURSOR; lido a partir de 7B.21+)",
    ]

    # extrair bloco numerico do phase_slug (e.g. "7b21" -> 21)
    try:
        prio_pass1_max_bn = int(phase_slug.replace("7b", ""))
    except Exception:
        prio_pass1_max_bn = 10
    prio_list = [_pass1_tag(n) for n in range(prio_pass1_max_bn, 0, -1)] + [
        "RELEASE_V1_RETRY",
        "MANIFEST_RETRY_BLOCO_NN",
        "MANIFEST_LEGACY_RETRY_BACKLOG",
        "INDICE_VERDE_LIMPO",
    ]

    fase_human = {
        "7b4": "7B.4 — B04",
        "7b5": "7B.5 — B05",
        "7b6": "7B.6 — B06",
        "7b7": "7B.7 — B07",
        "7b8": "7B.8 — B08",
        "7b9": "7B.9 — B09",
        "7b10": "7B.10 — B10",
        "7b11": "7B.11 — B11",
        "7b12": "7B.12 — B12",
        "7b13": "7B.13 — B13",
        "7b14": "7B.14 — B14",
        "7b15": "7B.15 — B15",
        "7b16": "7B.16 — B16",
        PHASE_7B17: "7B.17 — B17",
        PHASE_7B18: "7B.18 — B18",
        PHASE_7B19: "7B.19 — B19",
        PHASE_7B20: "7B.20 — B20",
        PHASE_7B21: "7B.21 — B21",
        PHASE_7B22: "7B.22 — B22 + PROMOCAO_MANUAL_REVISADA_CURSOR (B14-B20)",
        PHASE_7B23: "7B.23 — B23",
        PHASE_7B24: "7B.24 — B24",
        PHASE_7B25: "7B.25 — B25",
        PHASE_7B26: "7B.26 — B26",
        PHASE_7B27: "7B.27 — B27",
        PHASE_7B28: "7B.28 — B28",
        PHASE_7B29: "7B.29 — B29",
        PHASE_7B30: "7B.30 — B30",
        PHASE_7B31: "7B.31 — B31",
        PHASE_7B32: "7B.32 — B32",
        PHASE_7B33: "7B.33 — B33",
        PHASE_7B34: "7B.34 — B34",
        PHASE_7B35: "7B.35 — B35",
        PHASE_7B36: "7B.36 — B36 (operação resgate)",
        PHASE_7B37: "7B.37 — B37 (operação resgate)",
        PHASE_7B38: "7B.38 — B38 (operação resgate)",
        PHASE_7B39: "7B.39 — B39 (operação resgate)",
        PHASE_7B40: "7B.40 — B40 (operação resgate)",
        PHASE_7B41: "7B.41 — B41 (operação resgate)",
        PHASE_7B42: "7B.42 — B42 (operação resgate)",
        PHASE_7B43: "7B.43 — B43 (operação resgate)",
        PHASE_7B44: "7B.44 — B44 (operação resgate, último lote cheio)",
        PHASE_7B45: "7B.45 — B45 (encerramento pool resgate)",
        PHASE_7B46: "7B.46 — B46 (nova era inéditos — massa física solta)",
    }[phase_slug]

    expect_total_window = {
        "7b4": (441, 445),
        "7b5": (452, 458),
        "7b6": (465, 475),
        "7b7": (477, 495),
        "7b8": (488, 498),
        "7b9": (502, 512),
        "7b10": (515, 525),
        "7b11": (527, 537),
        # 7B.12: baseline 7B.11=530 + 13 VERDE_SEGURO em B12 (0 V_C_A no resolved_manifest).
        "7b12": (540, 545),
        # 7B.13: baseline 7B.12=543 + 13 VERDE_SEGURO em B13 (0 V_C_A no resolved_manifest).
        "7b13": (553, 558),
        # 7B.14: baseline 7B.13=556 + esperado ~12-14 do bloco 14 (taxa historica 86-100%).
        "7b14": (565, 572),
        # 7B.15: baseline 7B.14=568 + esperado ~12-14 do bloco 15 (taxa historica 86-100%).
        "7b15": (577, 584),
        # 7B.16: baseline 7B.15=580 + esperado ~12-14 do bloco 16 (taxa historica 86-100%).
        "7b16": (589, 596),
        # 7B.17: baseline 7B.16=591 + esperado ~11-14 do bloco 17 (PDFs recentes mais duros).
        PHASE_7B17: (600, 607),
        # 7B.18: baseline 7B.17=599 + esperado ~10-14 do bloco 18 (pool segue duro).
        PHASE_7B18: (609, 613),
        # 7B.19: baseline 7B.18=607 + esperado ~8-12 do bloco 19 (plato dureza ~57%).
        PHASE_7B19: (615, 619),
        # 7B.20: baseline 7B.19=617 + esperado ~10-13 do bloco 20.
        PHASE_7B20: (627, 630),
        # 7B.21: baseline 7B.20=626 + esperado ~9-13 do bloco 21 (chaves OK pos-reset diario).
        PHASE_7B21: (635, 639),
        # 7B.22: baseline 7B.21=637 + +26 promocao manual B14-B20 + esperado ~10-13 do bloco 22.
        PHASE_7B22: (670, 680),
        # 7B.23: baseline 7B.22=675 + esperado ~10-13 do bloco 23 (mantendo patamar 78-86%).
        PHASE_7B23: (684, 690),
        # 7B.24: baseline 7B.23=684 + esperado ~9-12 (taxa volátil 64-86% no pool atual).
        PHASE_7B24: (693, 696),
        # 7B.25: baseline 7B.24~694 + esperado ~9-12; meta operacional 700.
        PHASE_7B25: (702, 708),
        # 7B.26–28: retomada pós-clean-slate rumo a 1600; pool recente oscilando ~57–86%.
        PHASE_7B26: (710, 718),
        PHASE_7B27: (718, 730),
        PHASE_7B28: (726, 742),
        # 7B.29: baseline pós-B28 (~737 OFICIAL) + até 11 VERDE_SEGURO típicos do bloco.
        PHASE_7B29: (738, 755),
        # 7B.30: baseline pós-B29 (~748 OFICIAL) + até 14 VERDE_SEGURO típicos do bloco.
        PHASE_7B30: (752, 772),
        # 7B.31: baseline pós-B30 (~762 OFICIAL) + até 12 VERDE_SEGURO típicos do bloco.
        PHASE_7B31: (768, 788),
        # 7B.32: baseline pós-B31 (~774 OFICIAL) + até 12 VERDE_SEGURO típicos do bloco.
        PHASE_7B32: (780, 802),
        # 7B.33: baseline pós-B32 (~786 OFICIAL) + até 10 VERDE_SEGURO típicos do bloco.
        PHASE_7B33: (792, 812),
        # 7B.34: baseline pós-B33 (~796 OFICIAL) + até ~12 VERDE/COM_ALERTA típicos (meta ≥800 OFICIAL).
        PHASE_7B34: (800, 825),
        # 7B.35: baseline pós-B34 (~808 OFICIAL) + até ~3 VERDE_SEGURO / COM_ALERTA do bloco 35 (pool misto).
        PHASE_7B35: (808, 820),
        # 7B.36: baseline pós-B35 (~811 OFICIAL) + 14 promovidos (operação resgate, union VCA).
        PHASE_7B36: (820, 830),
        # 7B.37: baseline pós-B36 (~825 OFICIAL) + até 14 promovidos (resgate, union VCA).
        PHASE_7B37: (835, 845),
        PHASE_7B38: (830, 840),
        PHASE_7B39: (829, 845),
        PHASE_7B40: (829, 845),
        PHASE_7B41: (835, 855),
        PHASE_7B42: (844, 865),
        PHASE_7B43: (853, 875),
        PHASE_7B44: (862, 885),
        PHASE_7B45: (869, 895),
        # 7B.46: baseline pós-B45 (869 OFICIAL) + até 14 inéditos (pool VOGE/NEMA/IEC).
        PHASE_7B46: (869, 890),
    }
    wl, wh = expect_total_window[phase_slug]

    summary = {
        "generated_at": utc,
        "fase_cli": phase_slug,
        "fase_human": fase_human,
        "offline_only": True,
        "promoted_pass1_block_number": promoted_bn,
        "backup_files_suffix_example": f".bak_pre_{phase_tag}_{ts_safe}",
        "fonte_release_ordem_prioridade": prio_list,
        "politica_manifestos_e_regra_d": {
            "manifest_oficial_sources": manifest_src,
            "safe_green_candidates_bloco_02": "Informativo — SHA já cobertos por manifests PASS1-v2 não geram CANDIDATO.",
            "regra_d_scope": "Somente aplicada a INDICE_VERDE_LIMPO (SHA fora da união sha_oficial_por_manifest).",
            "regra_c_basenames_politica_total": sorted(forbidden_bn_all),
        },
        "totais_sha_unicos": {
            "OFICIAL_total": oficiais,
            "OFICIAL_por_fonte": dict(br_fonte_of),
            "CANDIDATOS": cands,
            "TOTAL_linhas_master_manifest_csv": oficiais + cands,
        },
        "comparacao_vs_manifest_anterior": {
            "OFICIAL_total_antes_snapshot_ficheiro_anterior": len(old_oficial_sha),
            "OFICIAL_total_apos_run": oficiais,
            "delta_OFICIAL": delta,
            "sha_promovidos_total_vs_anterior": len(reincorporados),
            "overlap_manifest_v1_com_indice_limpo_count": len(indice_kept_overlap_manifest),
        },
        "verificacao_promoted_block": {
            "promoted_block": promoted_bn,
            "promoted_fonte_release": promo_tag_str,
            "sha_resolved_manifest_promoted": sorted(promoted_resolved_shas),
            "sha_que_entraram_na_fonte_PROMOTED_na_OFICIAL": sha_promo_ord,
            "contagem_na_OFICIAL_com_fonte_PROMOTED": len(sha_promo_ord),
            "legacy_candidato_b02_sha_antes_snapshot": sorted(old_candidato_b02_sha),
            "sha_desapareceram_inesperado": desapareceram,
            "sha_novos_inesperado_alem_manifest_promoted": novos_inesperado,
            "primeiros_10_promoted_conferencia": primeira10_pk,
            "primeira_linha_PROMOTED_oficial": pk_primeira_linha,
            "ultima_linha_PROMOTED_oficial": pk_ultima_linha,
        },
        "exclusoes_observacao": dict(motivo_tokens),
        "total_linhas_excluidos": len(excluded),
        "manual_flag_conflito_indices": {
            "sha_alguma_precisa_manual": len(conflict_manual_index),
            "sha_linha_verde_e_manual_1": len(verde_manual_linha_conflict),
        },
        "sanidade": {
            "OFICIAL_total_janela_esperado": {"min": wl, "max": wh, "ok": wl <= oficiais <= wh},
            "PASS1_promoted_OFICIAL_count": len(sha_promo_ord),
            "PROMOCAO_MANUAL_REVISADA_CURSOR_OFICIAL": br_fonte_of.get("PROMOCAO_MANUAL_REVISADA_CURSOR", 0),
            "PASS1_V2_B46_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_46_RECONCILIADO", 0),
            "PASS1_V2_B45_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_45_RECONCILIADO", 0),
            "PASS1_V2_B44_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_44_RECONCILIADO", 0),
            "PASS1_V2_B43_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_43_RECONCILIADO", 0),
            "PASS1_V2_B42_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_42_RECONCILIADO", 0),
            "PASS1_V2_B41_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_41_RECONCILIADO", 0),
            "PASS1_V2_B40_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_40_RECONCILIADO", 0),
            "PASS1_V2_B39_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_39_RECONCILIADO", 0),
            "PASS1_V2_B38_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_38_RECONCILIADO", 0),
            "PASS1_V2_B37_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_37_RECONCILIADO", 0),
            "PASS1_V2_B36_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_36_RECONCILIADO", 0),
            "rescue_amnesty_shas_count": len(rescue_amnesty_shas),
            "PASS1_V2_B35_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_35_RECONCILIADO", 0),
            "PASS1_V2_B34_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_34_RECONCILIADO", 0),
            "PASS1_V2_B33_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_33_RECONCILIADO", 0),
            "PASS1_V2_B32_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_32_RECONCILIADO", 0),
            "PASS1_V2_B31_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_31_RECONCILIADO", 0),
            "PASS1_V2_B30_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_30_RECONCILIADO", 0),
            "PASS1_V2_B29_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_29_RECONCILIADO", 0),
            "PASS1_V2_B28_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_28_RECONCILIADO", 0),
            "PASS1_V2_B27_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_27_RECONCILIADO", 0),
            "PASS1_V2_B26_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_26_RECONCILIADO", 0),
            "PASS1_V2_B25_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_25_RECONCILIADO", 0),
            "PASS1_V2_B24_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_24_RECONCILIADO", 0),
            "PASS1_V2_B23_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_23_RECONCILIADO", 0),
            "PASS1_V2_B22_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_22_RECONCILIADO", 0),
            "PASS1_V2_B21_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_21_RECONCILIADO", 0),
            "PASS1_V2_B20_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_20_RECONCILIADO", 0),
            "PASS1_V2_B19_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_19_RECONCILIADO", 0),
            "PASS1_V2_B18_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_18_RECONCILIADO", 0),
            "PASS1_V2_B17_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_17_RECONCILIADO", 0),
            "PASS1_V2_B16_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_16_RECONCILIADO", 0),
            "PASS1_V2_B15_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_15_RECONCILIADO", 0),
            "PASS1_V2_B14_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_14_RECONCILIADO", 0),
            "PASS1_V2_B13_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_13_RECONCILIADO", 0),
            "PASS1_V2_B12_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_12_RECONCILIADO", 0),
            "PASS1_V2_B11_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_11_RECONCILIADO", 0),
            "PASS1_V2_B10_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_10_RECONCILIADO", 0),
            "PASS1_V2_B09_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_09_RECONCILIADO", 0),
            "PASS1_V2_B08_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_08_RECONCILIADO", 0),
            "PASS1_V2_B07_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_07_RECONCILIADO", 0),
            "PASS1_V2_B06_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_06_RECONCILIADO", 0),
            "PASS1_V2_B05_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_05_RECONCILIADO", 0),
            "PASS1_V2_B04_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_04_RECONCILIADO", 0),
            "PASS1_V2_B03_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_03_RECONCILIADO", 0),
            "PASS1_V2_B02_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_02_RECONCILIADO", 0),
            "PASS1_V2_B01_OFICIAL": br_fonte_of.get("PASS1_V2_BLOCO_01_RECONCILIADO", 0),
            "INDICE_VERDE_LIMPO_linhas_esperado_337": br_fonte_of.get("INDICE_VERDE_LIMPO", 0) == 337,
            "RELEASE_V1_RETRY_linhas_esperado_64": br_fonte_of.get("RELEASE_V1_RETRY", 0) == 64,
            "CANDIDATOS_esperado_zero": cands == 0,
        },
        "apenas_INDICE_SEM_release_v1_path_label": apenas_indice_pk,
        "oficial_overlap_indice_verde_false_count": overlap_ix_false_pk,
        "gap_meta": {"meta": META_DEPLOY_GAP, "gap_1600_menos_OFICIAL": gap, "recomendacao": rec},
        "inputs_contagem_interna": {
            "manifest_union_sha": len(sha_manifest_oficial),
            "release_v1_csv_sha_distintos": len(rv1_sha_set),
            "indice_limpo_criterios_sha_pres_exclusoes": len(indice_limpo_input_sha),
        },
        "cumprimento": {
            "sem_gemini_extract_ciclos": True,
            "sem_rebuild_index": True,
            "sem_supabase_app_gold_sql": True,
            "sem_mutar_manifest_originais": True,
            "sem_mutar_processed_image_index": True,
            "script": "scripts/master_release_v2_build_offline.py",
        },
    }

    REVIEW_DIR.joinpath("master_release_v2.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    isolados_confirmados = sorted(forbidden_bn_all)
    md = [
        f"# Master release v2 ({utc}) — `{fase_human}`",
        "",
        "## Totais OFICIAL",
        "",
        f"- **OFICIAL_total**: **{oficiais}**",
        f"- **CANDIDATO** bloco 02 safe_green legacy: **{cands}**",
        "",
        "### OFICIAL por `fonte_release`",
        "",
        *[f"- **{k}**: **{v}**" for k, v in sorted(br_fonte_of.items(), key=lambda x: (-x[1], x[0]))],
        "",
        f"## Comparativo (run `{phase_slug}`)",
        "",
        f"- OFICIAL antes (ficheiro anterior): **{len(old_oficial_sha)}**",
        f"- OFICIAL agora: **{oficiais}** (**Δ={delta:+d}**)",
        f"- SHA **`{promo_tag_str}`** presentes como OFICIAL: **{len(sha_promo_ord)}** (diff: `{diff_name}`)",
        "",
        "## Basenames políticos (`pass1_v2_progress.NO_AUTO` + isolados retry)",
        "",
        "```text",
        *isolados_confirmados,
        "```",
        "",
        f"- **GAP 1600**: **{gap}** · **Recomendação**: `{rec}`",
        "",
    ]
    REVIEW_DIR.joinpath("master_release_v2.md").write_text("\n".join(md), encoding="utf-8")

    diff_fp = REVIEW_DIR / diff_name
    lista_pk = promoted_resolved_shas
    diff_fp.write_text(
        "\n".join(
            [
                f"# Diff `{phase_tag}` (`{utc}`)",
                "",
                "## Resumo",
                "",
                f"- **Δ OFICIAL** vs ficheiro anterior: **{delta:+d}** (antes **{len(old_oficial_sha)}**, depois **{oficiais}**)",
                f"- **SHA `{promo_tag_str}`** na linha mestre OFICIAL: **{len(sha_promo_ord)}** (resolved tinha **{len(lista_pk)}**) ; alert/manual excluem via regras a/b/c)",
                "",
                "## Conferência PROMOTED (ordenado)",
                "",
                f"- Primeira: {pk_primeira_linha}",
                f"- Última: {pk_ultima_linha}",
                "",
                "```text",
                *sha_promo_ord,
                "```",
                "",
                "## Extra inesperado além promoted",
                "```text",
                *(novos_inesperado or ["(vazio)"]),
                "```",
                "",
                "## Shaíram DO OFICIAL",
                "```text",
                *(desapareceram or ["(vazio)"]),
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "ok": True,
                "phase": phase_slug,
                "OFICIAL": oficiais,
                "CANDIDATO": cands,
                "delta": delta,
                "PROMOTED_BLOCK": promoted_bn,
                "PROMOTED_OFICIAL_count": len(sha_promo_ord),
                "recomendacao": rec,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
