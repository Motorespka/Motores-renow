from __future__ import annotations

import csv
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import streamlit as st
from supabase import create_client

from services.descoberta_automatica import executar_descoberta_automatica

logger = logging.getLogger(__name__)


def _salvar_export_descobertas(resumo: Dict[str, Any], pasta_saida: str = "exports") -> Dict[str, str]:
    out_dir = Path(pasta_saida)
    out_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    json_path = out_dir / f"descobertas_ia_{now}.json"
    csv_path = out_dir / f"descobertas_ia_{now}.csv"

    payload = []
    for item in resumo.get("descobertas", []):
        payload.append({
            "padrao": item.get("padrao"),
            "calculo_inferido": item.get("calculo_inferido"),
            "nivel_confianca": item.get("nivel_confianca"),
            "amostras": item.get("amostras"),
            "gerado_em": datetime.now(timezone.utc).isoformat(),
        })

    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["padrao", "calculo_inferido", "nivel_confianca", "amostras", "gerado_em"])
        writer.writeheader()
        writer.writerows(payload)

    return {"json": str(json_path), "csv": str(csv_path)}


def _init_supabase() -> Any:
    url = st.secrets.get("SUPABASE_URL")
    key = st.secrets.get("SUPABASE_KEY")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL/SUPABASE_KEY não configurados em st.secrets")
    return create_client(url, key)


def executar_runner_descoberta() -> Dict[str, Any]:
    """
    Runner manual e seguro para atualização da inteligência técnica.

    Fluxo:
      1) conecta ao Supabase
      2) executa descoberta automática
      3) registra logs das descobertas encontradas

    Este runner não é executado automaticamente na inicialização do site.
    """
    try:
        supabase = _init_supabase()
        resumo = executar_descoberta_automatica(supabase)

        total = resumo.get("total_descobertas", 0)
        persistidas = resumo.get("total_persistidas", 0)
        logger.info("[descoberta_runner] total_descobertas=%s | total_persistidas=%s", total, persistidas)

        if resumo.get("tabela_descobertas_ausente"):
            logger.warning("[descoberta_runner] tabela public.descobertas_ia ausente; descobertas não persistidas")

        for item in resumo.get("descobertas", []):
            logger.info(
                "[descoberta_runner] padrao=%s | confianca=%s | amostras=%s | calculo=%s",
                item.get("padrao"),
                item.get("nivel_confianca"),
                item.get("amostras"),
                item.get("calculo_inferido"),
            )

        arquivos = _salvar_export_descobertas(resumo)
        logger.info("[descoberta_runner] export salvo: json=%s csv=%s", arquivos.get("json"), arquivos.get("csv"))

        return {"ok": True, "resumo": resumo, "arquivos_exportados": arquivos}
    except Exception as exc:
        logger.exception("[descoberta_runner] erro ao executar descoberta automática")
        return {"ok": False, "erro": str(exc)}
