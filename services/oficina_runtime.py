from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from core.calculadora import alertas_validacao_projeto
from services.aprendizado_motor import salvar_motor as salvar_memoria_aprendizado
from services.aprendizado_motor import sugestao_inteligente
from services.diagnostico_ia import diagnostico_motor
from services.engenharia_ia import engenharia_automatica
from services.fabrica_motor import analise_fabrica
from services.ia_oficina import inteligencia_oficina, registrar_rebobinagem


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _to_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [_to_text(v) for v in value if _to_text(v)]
    text = _to_text(value)
    if not text:
        return []
    return [p.strip() for p in text.replace(";", ",").split(",") if p.strip()]


def _first_numeric(value: Any) -> str:
    text = _to_text(value)
    if not text:
        return ""
    for sep in ["/", ",", ";", "|", " "]:
        if sep in text:
            text = text.split(sep)[0].strip()
            break
    out = []
    dot_used = False
    for ch in text:
        if ch.isdigit():
            out.append(ch)
        elif ch in ".,":  # decimal separator
            if not dot_used:
                out.append(".")
                dot_used = True
    return "".join(out)


def _build_dados_base(normalized: Dict[str, Any]) -> Dict[str, str]:
    motor = normalized.get("motor", {}) if isinstance(normalized.get("motor"), dict) else {}
    tensao_list = _to_list(motor.get("tensao"))
    corrente_list = _to_list(motor.get("corrente"))

    tensao_text = tensao_list[0] if tensao_list else _to_text(motor.get("tensao"))
    corrente_text = corrente_list[0] if corrente_list else _to_text(motor.get("corrente"))

    return {
        "marca": _to_text(motor.get("marca")),
        "modelo": _to_text(motor.get("modelo")),
        "potencia": _to_text(motor.get("potencia") or motor.get("cv")),
        "rpm": _to_text(motor.get("rpm")),
        "tensao": _to_text(tensao_text),
        "corrente": _to_text(corrente_text),
        "frequencia": _to_text(motor.get("frequencia")),
        "fases": _to_text(motor.get("fases")),
        "tipo_motor": _to_text(motor.get("tipo_motor")),
    }


def _media_espiras(normalized: Dict[str, Any]) -> int | None:
    principal = normalized.get("bobinagem_principal", {})
    if not isinstance(principal, dict):
        return None
    espiras = _to_list(principal.get("espiras"))
    nums: List[float] = []
    for item in espiras:
        num = _first_numeric(item)
        if not num:
            continue
        try:
            nums.append(float(num))
        except Exception:
            continue
    if not nums:
        return None
    return round(sum(nums) / len(nums))


def _build_engenharia(normalized: Dict[str, Any], dados_base: Dict[str, str]) -> Dict[str, Any]:
    principal = normalized.get("bobinagem_principal", {})
    if not isinstance(principal, dict):
        principal = {}

    engenharia = engenharia_automatica(
        {
            "rpm": _first_numeric(dados_base.get("rpm")),
            "tensao": _first_numeric(dados_base.get("tensao")),
            "corrente": _first_numeric(dados_base.get("corrente")),
        }
    ) or {}

    espiras_originais = _to_list(principal.get("espiras"))
    fio_list = _to_list(principal.get("fios"))
    engenharia["espiras_originais"] = espiras_originais
    engenharia["fio_original"] = fio_list[0] if fio_list else ""
    engenharia["media_espiras"] = _media_espiras(normalized)
    return engenharia


def _infer_resultado_status(normalized: Dict[str, Any], evento: str) -> str:
    oficina = normalized.get("oficina", {}) if isinstance(normalized.get("oficina"), dict) else {}
    resultado = oficina.get("resultado_pos_servico", {}) if isinstance(oficina.get("resultado_pos_servico"), dict) else {}
    status = _to_text(resultado.get("status")).lower()
    if status:
        if any(tok in status for tok in ["ok", "aprov", "conclu", "estavel"]):
            return "OK"
        if any(tok in status for tok in ["falha", "erro", "queim", "reprov"]):
            return "FALHA"
        return "EM_ANALISE"

    if evento in {"edicao", "servico"}:
        texto = _to_text(normalized.get("observacoes_gerais")).lower()
        if any(tok in texto for tok in ["ok", "aprov", "conclu", "estavel"]):
            return "OK"
        if any(tok in texto for tok in ["falha", "erro", "queim", "reprov"]):
            return "FALHA"
    return "EM_ANALISE"


def _append_historico(oficina: Dict[str, Any], evento: str, resumo: str, payload: Dict[str, Any]) -> None:
    hist = oficina.get("historico_tecnico")
    if not isinstance(hist, list):
        hist = []
    hist.append(
        {
            "data": _now(),
            "evento": evento,
            "resumo": resumo,
            "payload": payload,
        }
    )
    oficina["historico_tecnico"] = hist[-60:]


def _append_fluxo(oficina: Dict[str, Any], evento: str) -> None:
    fluxo = oficina.get("fluxo_fechado")
    if not isinstance(fluxo, list):
        fluxo = []

    etapas = [
        ("captura", "ok"),
        ("validacao", "ok"),
        ("diagnostico", "ok"),
        ("servico", "pendente" if evento == "cadastro" else "ok"),
        ("aprendizado", "ok"),
    ]
    stamp = _now()
    fluxo.append(
        {
            "data": stamp,
            "evento": evento,
            "etapas": [{"etapa": etapa, "status": status} for etapa, status in etapas],
        }
    )
    oficina["fluxo_fechado"] = fluxo[-30:]


