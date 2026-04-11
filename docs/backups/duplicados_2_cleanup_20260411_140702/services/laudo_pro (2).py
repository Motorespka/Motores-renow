from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, List, Optional
from urllib.parse import quote


def normalize_text(value: Optional[Any]) -> str:
    return str(value or "").strip()


def _clean_list(values: Any) -> List[str]:
    if not isinstance(values, list):
        return []
    out: List[str] = []
    for row in values:
        text = normalize_text(row)
        if text:
            out.append(text)
    return out


@dataclass
class MotorIdentificacao:
    fabricante: Optional[str] = None
    modelo: Optional[str] = None
    potencia: Optional[str] = None
    rpm: Optional[str] = None
    tensao: Optional[str] = None
    corrente: Optional[str] = None
    polos: Optional[str] = None
    frequencia: Optional[str] = None
    fase: Optional[str] = None
    carcaca: Optional[str] = None


@dataclass
class LaudoTecnico:
    titulo: str
    emitido_em: str
    empresa_nome: Optional[str]
    identificacao: MotorIdentificacao
    status_geral: str
    nivel_confianca: Optional[str]
    resumo_executivo: str
    pontos_atencao: List[str] = field(default_factory=list)
    analise_bobinagem: Optional[str] = None
    analise_tensao_corrente: Optional[str] = None
    analise_compatibilidade: Optional[str] = None
    analise_incoerencias: Optional[str] = None
    acoes_recomendadas: List[str] = field(default_factory=list)
    observacao_final: Optional[str] = None


def build_laudo_tecnico(resultado: dict, empresa_nome: str | None = None) -> LaudoTecnico:
    identificacao = MotorIdentificacao(
        fabricante=normalize_text(resultado.get("fabricante")) or None,
        modelo=normalize_text(resultado.get("modelo")) or None,
        potencia=normalize_text(resultado.get("potencia")) or None,
        rpm=normalize_text(resultado.get("rpm")) or None,
        tensao=normalize_text(resultado.get("tensao")) or None,
        corrente=normalize_text(resultado.get("corrente")) or None,
        polos=normalize_text(resultado.get("polos")) or None,
        frequencia=normalize_text(resultado.get("frequencia")) or None,
        fase=normalize_text(resultado.get("fase")) or None,
        carcaca=normalize_text(resultado.get("carcaca")) or None,
    )

    return LaudoTecnico(
        titulo="LAUDO TECNICO DO MOTOR",
        emitido_em=datetime.now().strftime("%d/%m/%Y %H:%M"),
        empresa_nome=normalize_text(empresa_nome) or None,
        identificacao=identificacao,
        status_geral=normalize_text(resultado.get("status_geral")) or "Diagnostico preliminar",
        nivel_confianca=normalize_text(resultado.get("nivel_confianca")) or "Conferencia recomendada",
        resumo_executivo=normalize_text(resultado.get("resumo_executivo")),
        pontos_atencao=_clean_list(resultado.get("pontos_atencao")),
        analise_bobinagem=normalize_text(resultado.get("analise_bobinagem")) or None,
        analise_tensao_corrente=normalize_text(resultado.get("analise_tensao_corrente")) or None,
        analise_compatibilidade=normalize_text(resultado.get("analise_compatibilidade")) or None,
        analise_incoerencias=normalize_text(resultado.get("analise_incoerencias")) or None,
        acoes_recomendadas=_clean_list(resultado.get("acoes_recomendadas")),
        observacao_final=normalize_text(resultado.get("observacao_final"))
        or "Este laudo e um apoio tecnico da plataforma e requer conferencia humana antes da aplicacao pratica.",
    )


def format_whatsapp_summary(laudo: LaudoTecnico) -> str:
    linhas = [
        "*LAUDO TECNICO DO MOTOR*",
        "",
        "*Identificacao*",
        f"• Fabricante: {laudo.identificacao.fabricante or '-'}",
        f"• Modelo: {laudo.identificacao.modelo or '-'}",
        f"• Potencia: {laudo.identificacao.potencia or '-'}",
        f"• RPM: {laudo.identificacao.rpm or '-'}",
        f"• Tensao: {laudo.identificacao.tensao or '-'}",
        f"• Polos: {laudo.identificacao.polos or '-'}",
        "",
        "*Resumo tecnico*",
        laudo.resumo_executivo or "-",
    ]

    if laudo.pontos_atencao:
        linhas.extend(["", "*Pontos de atencao*"])
        for item in laudo.pontos_atencao[:3]:
            linhas.append(f"• {item}")

    if laudo.acoes_recomendadas:
        linhas.extend(["", "*Recomendacao*", laudo.acoes_recomendadas[0]])

    linhas.extend(
        [
            "",
            "*Observacao*",
            "Este laudo e um apoio tecnico e deve ser confirmado antes da execucao final.",
        ]
    )
    return "\n".join(linhas)


def format_whatsapp_full(laudo: LaudoTecnico) -> str:
    linhas = [
        "*LAUDO TECNICO DO MOTOR*",
        f"Emitido em: {laudo.emitido_em}",
        "",
        "*1. Identificacao*",
        f"• Fabricante: {laudo.identificacao.fabricante or '-'}",
        f"• Modelo: {laudo.identificacao.modelo or '-'}",
        f"• Potencia: {laudo.identificacao.potencia or '-'}",
        f"• RPM: {laudo.identificacao.rpm or '-'}",
        f"• Tensao: {laudo.identificacao.tensao or '-'}",
        f"• Corrente: {laudo.identificacao.corrente or '-'}",
        f"• Polos: {laudo.identificacao.polos or '-'}",
        f"• Frequencia: {laudo.identificacao.frequencia or '-'}",
        "",
        "*2. Resumo executivo*",
        laudo.resumo_executivo or "-",
    ]

    linhas.extend(["", "*3. Analise tecnica*"])
    if laudo.analise_bobinagem:
        linhas.append(f"• Bobinagem: {laudo.analise_bobinagem}")
    if laudo.analise_tensao_corrente:
        linhas.append(f"• Tensao/Corrente: {laudo.analise_tensao_corrente}")
    if laudo.analise_compatibilidade:
        linhas.append(f"• Compatibilidade: {laudo.analise_compatibilidade}")
    if laudo.analise_incoerencias:
        linhas.append(f"• Incoerencias: {laudo.analise_incoerencias}")

    if laudo.acoes_recomendadas:
        linhas.extend(["", "*4. Acao recomendada*"])
        for acao in laudo.acoes_recomendadas[:5]:
            linhas.append(f"• {acao}")

    linhas.extend(
        [
            "",
            "*5. Observacao*",
            "Este laudo e um apoio tecnico da plataforma e requer conferencia humana antes da aplicacao pratica.",
        ]
    )
    return "\n".join(linhas)


def build_wa_link(numero: str, mensagem: str) -> str:
    numero_limpo = "".join(ch for ch in str(numero or "") if ch.isdigit())
    return f"https://wa.me/{numero_limpo}?text={quote(mensagem)}"

