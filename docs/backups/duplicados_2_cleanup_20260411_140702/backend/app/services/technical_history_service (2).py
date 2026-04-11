from __future__ import annotations

from typing import Any, Dict, List


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


class TechnicalHistoryService:
    def _tipo_penalty(self, tipo_atual: Any, tipo_candidato: Any) -> float:
        atual = _to_text(tipo_atual).lower()
        candidato = _to_text(tipo_candidato).lower()
        if not atual or not candidato:
            return 0.0
        if atual == candidato:
            return 0.0
        return 0.25

    def build_suggestion(self, *, parser_tecnico: Dict[str, Any], candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        sample_size = len(candidates or [])
        if sample_size < 5:
            return {
                "ativo": False,
                "motivo": "amostra_insuficiente",
                "confianca": "n/a",
                "amostra": sample_size,
                "sugestao": {},
            }

        # TODO: no futuro considerar exigir espiras + passo para peso maximo.
        has_main = bool(
            (parser_tecnico or {}).get("espiras_normalizado")
            or (parser_tecnico or {}).get("passo_normalizado")
        )
        if not has_main:
            return {
                "ativo": False,
                "motivo": "sem_base_principal",
                "confianca": "n/a",
                "amostra": sample_size,
                "sugestao": {},
            }

        confidence = "baixa" if 5 <= sample_size <= 10 else "normal"
        if not candidates:
            return {
                "ativo": False,
                "motivo": "sem_candidatos",
                "confianca": confidence,
                "amostra": sample_size,
                "sugestao": {},
            }

        tipo_atual = (parser_tecnico or {}).get("ligacao_tipo_eletrico")
        ranked: List[Dict[str, Any]] = []
        for row in candidates:
            if not isinstance(row, dict):
                continue
            tipo_candidato = row.get("ligacao_tipo_eletrico") or row.get("tipo_motor")
            base_score = float(row.get("score") or 1.0)
            score = max(0.0, base_score - self._tipo_penalty(tipo_atual, tipo_candidato))
            ranked.append({"score": score, "row": row})

        if not ranked:
            return {
                "ativo": False,
                "motivo": "sem_candidatos_validos",
                "confianca": confidence,
                "amostra": sample_size,
                "sugestao": {},
            }

        ranked.sort(key=lambda item: float(item.get("score") or 0.0), reverse=True)
        best = ranked[0].get("row") if isinstance(ranked[0], dict) else {}

        return {
            "ativo": True,
            "motivo": "base_historica",
            "confianca": confidence,
            "amostra": sample_size,
            "sugestao": best if isinstance(best, dict) else {},
        }

