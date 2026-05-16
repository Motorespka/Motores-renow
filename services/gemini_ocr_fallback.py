from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from services.gemini_key_manager import GeminiKeyManager, mask_key


def _t(v: Any) -> str:
    if v is None:
        return ""
    return str(v).strip()


def _extract_json(text: str) -> Dict[str, Any]:
    t = (text or "").strip()
    if not t:
        raise ValueError("Resposta vazia do Gemini.")
    # aceita ruído antes/depois, mas extrai o primeiro bloco JSON válido
    m = re.search(r"\{[\s\S]*\}\s*$", t)
    if not m:
        m = re.search(r"\{[\s\S]*\}", t)
    if not m:
        raise ValueError("Não foi possível localizar JSON na resposta do Gemini.")
    return json.loads(m.group(0))


def _prompt_rebobinagem_json() -> str:
    return (
        "Você é especialista em rebobinagem de motores.\n"
        "Analise a imagem técnica (ficha/tabela/folha) e extraia apenas dados VISÍVEIS.\n"
        "NÃO invente valores e NÃO complete por conhecimento geral.\n"
        "Se não enxergar, deixe string vazia.\n\n"
        "Responda SOMENTE com JSON válido, sem markdown, sem texto antes/depois, neste formato:\n"
        "{\n"
        '  "tipo_motor": "",\n'
        '  "potencia_cv": "",\n'
        '  "rpm": "",\n'
        '  "tensao": "",\n'
        '  "polos": "",\n'
        '  "frequencia": "",\n'
        '  "carcaca": "",\n'
        '  "ranhuras": "",\n'
        '  "pacote_mm": "",\n'
        '  "diametro_mm": "",\n'
        '  "capacitor": "",\n'
        '  "principal": {\n'
        '    "fio": "",\n'
        '    "espiras": "",\n'
        '    "passo": "",\n'
        '    "camada": "",\n'
        '    "ligacao": "",\n'
        '    "bobinas_por_grupo": "",\n'
        '    "grupos_por_fase": ""\n'
        "  },\n"
        '  "auxiliar": {\n'
        '    "fio": "",\n'
        '    "espiras": "",\n'
        '    "passo": "",\n'
        '    "camada": "",\n'
        '    "ligacao": "",\n'
        '    "bobinas_por_grupo": "",\n'
        '    "grupos_por_fase": ""\n'
        "  },\n"
        '  "observacoes": "",\n'
        '  "confianca": 0,\n'
        '  "campos_incertos": [],\n'
        '  "nao_encontrado": [],\n'
        '  "evidencias_textuais": []\n'
        "}\n\n"
        "Regras de extração:\n"
        "- Preserve padrões como 1:4:6, 1:6:8:10:12, 38:58:71, 2X24, 1 X 23, 127/220.\n"
        "- Diferencie principal/efetivo de auxiliar.\n"
        "- Diferencie monofásico de trifásico.\n"
        "- Em folha Hercules, 'Efetivo' geralmente equivale ao enrolamento principal.\n"
        "- Não transforme 1/2 CV em 12 CV; não transforme 1/4 CV em 14 CV.\n"
        "- Se aparecer CAP. PARTIDA / CAP. PERMANENTE / PART/PERM, preserve em tipo_motor/observacoes.\n"
    )


DETECTIVE_MODE_PROMPT_SUFFIX = (
    "\n\n"
    "--- MODO DETETIVE (AUDITORIA ADMIN — lote difícil) ---\n"
    "Este documento pode ter baixa qualidade de imagem, ser esquema parcial ou misturar vários equipamentos.\n"
    "- Extraia TUDO que conseguir ler com segurança razoável sobre o MOTOR / enrolamento rebobinagem.\n"
    "- Ignore preocupações cosméticas de 'baixa confiança OCR' aqui — ainda assim NÃO invente números: "
    "se não estiver visível, deixe string vazia ou liste em nao_encontrado.\n"
    "- Para qualquer campo em que aceite uma leitura mas haja ambiguidade, preencha o valor mais provável "
    "QUE ESTEJA na imagem e inclua esse campo também em campos_incertos com uma breve razão PT-BR.\n"
    "- Use evidencias_textuais com trechos OCR curtos dos rótulos que justificam leituras difíceis.\n"
    "- No campo observacoes, indique explicitamente duvidas remanescentes e o que recomenda revisão manual.\n"
    "- confianca: use 0.0–1.0 refletindo clareza VISUAL do documento, não penalize apenas por incompletude;\n"
    "documentos válidos mas parciais podem ter confianca média desde que os valores copiados estejam na chapa.\n"
)


def _image_part(image_bytes: bytes, mime_type: str) -> Dict[str, Any]:
    return {"mime_type": mime_type, "data": image_bytes}


def _guess_mime_from_path(path: str) -> str:
    ext = Path(path).suffix.lower()
    if ext in {".jpg", ".jpeg", ".jfif"}:
        return "image/jpeg"
    if ext in {".png"}:
        return "image/png"
    # PDF não é suportado como "image/*" — pipeline deve renderizar página para imagem antes.
    return "image/jpeg"


@dataclass
class GeminiCallResult:
    ok: bool
    data: Dict[str, Any]
    key_alias: str = ""
    masked_key: str = ""
    model: str = ""
    error_status: str = ""
    error_message: str = ""


