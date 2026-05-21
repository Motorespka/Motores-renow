#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gêmeo digital de motores — Modo Caixa Preta (projeto do zero) e Modo Auditoria.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from engine.physics_audit import (
    B_ABORT_TESLA,
    B_MAX_TESLA,
    MSG_B_ABORT,
    audit_auditoria_user_winding,
    audit_winding_physics,
    check_required_inputs,
    espiras_weg_fem,
)
from engine.winding_sanity import (
    COMMERCIAL_BOBINAGEM_AWGS,
    apply_fem_physics_guard,
    espiras_from_fem_equation,
    select_awg_for_slot_fill,
    estimate_physical_slot_fill_limit,
)
from services.stator_vision_ingest import (
    ImageSource,
    MSG_VISAO_ILEGIVEL,
    extract_stator_geometry_from_images,
    is_vision_reliable,
    merge_vision_into_entrada,
    vision_status_message,
)

MODO_CAIXA_PRETA = "caixa_preta"
MODO_AUDITORIA = "auditoria"


@dataclass
class WindingCandidate:
    opcao: str
    espiras_por_bobina: float
    fio_awg: int
    paralelo: int
    densidade_j: Optional[float]
    ocupacao_ff: float
    confianca_pct: int
    alertas: list[str] = field(default_factory=list)
    descricao: str = ""


@dataclass
class DigitalTwinResult:
    modo: str
    entrada: dict[str, Any]
    completo: bool
    checklist_faltante: list[str] = field(default_factory=list)
    candidatos: list[WindingCandidate] = field(default_factory=list)
    visao: dict[str, Any] = field(default_factory=dict)
    gemini_auditoria: dict[str, Any] = field(default_factory=dict)
    relatorio_markdown: str = ""
    mermaid_validacao: str = ""
    mermaid_ligacao: str = ""
    bloqueado: bool = False
    mensagem_bloqueio: str = ""
    saturacao_abortada: bool = False
    flux_density_b_t: Optional[float] = None


def _ligacao_mermaid(ligacao: str) -> str:
    lig = (ligacao or "").strip().lower()
    if "tri" in lig or "delta" in lig or "△" in lig:
        return """flowchart LR
    U[V linha] --> T[Triângulo Δ]
    T --> W1[Bobina U-V]
    T --> W2[Bobina V-W]
    T --> W3[Bobina W-U]"""
    return """flowchart LR
    N[Neutro] --- Y[Estrela Y]
    Y --> W1[Fase U]
    Y --> W2[Fase V]
    Y --> W3[Fase W]
    U[V linha] --> W1
    U --> W2
    U --> W3"""


def _mermaid_validacao_flow() -> str:
    return """flowchart TD
    A[Entrada geometria + tensao] --> B{FEM B <= 1.5 T?}
    B -->|Nao| C[Corrigir espiras]
    B -->|Sim| D[Calcular ff ranhura]
    D --> E{ff 25-45%?}
    E -->|Nao| F[Alerta ocupacao]
    E -->|Sim| G[Calcular J A/mm2]
    G --> H{J 3-7 A/mm2?}
    H -->|Nao| I[Invalidar / propor AWG]
    H -->|Sim| J[Score confianca]
    J --> K[Relatorio executivo]"""