def enriquecer_motor_oficina(normalized: Dict[str, Any], evento: str = "cadastro") -> Dict[str, Any]:
    data = dict(normalized or {})
    oficina = data.get("oficina")
    if not isinstance(oficina, dict):
        oficina = {}

    dados_base = _build_dados_base(data)
    engenharia = _build_engenharia(data, dados_base)
    fabrica = analise_fabrica({"tensao": dados_base.get("tensao", ""), "corrente": dados_base.get("corrente", "")}) or {}
    avisos = diagnostico_motor(dados_base, engenharia, fabrica) or []

    validacao_input = {
        "potencia": dados_base.get("potencia"),
        "tensao": dados_base.get("tensao"),
        "corrente": dados_base.get("corrente"),
        "rpm": dados_base.get("rpm"),
        "frequencia": dados_base.get("frequencia"),
        "fases": dados_base.get("fases"),
        "tipo_motor": dados_base.get("tipo_motor"),
    }
    alertas_validacao = alertas_validacao_projeto(validacao_input)

    oficina["dados_placa"] = {
        "marca": dados_base.get("marca"),
        "modelo": dados_base.get("modelo"),
        "potencia": dados_base.get("potencia"),
        "rpm": dados_base.get("rpm"),
        "tensao": dados_base.get("tensao"),
        "corrente": dados_base.get("corrente"),
        "fases": dados_base.get("fases"),
        "tipo_motor": dados_base.get("tipo_motor"),
    }

    oficina["calculos_aplicados"] = {
        "engenharia_automatica": engenharia,
        "analise_fabrica": fabrica,
    }

    oficina["diagnostico"] = {
        "avisos": avisos,
        "alertas_validacao": alertas_validacao,
        "fonte": "servicos_oficina_conectados",
        "data": _now(),
    }

    servico_executado = oficina.get("servico_executado")
    if not isinstance(servico_executado, dict):
        servico_executado = {}
    servico_executado.setdefault("descricao", "")
    servico_executado.setdefault("responsavel", "")
    servico_executado["status"] = "Capturado para oficina" if evento == "cadastro" else "Servico atualizado"
    servico_executado["data"] = _now()
    oficina["servico_executado"] = servico_executado

    resultado_pos = oficina.get("resultado_pos_servico")
    if not isinstance(resultado_pos, dict):
        resultado_pos = {}
    if "status" not in resultado_pos or not _to_text(resultado_pos.get("status")):
        resultado_pos["status"] = "Em acompanhamento"
    resultado_pos["observacoes"] = _to_text(data.get("observacoes_gerais")) or _to_text(resultado_pos.get("observacoes"))
    resultado_pos["data"] = _now()
    oficina["resultado_pos_servico"] = resultado_pos

    sugestao_oficina = None
    sugestao_aprendizado = None
    resultado_memoria = _infer_resultado_status(data, evento)
    try:
        salvar_memoria_aprendizado(dados_base, engenharia)
    except Exception:
        pass
    try:
        registrar_rebobinagem(dados_base, engenharia, resultado_memoria)
    except Exception:
        pass
    try:
        sugestao_oficina = inteligencia_oficina(dados_base)
    except Exception:
        sugestao_oficina = None
    try:
        sugestao_aprendizado = sugestao_inteligente(dados_base)
    except Exception:
        sugestao_aprendizado = None

    oficina["aprendizado"] = {
        "sugestao_oficina": sugestao_oficina or {},
        "sugestao_aprendizado": sugestao_aprendizado or {},
        "ultima_atualizacao": _now(),
    }

    _append_historico(
        oficina,
        evento=evento,
        resumo="Fluxo oficina atualizado",
        payload={
            "diagnostico": avisos[:4],
            "alertas_validacao": alertas_validacao[:4],
            "resultado_memoria": resultado_memoria,
        },
    )
    _append_fluxo(oficina, evento=evento)

    data["oficina"] = oficina
    return data


def resumir_diagnostico_oficina(normalized: Dict[str, Any]) -> Dict[str, Any]:
    oficina = normalized.get("oficina") if isinstance(normalized, dict) else {}
    if not isinstance(oficina, dict):
        return {}
    diagnostico = oficina.get("diagnostico")
    if not isinstance(diagnostico, dict):
        return {}
    return {
        "dados_placa": oficina.get("dados_placa", {}),
        "avisos": diagnostico.get("avisos", []),
        "alertas_validacao": diagnostico.get("alertas_validacao", []),
        "aprendizado": oficina.get("aprendizado", {}),
        "resultado_pos_servico": oficina.get("resultado_pos_servico", {}),
        "historico_tecnico": oficina.get("historico_tecnico", []),
    }


def diagnostico_motor_oficina_readonly(normalized: Dict[str, Any]) -> Dict[str, Any]:
    dados_base = _build_dados_base(normalized)
    engenharia = _build_engenharia(normalized, dados_base)
    fabrica = analise_fabrica({"tensao": dados_base.get("tensao", ""), "corrente": dados_base.get("corrente", "")}) or {}
    avisos = diagnostico_motor(dados_base, engenharia, fabrica) or []
    alertas = alertas_validacao_projeto(
        {
            "potencia": dados_base.get("potencia"),
            "tensao": dados_base.get("tensao"),
            "corrente": dados_base.get("corrente"),
            "rpm": dados_base.get("rpm"),
            "frequencia": dados_base.get("frequencia"),
            "fases": dados_base.get("fases"),
            "tipo_motor": dados_base.get("tipo_motor"),
        }
    )
    return {
        "dados_placa": dados_base,
        "avisos": avisos,
        "alertas_validacao": alertas,
        "calculos_aplicados": {
            "engenharia_automatica": engenharia_automatica(
                {
                    "rpm": _first_numeric(dados_base.get("rpm")),
                    "tensao": _first_numeric(dados_base.get("tensao")),
                    "corrente": _first_numeric(dados_base.get("corrente")),
                }
            )
            or {},
            "analise_fabrica": fabrica,
        },
    }
