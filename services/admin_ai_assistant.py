from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

try:
    import google.generativeai as genai
except Exception:  # pragma: no cover - dependencia opcional em runtime
    genai = None


ROOT_DIR = Path(__file__).resolve().parents[1]
AI_BOARD_DIR = ROOT_DIR / "ai_board"
BRANDS_DIR = AI_BOARD_DIR / "brands"
PACKS_DIR = AI_BOARD_DIR / "packs"
PROMPTS_DIR = AI_BOARD_DIR / "prompts"
AUDIT_LOG_PATH = ROOT_DIR / "updates" / "admin_ai_audit.log"

PROMPT_BASE_FILE = PROMPTS_DIR / "admin_internal_assistant.md"


@dataclass(frozen=True)
class RoutedContext:
    brands: List[str]
    intents: List[str]
    product_types: List[str]
    selected_packs: List[str]


BRAND_ALIASES: Dict[str, List[str]] = {
    "weg": ["weg"],
    "siemens": ["siemens"],
    "abb": ["abb"],
    "nidec": ["nidec"],
    "bonfiglioli": ["bonfiglioli"],
    "nova_motores": ["nova motores", "nova motor", "nova"],
    "hercules_motores": ["hercules motores", "hércules motores", "hercules"],
    "mercosul_motores": ["mercosul motores", "mercosul"],
    "eberle": ["eberle"],
    "voges": ["voges"],
    "cestari": ["cestari"],
    "nord": ["nord", "nord drivesystems", "nord drivesystems"],
    "sew": ["sew", "sew eurodrive", "sew-eurodrive", "sew euro-drive"],
    "schneider": ["schneider", "schneider electric"],
    "danfoss": ["danfoss"],
    "bosch_rexroth": ["bosch rexroth", "rexroth"],
    "ge": ["ge", "general electric"],
    "wolong": ["wolong"],
    "toshiba": ["toshiba"],
    "mitsubishi_electric": ["mitsubishi", "mitsubishi electric"],
}

INTENT_RULES: Dict[str, List[str]] = {
    "tecnica": ["coerente", "incoer", "rpm", "polos", "tensao", "corrente", "placa", "dados"],
    "manutencao": ["oficina", "bancada", "manuten", "diagnost", "rebobin", "rolamento", "ligacao"],
    "cadastro": ["cadastro", "campos", "filtro", "consulta", "pagina", "aba"],
    "comparacao": ["compar", "vs", "ou", "diferen", "melhor"],
    "inconsistencia": ["estranha", "estranho", "erro", "inconsist", "contradit"],
    "melhoria_admin": ["admin", "site", "tela", "fluxo", "bug", "melhoria", "ideia", "profissional"],
}

PRODUCT_RULES: Dict[str, List[str]] = {
    "motor": ["motor", "trifas", "monofas", "motofreio"],
    "motoredutor": ["motoredutor", "motorredutor", "gear motor", "gearmotor"],
    "redutor": ["redutor", "reducao", "redução"],
    "acionamento": ["inversor", "acionamento", "automacao", "automação", "drive"],
}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _candidate_keys() -> List[str]:
    primary = (os.environ.get("GEMINI_API_KEY") or "").strip()
    fallback = (os.environ.get("GEMINI_API_KEY_FALLBACK") or "").strip()

    try:
        import streamlit as st

        if not primary:
            primary = str(st.secrets.get("GEMINI_API_KEY", "") or "").strip()
        if not fallback:
            fallback = str(st.secrets.get("GEMINI_API_KEY_FALLBACK", "") or "").strip()
    except Exception:
        pass

    out: List[str] = []
    if primary:
        out.append(primary)
    if fallback and fallback != primary:
        out.append(fallback)
    return out[:2]


def route_question_context(question: str) -> RoutedContext:
    text = _normalize(question)

    brands: List[str] = []
    for brand_key, aliases in BRAND_ALIASES.items():
        if any(re.search(rf"\b{re.escape(alias)}\b", text) for alias in aliases):
            brands.append(brand_key)

    intents: List[str] = [
        intent
        for intent, markers in INTENT_RULES.items()
        if any(marker in text for marker in markers)
    ]
    if not intents:
        intents = ["tecnica"]

    product_types: List[str] = [
        product
        for product, markers in PRODUCT_RULES.items()
        if any(marker in text for marker in markers)
    ]
    if not product_types:
        product_types = ["motor"]

    packs = _select_packs(brands, intents, product_types)
    return RoutedContext(brands=brands, intents=intents, product_types=product_types, selected_packs=packs)


def _select_packs(brands: List[str], intents: List[str], product_types: List[str]) -> List[str]:
    selected: List[str] = []

    for brand_key in brands:
        selected.append(f"brands/{brand_key}.md")

    selected.append("packs/generic_motor_rules.md")
    selected.append("packs/nameplate_reading_rules.md")
    selected.append("packs/data_consistency_rules.md")

    if any(p in {"motoredutor", "redutor", "acionamento"} for p in product_types):
        selected.append("packs/generic_gearmotor_rules.md")
    if any(i in {"manutencao", "inconsistencia"} for i in intents):
        selected.append("packs/rewinding_and_workshop_rules.md")
    if any(i in {"melhoria_admin", "cadastro"} for i in intents):
        selected.append("packs/admin_product_ideas.md")
    if not brands:
        selected.append("packs/legacy_or_unknown_brands.md")

    dedup: List[str] = []
    for item in selected:
        if item not in dedup:
            dedup.append(item)
    return dedup