def _genetic_candidates(
    *,
    espiras_base: float,
    diametro_mm: float,
    pacote_mm: float,
    ranhuras: int,
    polos: Optional[int],
    carcaca: str,
    voltage_v: float,
    n_options: int = 5,
) -> list[WindingCandidate]:
    """3–5 opções cruzando AWG e arranjos (paralelo 1 ou 2)."""
    slot_lim = estimate_physical_slot_fill_limit(ranhuras, diametro_mm, pacote_mm)
    offsets = (0.0, -2.0, 2.0, -4.0, 4.0)
    awg_prefs = (19, 20, 18, 22, 17)
    out: list[WindingCandidate] = []
    for i, (off, pref) in enumerate(zip(offsets, awg_prefs)):
        if len(out) >= n_options:
            break
        esp = round(max(espiras_base + off, 1.0), 1)
        esp, _, _ = apply_fem_physics_guard(
            esp,
            diametro_mm=diametro_mm,
            pacote_mm=pacote_mm,
            polos=polos,
            ranhuras=ranhuras,
            carcaca=carcaca,
            tensao_fase_v=voltage_v,
        )
        awg = select_awg_for_slot_fill(esp, slot_lim, prefer_awg=float(pref))
        audit = audit_winding_physics(
            espiras=esp,
            awg=awg,
            diametro_mm=diametro_mm,
            pacote_mm=pacote_mm,
            ranhuras=ranhuras,
            polos=polos,
            carcaca=carcaca,
            voltage_v=voltage_v,
        )
        par = 2 if awg >= 22 and pref == 22 else 1
        if par == 2 and awg >= 20:
            awg_equiv = max(17, awg - 3)
            audit2 = audit_winding_physics(
                espiras=esp,
                awg=awg_equiv,
                diametro_mm=diametro_mm,
                pacote_mm=pacote_mm,
                ranhuras=ranhuras,
                polos=polos,
                carcaca=carcaca,
                parallel_count=2,
                voltage_v=voltage_v,
            )
            if audit2.confidence_score >= audit.confidence_score:
                audit = audit2
                awg = awg_equiv
        fio_lbl = f"{par}x {int(awg)} AWG" if par > 1 else f"1x {int(awg)} AWG"
        out.append(
            WindingCandidate(
                opcao=chr(65 + i),
                espiras_por_bobina=audit.espiras,
                fio_awg=int(awg),
                paralelo=par,
                densidade_j=audit.current_density_j,
                ocupacao_ff=audit.fill_factor_ff,
                confianca_pct=audit.confidence_score,
                alertas=audit.alerts,
                descricao=fio_lbl,
            )
        )
    out.sort(key=lambda c: c.confianca_pct, reverse=True)
    return out[:n_options]


def run_caixa_preta(
    entrada: dict[str, Any],
    *,
    images: Optional[list[ImageSource]] = None,
    use_vision: bool = True,
    n_candidatos: int = 5,
) -> DigitalTwinResult:
    modo = MODO_CAIXA_PRETA
    visao: dict[str, Any] = {}
    ent = dict(entrada)
    if not ent.get("tensao_v") and not ent.get("voltagem"):
        ent["tensao_v"] = 220.0
    ok, missing = check_required_inputs(ent, modo=modo)

    if use_vision and images:
        visao = extract_stator_geometry_from_images(images, ent)
        ent = merge_vision_into_entrada(ent, visao)
        if ent.get("checklist_visao"):
            missing = list(dict.fromkeys(missing + list(ent["checklist_visao"])))
        if not is_vision_reliable(visao) and MSG_VISAO_ILEGIVEL not in missing:
            missing.append(MSG_VISAO_ILEGIVEL)

    ok2, missing2 = check_required_inputs(ent, modo=modo)
    missing = list(dict.fromkeys(missing + missing2))
    ok = ok and ok2

    if not ok:
        from services.executive_report import build_executive_markdown

        return DigitalTwinResult(
            modo=modo,
            entrada=ent,
            completo=False,
            checklist_faltante=missing,
            visao=visao,
            bloqueado=True,
            mensagem_bloqueio="Dados insuficientes para cálculo físico.",
            relatorio_markdown=build_executive_markdown(
                modo=modo,
                entrada=ent,
                candidatos=[],
                checklist=missing,
                bloqueado=True,
            ),
            mermaid_validacao=_mermaid_validacao_flow(),
            mermaid_ligacao=_ligacao_mermaid(ent.get("ligacao", "")),
        )

    d = float(ent["diametro_mm"])
    p = float(ent["pacote_mm"])
    ran = int(ent["ranhuras"])
    pol = ent.get("polos")
    pol_i = int(pol) if pol else 2
    car = str(ent.get("carcaca") or "")
    v = float(ent.get("tensao_v") or ent.get("voltagem") or 220.0)

    esp_fem = espiras_from_fem_equation(d, p, pol_i)
    esp_weg = espiras_weg_fem(voltage_v=v, diametro_mm=d, pacote_mm=p, polos=pol_i)
    esp_base = round((esp_fem + esp_weg) / 2.0, 1)

    candidatos = _genetic_candidates(
        espiras_base=esp_base,
        diametro_mm=d,
        pacote_mm=p,
        ranhuras=ran,
        polos=pol_i,
        carcaca=car,
        voltage_v=v,
        n_options=n_candidatos,
    )

    from services.executive_report import build_executive_markdown

    md = build_executive_markdown(
        modo=modo,
        entrada=ent,
        candidatos=candidatos,
        visao=visao,
        fem_refs={"fem_4_44": esp_fem, "weg_phi": esp_weg, "b_max_t": B_MAX_TESLA},
    )
    return DigitalTwinResult(
        modo=modo,
        entrada=ent,
        completo=True,
        candidatos=candidatos,
        visao=visao,
        relatorio_markdown=md,
        mermaid_validacao=_mermaid_validacao_flow(),
        mermaid_ligacao=_ligacao_mermaid(ent.get("ligacao", "")),
    )


