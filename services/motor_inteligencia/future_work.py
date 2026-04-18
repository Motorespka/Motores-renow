"""
Sugestões de cálculos e análises futuras a partir do estado atual dos dados.

Tudo aqui é **roadmap técnico** descritivo — não executa modelos ainda inexistentes.
"""

from __future__ import annotations

from typing import Any, Dict, List


def suggest_future_calculations(
    normalized: Dict[str, Any],
    derived: Dict[str, Any],
    validation: Dict[str, Any],
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []

    def add(
        *,
        id: str,
        titulo: str,
        disponivel: bool,
        falta: List[str],
        notas: str,
    ) -> None:
        out.append(
            {
                "id": id,
                "titulo": titulo,
                "disponivel_agora": disponivel,
                "campos_faltantes": falta,
                "notas": notas,
            }
        )

    falta_fp = normalized.get("power_factor") is None
    falta_eta = normalized.get("efficiency") is None
    falta_fases = (normalized.get("phases") or "") == "unknown"

    add(
        id="pin_pout_torque_refino",
        titulo="Refino Pin/Pout/torque com esquema Y/D e leitura de tensão de trabalho",
        disponivel=not (falta_fp or falta_eta or falta_fases),
        falta=[x for x, y in [("fator_potencia", falta_fp), ("rendimento", falta_eta), ("fases", falta_fases)] if y],
        notas="Desbloqueia comparação elétrica mais forte com a placa quando fp, rendimento e mono/tri forem confiáveis.",
    )

    add(
        id="rebobinagem_profunda",
        titulo="Validação de rebobinagem (passos, espiras, ranhuras, pacote)",
        disponivel=bool(normalized.get("ranhuras")),
        falta=["ranhuras", "pacote_mm", "passos/espiras estruturados"]
        if not normalized.get("ranhuras")
        else ["modelo de máquina dedicado"],
        notas="Base preparada em ``bobinagem_*`` e ``esquema``; requer motor de regras por classe sem hardcode de marca.",
    )

    add(
        id="corrente_esperada_faixa",
        titulo="Estimativa de corrente esperada por faixa de carga",
        disponivel=bool(derived.get("pout_kw", {}).get("value")),
        falta=["Pout confiável", "curva típica ou dados de ensaio"] if not derived.get("pout_kw", {}).get("value") else ["tabela de carga"],
        notas="Heurística futura; não substitui ensaio em bancada.",
    )

    add(
        id="assinatura_tecnica",
        titulo="Assinatura técnica normalizada + similaridade entre cadastros",
        disponivel=bool(normalized.get("power_kw") and normalized.get("rpm_nominal")),
        falta=[] if normalized.get("power_kw") else ["potência confiável"],
        notas="Comparar com motores já cadastrados (memória de oficina) — integração planejada com serviços existentes.",
    )

    add(
        id="capacitor_auxiliar",
        titulo="Modelo monofásico com ramo auxiliar e capacitor",
        disponivel=bool(normalized.get("capacitor")),
        falta=["dados de capacitor"] if not normalized.get("capacitor") else ["modelo equivalente ramificado"],
        notas="Campo capacitor já capturado; cálculo elétrico exige topologia explícita (não inferida agora).",
    )

    add(
        id="inversor_ifd",
        titulo="Análise com alimentação por inversor (harmónicos, derating)",
        disponivel=False,
        falta=["frequência variável", "modo de controlo", "PWM/carrier"],
        notas="Reservado para extensão; não aplicar regras de rede fixa 50/60 Hz a esse regime.",
    )

    add(
        id="ocr_conflito_placa",
        titulo="Conferência placa vs. texto OCR / manuscrito",
        disponivel=bool(normalized.get("texto_ocr_len")),
        falta=["texto_ocr"] if not normalized.get("texto_ocr_len") else [],
        notas="Quando houver divergência entre campos estruturados e OCR, marcar revisão humana (já alinhado a parser_tecnico).",
    )

    if validation.get("needs_human_review"):
        out.append(
            {
                "id": "revisao_humana",
                "titulo": "Revisão humana recomendada",
                "disponivel_agora": True,
                "campos_faltantes": [],
                "notas": "Conflitos fracos ou metadados OCR pedem confirmação antes de decisões de oficina.",
            }
        )

    return out
