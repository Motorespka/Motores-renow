#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Motor de calculo proporcional e catalogo 'file' do acervo OFICIAL."""

from __future__ import annotations

import hashlib
import json
import logging
import math
import sqlite3
from dataclasses import asdict, dataclass, field
from pathlib import Path
from statistics import median
from typing import Any, Optional

from app.search_lib import (
    DEFAULT_DB,
    MotorRow,
    awg_from_mm2,
    awg_to_mm2,
    connect,
    find_similar,
    load_all_motors,
    norm_carcaca,
    parse_awg_number,
    parse_mm,
    parse_passo_nums,
    parse_scalar,
    passo_canonical,
    slot_fill_units,
)

logger = logging.getLogger(__name__)

HIST_DIVERGENCE_REVISAR_PCT = 0.10
SLOT_FILL_TOLERANCE = 1.02

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
    validation_status: str = ""
    validation_message: str = ""
    lei_ranhura_logs: list[str] = field(default_factory=list)
    media_historica_espiras: Optional[float] = None
    slot_fill_limit: Optional[float] = None
    slot_fill_actual: Optional[float] = None


def _ligacao_from_row(m: MotorRow) -> str:
    return m.ligacao or ""


def _apply_slot_law(
    hits: list[ProportionalHit],
    esp_sug: float,
    fio_base: Optional[float],
) -> tuple[Optional[float], list[str], Optional[float], Optional[float]]:
    """
    Conservação de enchimento: (espiras * secao_fio) <= limite historico do passo.
    Se espiras sobem vs mediana historica, AWG deve subir (fio mais fino).
    """
    logs: list[str] = []
    fills_hist: list[float] = []
    for h in hits:
        awg = h.fio_sugerido_awg
        if awg and h.espiras_historico > 0:
            fills_hist.append(slot_fill_units(h.espiras_historico, awg))

    if not fills_hist or esp_sug <= 0:
        return fio_base, logs, None, None

    limite = max(fills_hist)
    esp_hist_med = median([h.espiras_historico for h in hits if h.espiras_historico > 0])
    fio_adj = fio_base

    if fio_adj is None and hits:
        awgs = [h.fio_sugerido_awg for h in hits if h.fio_sugerido_awg is not None]
        fio_adj = median(awgs) if awgs else None

    if fio_adj is None:
        return None, logs, round(limite, 4), None

    area_atual = awg_to_mm2(fio_adj)
    fill_atual = slot_fill_units(esp_sug, fio_adj)

    if esp_sug > esp_hist_med * 1.001:
        area_max = limite / esp_sug
        fio_thinner = awg_from_mm2(area_max)
        if fio_thinner is not None and fio_thinner > fio_adj:
            logs.append(
                f"Lei da ranhura: espiras subiram ({esp_sug:.1f} vs med. hist. {esp_hist_med:.1f}); "
                f"fio ajustado AWG {fio_adj:.1f} -> {fio_thinner:.1f} (secao menor)."
            )
            fio_adj = fio_thinner
    elif esp_sug < esp_hist_med * 0.999:
        area_allow = min(limite / esp_sug, area_atual * 1.15)
        fio_thicker = awg_from_mm2(area_allow)
        if fio_thicker is not None and fio_thicker < fio_adj:
            logs.append(
                f"Lei da ranhura: espiras caíram ({esp_sug:.1f} vs med. hist. {esp_hist_med:.1f}); "
                f"fio pode aumentar AWG {fio_adj:.1f} -> {fio_thicker:.1f}."
            )
            fio_adj = fio_thicker

    fill_final = slot_fill_units(esp_sug, fio_adj)
    if fill_final > limite * SLOT_FILL_TOLERANCE:
        fio_force = awg_from_mm2(limite / esp_sug)
        if fio_force is not None:
            logs.append(
                f"Enchimento {fill_final:.4f} excede limite {limite:.4f}; "
                f"fio forcado para AWG {fio_force:.1f}."
            )
            fio_adj = fio_force
            fill_final = slot_fill_units(esp_sug, fio_adj)

    logs.append(
        f"Enchimento ranhura: {fill_final:.4f} <= limite {limite:.4f} "
        f"(Espiras×mm²_fio, tol. {SLOT_FILL_TOLERANCE:.0%})."
    )
    return round(fio_adj, 1), logs, round(limite, 4), round(fill_final, 4)