def _load_pack(relative_path: str) -> str:
    target = AI_BOARD_DIR / relative_path
    if not target.exists():
        return ""
    try:
        return target.read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def _build_prompt(question: str, routed: RoutedContext, history: List[Dict[str, str]] | None = None) -> str:
    base_prompt = ""
    if PROMPT_BASE_FILE.exists():
        base_prompt = PROMPT_BASE_FILE.read_text(encoding="utf-8")

    pack_blobs: List[str] = []
    for rel in routed.selected_packs:
        content = _load_pack(rel)
        if content:
            pack_blobs.append(f"## PACK: {rel}\n{content}")

    history_blob = ""
    if history:
        turns = history[-8:]
        lines = [f"- {row.get('role', 'user')}: {row.get('content', '')}" for row in turns]
        history_blob = "\n".join(lines)

    return (
        f"{base_prompt}\n\n"
        f"### CONTEXTO ROTEADO\n"
        f"Marcas detectadas: {', '.join(routed.brands) or 'nenhuma'}\n"
        f"Intencoes detectadas: {', '.join(routed.intents) or 'tecnica'}\n"
        f"Tipos de produto detectados: {', '.join(routed.product_types) or 'motor'}\n\n"
        f"### HISTORICO (RESUMIDO)\n{history_blob or '- sem historico'}\n\n"
        f"### PACKS ATIVOS\n" + "\n\n".join(pack_blobs) + "\n\n"
        f"### PERGUNTA DO USUARIO\n{question.strip()}\n"
    )


def _call_llm(prompt: str) -> tuple[str, str, bool]:
    if genai is None:
        raise RuntimeError("Dependencia google.generativeai indisponivel.")

    keys = _candidate_keys()
    if not keys:
        raise RuntimeError("Nenhuma chave Gemini configurada (GEMINI_API_KEY).")

    model_name = (os.environ.get("GEMINI_MODEL") or "gemini-2.5-flash").strip()
    errors: List[str] = []

    for idx, key in enumerate(keys):
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel(model_name)
            result = model.generate_content(prompt)
            text = (getattr(result, "text", "") or "").strip()
            if text:
                return text, model_name, idx > 0
            errors.append(f"resposta_vazia_key_{idx+1}")
        except Exception as exc:
            errors.append(str(exc))

    raise RuntimeError(" | ".join(errors) or "Falha ao gerar resposta com Gemini.")


def _fallback_answer(question: str, routed: RoutedContext) -> str:
    brands = ", ".join(routed.brands) or "sem marca explicita"
    intents = ", ".join(routed.intents) or "tecnica"
    products = ", ".join(routed.product_types) or "motor"
    checks = [
        "Confirmar potencia, tensao, corrente, rpm, polos e frequencia no cadastro.",
        "Separar no laudo: fato observado, padrao provavel, hipotese e verificacao recomendada.",
        "Registrar inconsistencias de placa/ligacao antes de aprovar o cadastro.",
    ]
    checks_blob = "\n".join([f"- {item}" for item in checks])
    return (
        "**entendimento da pergunta**\n"
        f"Pergunta analisada em modo local (sem LLM): {question.strip()}\n\n"
        "**marca/domínio detectado**\n"
        f"{brands}\n\n"
        "**tipo de problema**\n"
        f"{intents} | {products}\n\n"
        "**leitura técnica**\n"
        "Sem inferir dado oficial fechado. Avaliacao conservadora aplicada.\n\n"
        "**o que conferir**\n"
        f"{checks_blob}\n\n"
        "**sugestao pratica**\n"
        "Use os campos obrigatorios e valide placa com foto legivel antes de fechar diagnostico/cadastro."
    )


def _write_audit_log(question: str, routed: RoutedContext, model: str, used_fallback_key: bool, status: str) -> None:
    try:
        AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "event": "admin_ai_assistant_query",
            "status": status,
            "model": model,
            "used_fallback_key": bool(used_fallback_key),
            "brands": routed.brands,
            "intents": routed.intents,
            "product_types": routed.product_types,
            "question_hash": hashlib.sha256((question or "").encode("utf-8")).hexdigest(),
            "question_preview": (question or "").strip()[:120],
        }
        with AUDIT_LOG_PATH.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        return


def ask_admin_internal_assistant(
    question: str,
    history: List[Dict[str, str]] | None = None,
) -> Dict[str, Any]:
    text = (question or "").strip()
    if not text:
        return {
            "ok": False,
            "error": "Pergunta vazia.",
            "response": "",
            "routed": {
                "brands": [],
                "intents": [],
                "product_types": [],
                "selected_packs": [],
            },
        }

    routed = route_question_context(text)
    prompt = _build_prompt(text, routed, history=history)

    model = "local-fallback"
    used_fallback_key = False
    status = "ok"

    try:
        answer, model, used_fallback_key = _call_llm(prompt)
    except Exception as exc:
        answer = _fallback_answer(text, routed)
        status = f"fallback:{str(exc)[:180]}"

    _write_audit_log(text, routed, model=model, used_fallback_key=used_fallback_key, status=status)

    return {
        "ok": True,
        "error": "",
        "response": answer,
        "model": model,
        "used_fallback_key": used_fallback_key,
        "routed": {
            "brands": routed.brands,
            "intents": routed.intents,
            "product_types": routed.product_types,
            "selected_packs": routed.selected_packs,
        },
    }
