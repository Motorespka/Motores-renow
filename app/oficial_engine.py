#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Motor de calculo proporcional e catalogo 'file' do acervo OFICIAL."""

from __future__ import annotations

import hashlib
import json
import math
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional

from app.search_lib import (
    DEFAULT_DB,
    MotorRow,
    connect,
    find_similar,
    load_all_motors,
    norm_carcaca,
    parse_awg_number,
    parse_mm,
    parse_passo_nums,
    parse_scalar,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
MASTER_CSV = REPO_ROOT / "exports" / "review" / "master_release_v2_manifest.csv"
ENGINEERING_SAVES = REPO_ROOT / "exports" / "review" / "official_engineering_saves.jsonl"


def is_file_record(m: MotorRow) -> bool:
    """Registro completo para calculo matematico (sem None nos campos criticos)."""
    return bool(
        m.diametro_mm
        and m.pacote_mm
        and m.carcaca.strip()
        and m.passo_principal.strip()
        and m.fio_principal.strip()
        and m.espiras_principal is not None
    )


def filter_file(motors: list[MotorRow]) -> list[MotorRow]:
    return [m for m in motors if is_file_record(m)]


def stator_area_mm2(diameter_mm: float) -> float:
    return math.pi * (diameter_mm / 2.0) ** 2


def proportional_espiras(
    espiras_historico: float,
    pacote_historico: float,
    pacote_entrada: float,
    diametro_historico: float,
    diametro_entrada: float,
) -> float:
    """
    Espiras_Calculadas = Espiras_Historico * (Pacote_Entrada / Pacote_Historico)
                         * (Area_Entrada / Area_Historico)
    Area proporcional ao quadrado do diametro interno.
    """
    if pacote_historico <= 0 or diametro_historico <= 0:
        raise ValueError("Dimensoes historicas invalidas para proporcao.")
    area_ratio = stator_area_mm2(diametro_entrada) / stator_area_mm2(diametro_historico)
    pacote_ratio = pacote_entrada / pacote_historico
    return round(espiras_historico * pacote_ratio * area_ratio, 1)


@dataclass
class ProportionalHit:
    sha: str
    arquivo_rel: str
    score: float
    diametro_mm: float
    pacote_mm: float
    carcaca: str
    passo_principal: str
    ligacao: str
    fio_principal: str
    espiras_historico: float
    espiras_calculadas: float
    fio_sugerido_awg: Optional[float]
    pacote_ratio: float = 0.0
    area_ratio: float = 0.0


@dataclass
class CalculationSuggestion:
    entrada: dict[str, Any]
    top_matches: list[ProportionalHit]
    espiras_media_top5: Optional[float]
    fio_medio_top5: Optional[float]
    passo_moda: str
    carcaca_moda: str
    n_file_catalog: int
    n_matches: int
    modo_processamento: str = "proporcional"
    sugestao_espira: Optional[float] = None
    sugestao_fio_awg: Optional[float] = None
    justificativa_tecnica: str = ""
    alerta_risco: str = ""
    gemini_usado: bool = False
    dispersao_espiras: float = 0.0


def _ligacao_from_row(m: MotorRow) -> str:
    return m.ligacao or ""


def _coef_variation(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    if mean <= 0:
        return 0.0
    var = sum((x - mean) ** 2 for x in values) / len(values)
    return (var**0.5) / mean


def suggest_calculation(
    motors: list[MotorRow],
    *,
    diametro_mm: float,
    pacote_mm: float,
    carcaca: str,
    passo: str,
    ligacao: str = "",
    fio_engenheiro: str = "",
    espiras_engenheiro: str = "",
    top_k: int = 5,
    use_gemini: bool = True,
) -> CalculationSuggestion:
    file_pool = filter_file(motors)
    matches = find_similar(
        file_pool,
        diametro_mm=diametro_mm,
        pacote_mm=pacote_mm,
        carcaca=carcaca,
        passo=passo,
        top_k=top_k,
    )

    lig_key = norm_carcaca(ligacao)
    hits: list[ProportionalHit] = []
    calculos_payload: list[dict[str, Any]] = []

    for mt in matches:
        m = mt.motor
        if lig_key:
            ml = norm_carcaca(_ligacao_from_row(m))
            if ml and lig_key not in ml and ml not in lig_key:
                continue
        esp_h = float(m.espiras_principal or 0)
        d_hist = float(m.diametro_mm or 0)
        p_hist = float(m.pacote_mm or 0)
        if esp_h <= 0 or d_hist <= 0 or p_hist <= 0:
            continue
        pacote_ratio = pacote_mm / p_hist
        area_ratio = stator_area_mm2(diametro_mm) / stator_area_mm2(d_hist)
        esp_c = round(esp_h * pacote_ratio * area_ratio, 1)
        hits.append(
            ProportionalHit(
                sha=m.sha,
                arquivo_rel=m.arquivo_rel,
                score=mt.score,
                diametro_mm=d_hist,
                pacote_mm=p_hist,
                carcaca=m.carcaca,
                passo_principal=m.passo_principal,
                ligacao=_ligacao_from_row(m),
                fio_principal=m.fio_principal,
                espiras_historico=esp_h,
                espiras_calculadas=esp_c,
                fio_sugerido_awg=parse_awg_number(m.fio_principal),
                pacote_ratio=round(pacote_ratio, 4),
                area_ratio=round(area_ratio, 4),
            )
        )
        calculos_payload.append(
            {
                "arquivo": m.arquivo_rel,
                "espiras_historico": esp_h,
                "espiras_calculadas": esp_c,
                "pacote_ratio": round(pacote_ratio, 4),
                "area_ratio": round(area_ratio, 4),
                "diametro_hist_mm": d_hist,
                "pacote_hist_mm": p_hist,
                "formula": f"{esp_h} * {pacote_ratio:.4f} * {area_ratio:.4f} = {esp_c}",
            }
        )

    esp_calc = [h.espiras_calculadas for h in hits]
    dispersao = round(_coef_variation(esp_calc), 4)
    media_prop = round(sum(esp_calc) / len(esp_calc), 1) if esp_calc else None
    fio_list = [h.fio_sugerido_awg for h in hits if h.fio_sugerido_awg is not None]
    media_fio = round(sum(fio_list) / len(fio_list), 2) if fio_list else None

    passo_moda = ""
    carcaca_moda = ""
    if hits:
        passos = [h.passo_principal for h in hits if h.passo_principal]
        carcasas = [h.carcaca for h in hits if h.carcaca]
        passo_moda = max(set(passos), key=passos.count) if passos else ""
        carcaca_moda = max(set(carcasas), key=carcasas.count) if carcasas else ""

    entrada = {
        "diametro_mm": diametro_mm,
        "pacote_mm": pacote_mm,
        "carcaca": carcaca,
        "passo": passo,
        "ligacao": ligacao,
    }

    sugestao_espira = media_prop
    sugestao_fio = media_fio
    justificativa = ""
    alerta = ""
    gemini_usado = False
    modo = "proporcional"

    referencias_escassas = len(hits) < 3
    discrepante = dispersao > 0.22
    eng_esp = parse_scalar(espiras_engenheiro)
    if eng_esp and media_prop and abs(eng_esp - media_prop) / max(media_prop, 1) > 0.2:
        discrepante = True

    must_gemini = use_gemini and (referencias_escassas or discrepante or len(hits) > 0)

    if must_gemini:
        try:
            from services.gemini_engineering_validator import validate_with_gemini

            gem = validate_with_gemini(
                {
                    "entrada": entrada,
                    "calculos_proporcionais": calculos_payload,
                    "media_proporcional_espiras": media_prop,
                    "dispersao_espiras": dispersao,
                    "referencias_escassas": referencias_escassas,
                    "fio_engenheiro": fio_engenheiro,
                    "espiras_engenheiro": espiras_engenheiro,
                }
            )
            sugestao_espira = gem.get("sugestao_espira", media_prop)
            sugestao_fio = gem.get("sugestao_fio_awg", media_fio)
            justificativa = gem.get("justificativa_tecnica", "")
            alerta = gem.get("alerta_risco", "")
            gemini_usado = True
            modo = "proporcional+gemini"
        except Exception as exc:
            justificativa = (
                f"Media proporcional de {len(hits)} referencia(s): {media_prop} espiras. "
                f"(Gemini indisponivel: {exc})"
            )
            if discrepante or referencias_escassas:
                alerta = "Poucas referencias ou alta dispersao — revisar manualmente."
            modo = "proporcional_sem_gemini"
    elif media_prop is not None:
        justificativa = (
            f"Calculado por proporcionalidade em {len(hits)} motor(es): "
            f"Espiras = Espiras_hist x (Pacote_in/Pacote_hist) x (Area_in/Area_hist). "
            f"Media das espiras calculadas: {media_prop}."
        )

    return CalculationSuggestion(
        entrada=entrada,
        top_matches=hits,
        espiras_media_top5=media_prop,
        fio_medio_top5=media_fio,
        passo_moda=passo_moda,
        carcaca_moda=carcaca_moda,
        n_file_catalog=len(file_pool),
        n_matches=len(hits),
        modo_processamento=modo,
        sugestao_espira=sugestao_espira,
        sugestao_fio_awg=sugestao_fio,
        justificativa_tecnica=justificativa,
        alerta_risco=alerta,
        gemini_usado=gemini_usado,
        dispersao_espiras=dispersao,
    )


def load_catalog(db_path: Path | None = None) -> tuple[list[MotorRow], dict[str, str]]:
    conn = connect(db_path or DEFAULT_DB)
    motors = load_all_motors(conn)
    meta = {r["key"]: r["value"] for r in conn.execute("SELECT key, value FROM index_meta").fetchall()}
    conn.close()
    return motors, meta


def save_official_calculation(
    payload: dict[str, Any],
    *,
    db_path: Path | None = None,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    """Persiste calculo validado: JSONL + manifest + upsert SQLite."""
    import csv
    from datetime import datetime, timezone

    db = db_path or DEFAULT_DB
    manifest = manifest_path or MASTER_CSV
    utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    sha = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    arquivo_rel = f"engineering_oficial\\{sha[:16]}_calculo.json"

    row_jsonl = {
        "generated_at": utc,
        "arquivo_rel": arquivo_rel,
        "sha256_arquivo": sha,
        "tipo": "ENGINEERING_SAVE",
        "resultado": {
            "diametro_mm": str(payload.get("diametro_mm", "")),
            "pacote_mm": str(payload.get("pacote_mm", "")),
            "carcaca": payload.get("carcaca", ""),
            "passo_principal": payload.get("passo", ""),
            "fio_principal": str(payload.get("fio_principal", "")),
            "espiras_principal": str(payload.get("espiras_principal", "")),
            "ligacao": payload.get("ligacao", ""),
            "observacoes": payload.get("observacoes", "Salvo via admin demo-calculo"),
        },
    }

    ENGINEERING_SAVES.parent.mkdir(parents=True, exist_ok=True)
    with ENGINEERING_SAVES.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row_jsonl, ensure_ascii=False) + "\n")

    manifest_row = {
        "arquivo_rel": arquivo_rel,
        "sha256_arquivo": sha,
        "melhor_status": "VERDE_SEGURO",
        "fonte_ultimo_processamento": "admin/demo-calculo",
        "output_tag": "engineering_oficial_save",
        "status_release": "OFICIAL",
        "fonte_release": "ENGINEERING_ADMIN_SAVE",
        "overlap_release_v1": "false",
        "overlap_indice_verde": "false",
        "nota_indice": "CALCULO_ENGENHARIA_VALIDADO",
        "updated_at_indice": utc,
    }
    fieldnames = list(manifest_row.keys())
    if manifest.is_file():
        with manifest.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames:
                fieldnames = list(reader.fieldnames)
    with manifest.open("a", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writerow(manifest_row)

    d_mm = parse_mm(str(payload.get("diametro_mm", "")))
    p_mm = parse_mm(str(payload.get("pacote_mm", "")))
    esp = parse_scalar(str(payload.get("espiras_principal", "")))
    conn = sqlite3.connect(db)
    conn.execute(
        """
        INSERT OR REPLACE INTO motores_oficial (
            sha, arquivo_rel, melhor_status, carcaca, carcaca_norm,
            diametro_mm, pacote_mm, diametro_raw, pacote_raw,
            passo_principal, passo_nums_json,
            fio_principal, fio_principal_num, espiras_principal,
            fio_auxiliar, fio_auxiliar_num, espiras_auxiliar,
            potencia_cv, polos, tipo_motor, source_jsonl, is_file, ligacao
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        [
            sha,
            arquivo_rel,
            "VERDE_SEGURO",
            payload.get("carcaca", ""),
            norm_carcaca(str(payload.get("carcaca", ""))),
            d_mm,
            p_mm,
            str(payload.get("diametro_mm", "")),
            str(payload.get("pacote_mm", "")),
            payload.get("passo", ""),
            json.dumps(parse_passo_nums(str(payload.get("passo", "")))),
            str(payload.get("fio_principal", "")),
            parse_awg_number(str(payload.get("fio_principal", ""))),
            esp,
            "",
            None,
            None,
            "",
            "",
            "engineering",
            "official_engineering_saves.jsonl",
            1,
            payload.get("ligacao", ""),
        ],
    )
    conn.commit()
    conn.close()

    return {"sha256_arquivo": sha, "arquivo_rel": arquivo_rel, "saved_at": utc}
