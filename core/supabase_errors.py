"""Mensagens de erro Supabase/rede mais acionaveis para quem usa a app o dia inteiro."""

from __future__ import annotations


def format_supabase_client_error(exc: BaseException) -> str:
    msg = str(exc).strip() or exc.__class__.__name__
    low = msg.lower()
    hints: list[str] = []
    if "connection" in low or "timeout" in low or "timed out" in low or "ssl" in low:
        hints.append("Verifique rede, VPN ou firewall; tente de novo dentro de instantes.")
    if "jwt" in low or "401" in msg or "403" in msg or ("invalid" in low and "token" in low):
        hints.append("Sessao ou chave invalida: volte ao login ou confirme secrets/env do projeto.")
    if "name or service not known" in low or "getaddrinfo" in low:
        hints.append("DNS ou URL do Supabase incorrecta (SUPABASE_URL / secrets).")
    if "relation" in low and "does not exist" in low:
        hints.append("Tabela em falta: aplique migracoes SQL indicadas na mensagem da pagina.")
    if hints:
        return msg + " — " + " ".join(hints)
    return msg