def _resolve_validation(
    *,
    hits: list[ProportionalHit],
    esp_sug: Optional[float],
    passo: str,
    slot_ok: bool,
    hist_divergence: bool,
    referencias_escassas: bool,
    discrepante: bool,
) -> tuple[str, str]:
    if not (passo or "").strip():
        return "INCOMPLETO", "Informe o passo de bobinagem para aplicar a Lei da Ranhura."

    if not hits:
        pk = passo_canonical(passo)
        return (
            "SEM_REFERENCIA",
            f"Nenhum motor OFICIAL com passo exato '{pk or passo}' e geometria compatível.",
        )

    if referencias_escassas:
        return "REVISAR", "Menos de 3 referências com o mesmo passo — revisar na bancada."

    if hist_divergence:
        return (
            "REVISAR",
            f"Sugestão diverge >{HIST_DIVERGENCE_REVISAR_PCT:.0%} da média histórica do passo.",
        )

    if not slot_ok:
        return "REVISAR", "Enchimento de ranhura acima do limite histórico — ajustar fio ou espiras."

    if discrepante:
        return "REVISAR", "Alta dispersão entre referências proporcionais do mesmo passo."

    return "APROVADO", "Cálculo proporcional alinhado ao passo e à lei da ranhura."


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
    passo_exact = bool((passo or "").strip())
    matches = find_similar(
        file_pool,
        diametro_mm=diametro_mm,
        pacote_mm=pacote_mm,
        carcaca=carcaca,
        passo=passo,
        top_k=top_k,
        passo_exact=passo_exact,
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
    esp_hist = [h.espiras_historico for h in hits if h.espiras_historico > 0]
    dispersao = round(_coef_variation(esp_calc), 4)
    media_prop = round(sum(esp_calc) / len(esp_calc), 1) if esp_calc else None
    media_hist = round(median(esp_hist), 1) if esp_hist else None
    fio_list = [h.fio_sugerido_awg for h in hits if h.fio_sugerido_awg is not None]
    media_fio = round(median(fio_list), 2) if fio_list else None

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
    lei_logs: list[str] = []
    slot_limit: Optional[float] = None
    slot_actual: Optional[float] = None

    if passo_exact:
        lei_logs.append(
            f"Filtro passo exato: '{passo_canonical(passo)}' ({len(hits)} referência(s))."
        )

    referencias_escassas = len(hits) < 3
    discrepante = dispersao > 0.22

    if sugestao_espira is not None:
        sugestao_fio, slot_logs, slot_limit, slot_actual = _apply_slot_law(
            hits, float(sugestao_espira), sugestao_fio
        )
        lei_logs.extend(slot_logs)

    hist_divergence = False
    if sugestao_espira is not None and media_hist and media_hist > 0:
        rel = abs(float(sugestao_espira) - media_hist) / media_hist
        if rel > HIST_DIVERGENCE_REVISAR_PCT:
            hist_divergence = True
            lei_logs.append(
                f"Divergência histórica: sugestão {sugestao_espira} vs média histórica "
                f"{media_hist} ({rel:.1%} > {HIST_DIVERGENCE_REVISAR_PCT:.0%})."
            )
            logger.warning(
                "demo_calculo REVISAR: espiras %.1f diverge %.1f%% da media historica %.1f (passo %s)",
                sugestao_espira,
                rel * 100,
                media_hist,
                passo_canonical(passo),
            )

    slot_ok = True
    if slot_limit and slot_actual and slot_actual > slot_limit * SLOT_FILL_TOLERANCE:
        slot_ok = False
        logger.warning(
            "demo_calculo ranhura: fill %.4f > limite %.4f",
            slot_actual,
            slot_limit,
        )

    validation_status, validation_message = _resolve_validation(
        hits=hits,
        esp_sug=sugestao_espira,
        passo=passo,
        slot_ok=slot_ok,
        hist_divergence=hist_divergence,
        referencias_escassas=referencias_escassas,
        discrepante=discrepante,
    )

    justificativa = (
        f"Cálculo determinístico em {len(hits)} motor(es) com passo "
        f"'{passo_canonical(passo) or passo}': média proporcional {media_prop} espiras."
    )
    alerta = ""
    gemini_usado = False
    modo = "proporcional_deterministico"

    if use_gemini and hits and sugestao_espira is not None:
        try:
            from services.gemini_engineering_validator import justify_with_gemini

            gem = justify_with_gemini(
                {
                    "entrada": entrada,
                    "calculos_proporcionais": calculos_payload,
                    "media_proporcional_espiras": media_prop,
                    "media_historica_espiras": media_hist,
                    "sugestao_espira": sugestao_espira,
                    "sugestao_fio_awg": sugestao_fio,
                    "slot_fill_limit": slot_limit,
                    "slot_fill_actual": slot_actual,
                    "dispersao_espiras": dispersao,
                    "validation_status": validation_status,
                }
            )
            justificativa = gem.get("justificativa_tecnica") or justificativa
            gem_alerta = gem.get("alerta_risco", "")
            if gem_alerta:
                alerta = gem_alerta
            gemini_usado = True
            modo = "proporcional+gemini_justificativa"
        except Exception as exc:
            lei_logs.append(f"Gemini (só justificativa) indisponível: {exc}")
            modo = "proporcional_sem_gemini"

    if validation_status == "REVISAR" and not alerta:
        alerta = validation_message

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
        validation_status=validation_status,
        validation_message=validation_message,
        lei_ranhura_logs=lei_logs,
        media_historica_espiras=media_hist,
        slot_fill_limit=slot_limit,
        slot_fill_actual=slot_actual,
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