def run_auditoria(
    entrada: dict[str, Any],
    *,
    use_gemini: bool = True,
) -> DigitalTwinResult:
    modo = MODO_AUDITORIA
    ent = dict(entrada)
    if not ent.get("tensao_v") and not ent.get("voltagem"):
        ent["tensao_v"] = 220.0
    ok, missing = check_required_inputs(ent, modo=modo)

    if not ok:
        from services.executive_report import build_executive_markdown

        return DigitalTwinResult(
            modo=modo,
            entrada=ent,
            completo=False,
            checklist_faltante=missing,
            bloqueado=True,
            mensagem_bloqueio="Auditoria bloqueada — preencha espiras, fio e geometria.",
            relatorio_markdown=build_executive_markdown(
                modo=modo, entrada=ent, candidatos=[], checklist=missing, bloqueado=True
            ),
            mermaid_validacao=_mermaid_validacao_flow(),
            mermaid_ligacao=_ligacao_mermaid(ent.get("ligacao", "")),
        )

    d = float(ent["diametro_mm"])
    p = float(ent["pacote_mm"])
    ran = int(ent["ranhuras"])
    pol = ent.get("polos")
    pol_i = int(pol) if pol else None
    car = str(ent.get("carcaca") or "")
    v = float(ent.get("tensao_v") or ent.get("voltagem") or 220.0)
    esp = float(ent.get("espiras_engenheiro") or ent.get("espiras") or 0)
    awg_raw = ent.get("fio_engenheiro") or ent.get("fio_awg") or 19
    try:
        awg = int(float(str(awg_raw).replace(",", ".")))
    except ValueError:
        awg = 19

    from engine.physics_audit import infer_wire_from_fio

    tipo_bob = str(ent.get("tipo_bobinagem") or "")
    passo_ent = str(ent.get("passo") or "")
    par_count, awg_wire = infer_wire_from_fio(awg_raw, tipo_bobinagem=tipo_bob)
    if par_count > 1:
        awg = int(round(awg_wire))

    corrente_user = ent.get("corrente_nominal_a")
    try:
        corrente_f = float(corrente_user) if corrente_user not in (None, "") else None
    except (TypeError, ValueError):
        corrente_f = None
    pot_cv = ent.get("potencia_cv")
    try:
        pot_cv_f = float(pot_cv) if pot_cv not in (None, "") else None
    except (TypeError, ValueError):
        pot_cv_f = None

    audit_user = audit_auditoria_user_winding(
        espiras=esp,
        awg=awg,
        diametro_mm=d,
        pacote_mm=p,
        ranhuras=ran,
        polos=pol_i,
        carcaca=car,
        parallel_count=par_count,
        voltage_v=v,
        corrente_nominal_a=corrente_f,
        potencia_cv=pot_cv_f,
        tipo_bobinagem=tipo_bob,
        passo=passo_ent,
    )
    abort = bool(audit_user.calculation_aborted)

    candidatos: list[WindingCandidate] = [
        WindingCandidate(
            opcao="SUSPEITO",
            espiras_por_bobina=esp,
            fio_awg=awg,
            paralelo=par_count,
            densidade_j=audit_user.current_density_j,
            ocupacao_ff=audit_user.fill_factor_ff,
            confianca_pct=0 if abort else audit_user.confidence_score,
            alertas=list(audit_user.alerts),
            descricao="Cálculo informado pelo usuário",
        ),
    ]

    audit_corr = None
    if not abort:
        slot_lim = estimate_physical_slot_fill_limit(ran, d, p)
        awg_corr = select_awg_for_slot_fill(
            audit_user.espiras, slot_lim, prefer_awg=float(awg)
        )
        audit_corr = audit_winding_physics(
            espiras=audit_user.espiras,
            awg=awg_corr,
            diametro_mm=d,
            pacote_mm=p,
            ranhuras=ran,
            polos=pol_i,
            carcaca=car,
            parallel_count=par_count,
            voltage_v=v,
            corrente_nominal_a=corrente_f,
            potencia_cv=pot_cv_f,
            tipo_bobinagem=tipo_bob,
            passo=passo_ent,
        )
        candidatos.append(
            WindingCandidate(
                opcao="CORRIGIDO",
                espiras_por_bobina=audit_corr.espiras,
                fio_awg=int(awg_corr),
                paralelo=par_count,
                densidade_j=audit_corr.current_density_j,
                ocupacao_ff=audit_corr.fill_factor_ff,
                confianca_pct=audit_corr.confidence_score,
                alertas=audit_corr.alerts + audit_corr.corrections,
                descricao=f"Proposta física 1x {awg_corr} AWG",
            )
        )

    gemini_aud: dict[str, Any] = {}
    if abort:
        gemini_aud = {
            "status_auditoria": "REPROVADO",
            "nota_confianca_0_100": 0,
            "comentario": MSG_B_ABORT,
            "alerta_risco": f"B estimado ≈ {audit_user.flux_density_b_t} T (limite {B_ABORT_TESLA} T).",
        }
    elif use_gemini:
        try:
            from services.gemini_engineering_validator import validate_audit_with_gemini

            gemini_aud = validate_audit_with_gemini(
                {
                    "entrada": ent,
                    "auditoria_usuario": asdict(audit_user),
                    "auditoria_corrigida": asdict(audit_corr) if audit_corr else {},
                    "limites": {
                        "b_tesla": B_MAX_TESLA,
                        "b_abort_tesla": B_ABORT_TESLA,
                        "j_a_mm2": "3-7",
                        "ff": "0.25-0.45",
                    },
                }
            )
        except Exception as exc:
            gemini_aud = {"erro": str(exc)}

    from services.executive_report import build_executive_markdown

    fem_refs = {
        "referencia_fem": audit_user.fem_reference_turns,
        "b_operacional_t": audit_user.flux_density_b_t,
        "b_abort_t": B_ABORT_TESLA,
    }
    if abort:
        fem_refs["status"] = MSG_B_ABORT
    md = build_executive_markdown(
        modo=modo,
        entrada=ent,
        candidatos=candidatos,
        gemini=gemini_aud,
        fem_refs=fem_refs,
    )
    return DigitalTwinResult(
        modo=modo,
        entrada=ent,
        completo=True,
        candidatos=candidatos,
        gemini_auditoria=gemini_aud,
        relatorio_markdown=md,
        mermaid_validacao=_mermaid_validacao_flow(),
        mermaid_ligacao=_ligacao_mermaid(ent.get("ligacao", "")),
        saturacao_abortada=abort,
        flux_density_b_t=audit_user.flux_density_b_t,
    )


def twin_result_to_optimizer_payload(twin: DigitalTwinResult) -> dict[str, Any]:
    """Serialização para session_state / relatório HTML."""
    return {
        "modo": twin.modo,
        "entrada": twin.entrada,
        "completo": twin.completo,
        "bloqueado": twin.bloqueado,
        "checklist": twin.checklist_faltante,
        "candidatos": [asdict(c) for c in twin.candidatos],
        "visao": twin.visao,
        "gemini": twin.gemini_auditoria,
        "relatorio_markdown": twin.relatorio_markdown,
        "mermaid_validacao": twin.mermaid_validacao,
        "mermaid_ligacao": twin.mermaid_ligacao,
        "saturacao_abortada": twin.saturacao_abortada,
        "flux_density_b_t": twin.flux_density_b_t,
    }