class GeminiOcrFallback:
    def __init__(
        self,
        *,
        key_manager: GeminiKeyManager,
        model_default: str,
        model_fallback: str = "",
        enabled: bool = True,
        max_attempts_per_image: int = 3,  # FASE 7C: 2 -> 3 (3 retentativas por imagem, spec resiliência)
        require_status_ok: bool = False,
        quota_friendly: bool = False,
        extra_prompt_suffix: str = "",
    ) -> None:
        self.km = key_manager
        self.model_default = (model_default or "gemini-2.5-flash").strip()
        self.model_fallback = (model_fallback or "").strip()
        self.enabled = enabled
        self.max_attempts_per_image = max(1, int(max_attempts_per_image))
        self.require_status_ok = bool(require_status_ok)
        self.quota_friendly = bool(quota_friendly)
        self.extra_prompt_suffix = _t(extra_prompt_suffix)

    def extract_from_image_bytes(
        self,
        *,
        image_bytes: bytes,
        mime_type: str,
        file_hint: str = "",
        sleep_between_attempts_s: float = 0.5,
    ) -> GeminiCallResult:
        if not self.enabled:
            return GeminiCallResult(ok=False, data={}, error_status="disabled", error_message="Gemini disabled")

        try:
            import google.generativeai as genai  # lazy: evita carregar SDK quando só se importa o módulo
        except ImportError as exc:
            return GeminiCallResult(
                ok=False,
                data={},
                error_status="import_error",
                error_message=_t(str(exc))[:160],
            )

        prompt = _prompt_rebobinagem_json()
        if self.extra_prompt_suffix:
            prompt = prompt + "\n\n" + self.extra_prompt_suffix
        models = [self.model_default] + ([self.model_fallback] if self.model_fallback else [])

        # FASE 7C — força saída JSON pura (suportado em gemini-1.5+/2.x flash).
        # Não altera o prompt nem o contrato — apenas reduz risco de markdown/texto extra.
        # temperature=0.0 mantém determinismo entre execuções (estável para auditoria).
        gen_cfg = {
            "response_mime_type": "application/json",
            "temperature": 0.0,
        }

        # FASE 7C — guarda último erro observado para devolver no fim, em vez de mensagem genérica.
        last_err_status = ""
        last_err_msg = ""

        # FASE 7C — rotação round-robin imediata em 429/timeout/quota.
        # cada `attempt` consome 1 chave (via km.get_available_key); com max_attempts=3 a
        # mesma imagem pode trocar de chave até 3x antes de marcar falha definitiva.
        for attempt in range(1, self.max_attempts_per_image + 1):
            key_info = self.km.get_available_key(require_status_ok=self.require_status_ok)
            if not key_info:
                info = self.km.explain_no_keys(require_status_ok=self.require_status_ok)
                reason = (info.get("reason") or "no_keys") if isinstance(info, dict) else "no_keys"
                # codificar motivo no error_status (para o extractor distinguir pausas)
                code = f"no_keys:{reason}"
                return GeminiCallResult(
                    ok=False,
                    data={},
                    error_status=code,
                    error_message=f"Nenhuma chave disponível ({reason})",
                )
            key_alias, key = key_info
            masked = mask_key(key)

            # FASE 7C — flag para sair do laço de modelos e ir buscar outra chave no próximo attempt.
            rotate_next_attempt = False

            for model_name in models:
                try:
                    genai.configure(api_key=key)
                    model = genai.GenerativeModel(model_name)
                    part = _image_part(image_bytes, mime_type)
                    resp = model.generate_content(
                        [prompt, part],
                        generation_config=gen_cfg,  # FASE 7C: força response_mime_type=application/json
                    )
                    text = _t(getattr(resp, "text", ""))
                    data = _extract_json(text)
                    self.km.mark_success(key_alias)
                    self.km.save_status()
                    return GeminiCallResult(ok=True, data=data, key_alias=key_alias, masked_key=masked, model=model_name)
                except Exception as exc:  # noqa: BLE001
                    info = self.km.mark_failure(key_alias, exc)
                    self.km.save_status()
                    status = _t(info.get("status")) or "unknown_error"
                    last_err_status = status
                    last_err_msg = _t(info.get("error_message") or str(exc))[:180]

                    # FASE 7C — classificação explícita de rate-limit/timeout para forçar rotação imediata
                    # de chave. Cobre variações comuns das mensagens do SDK / HTTP do Google.
                    err_low = (str(exc) or "").lower()
                    is_rate_or_timeout = (
                        status == "quota_exhausted"
                        or " 429" in f" {err_low}"
                        or "rate_limit" in err_low
                        or "rate limit" in err_low
                        or "resource_exhausted" in err_low
                        or "deadline" in err_low
                        or "timeout" in err_low
                        or "timed out" in err_low
                    )

                    # quota-friendly: devolver cedo em quota explícita (preserva pausa do extractor).
                    if self.quota_friendly and status == "quota_exhausted":
                        return GeminiCallResult(
                            ok=False,
                            data={},
                            key_alias=key_alias,
                            masked_key=masked,
                            model=model_name,
                            error_status="quota_exhausted",
                            error_message=last_err_msg,
                        )

                    # FASE 7C — 429/timeout/quota OU credencial inválida -> rotaciona chave já.
                    if is_rate_or_timeout or status in {"invalid", "permission_denied"}:
                        rotate_next_attempt = True
                        break

                    # Erros transitórios não-rate: pequeno backoff e tenta próximo modelo da mesma chave.
                    time.sleep(float(sleep_between_attempts_s) * attempt)
                    continue

            if rotate_next_attempt:
                # FASE 7C — jitter pequeno entre rotações de chave para não martelar a API.
                time.sleep(float(sleep_between_attempts_s))
                continue

        return GeminiCallResult(
            ok=False,
            data={},
            error_status=(last_err_status or "failed"),
            error_message=(last_err_msg or f"Falha após {self.max_attempts_per_image} tentativas"),
        )

