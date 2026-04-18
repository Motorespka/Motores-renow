"""
Roadmap de análises de rebobinagem e similaridade (sem execução de I/O).
"""

from __future__ import annotations

from typing import Any, Dict, List


def suggest_rewinding_future_work(
    rewinding_normalized: Dict[str, Any],
    validation: Dict[str, Any],
    signature: Dict[str, Any],
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []

    def add(**kw: Any) -> None:
        out.append(kw)

    add(
        id="similaridade_cadastro",
        titulo="Comparar com motores já cadastrados (assinatura + tolerâncias)",
        disponivel_agora=False,
        notas="Usar ``prepare_similarity_query`` + consulta indexada quando existir API de busca.",
    )
    add(
        id="tabela_awg_mm2",
        titulo="Validação fio × corrente com tabela AWG/mm² por classe de isolamento",
        disponivel_agora=False,
        notas="Evita chute de seção; requer tabela técnica versionada, não heurística solta.",
    )
    add(
        id="bobina_por_ranhura",
        titulo="Modelo ranhuras × passo × camadas (desenho de máquina)",
        disponivel_agora=bool((rewinding_normalized.get("esquema") or {}).get("ranhuras", {}).get("value")),
        notas="Campos ``camadas`` / ``distribuicao_bobinas`` no esquema desbloqueiam análises mais fortes.",
    )
    if validation.get("needs_human_review"):
        add(
            id="revisao_humana_oficina",
            titulo="Revisão humana do cálculo manuscrito / OCR",
            disponivel_agora=True,
            notas="Conflitos fracos ou OCR duvidoso — conferência de oficina antes de decisão.",
        )
    if not (signature.get("signature_string") or "").strip():
        add(
            id="preencher_assinatura",
            titulo="Completar passo/espiras/fio para gerar assinatura comparável",
            disponivel_agora=False,
            notas="Assinatura vazia impede clusterização técnica útil.",
        )
    return out
