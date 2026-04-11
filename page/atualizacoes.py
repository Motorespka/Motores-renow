from __future__ import annotations

from typing import List, Dict

import streamlit as st


CHANGELOG: List[Dict[str, object]] = [
    {
        "versao": "V20.1",
        "data": "2026-04-11",
        "titulo": "Cadastro resiliente e consulta mais objetiva",
        "adicoes": [
            "Acao de exclusao de motor com confirmacao, disponivel apenas para admin.",
            "Previa tecnica no card da consulta com dados de rebobinagem e mecanica.",
        ],
        "correcoes": [
            "Cadastro agora remove automaticamente colunas inexistentes no schema antes do insert.",
            "Removido bloco redundante de resumo tecnico para evitar informacao duplicada na consulta.",
        ],
    },
    {
        "versao": "V20.0",
        "data": "2026-04-11",
        "titulo": "Cadastro robusto e anti-duplicacao",
        "adicoes": [
            "Bloqueio de duplicacao no cadastro antes do insert em motores.",
            "Historico de atualizacoes mantido na propria interface.",
        ],
        "correcoes": [
            "Cadastro de usuario passa a ter fallback por username no perfil.",
            "Fluxo de consulta otimizado para reduzir lentidao no site.",
        ],
    },
    {
        "versao": "V10.3",
        "data": "2026-04-10",
        "titulo": "Estabilidade de consulta e desempenho",
        "adicoes": [
            "Aba Atualizacoes adicionada ao menu principal.",
            "Paginacao na consulta de motores para renderizar lotes menores.",
        ],
        "correcoes": [
            "Leitura de motores otimizada com menos roundtrips no Supabase.",
            "Sincronizacao de perfil de login com cache curto para reduzir latencia.",
            "Auto-upsert de usuario em usuarios_app no login/cadastro quando permitido.",
        ],
    },
    {
        "versao": "V10.2",
        "data": "2026-04-10",
        "titulo": "Sessao persistente no refresh",
        "adicoes": [
            "Persistencia de refresh token assinada em query param tecnico.",
        ],
        "correcoes": [
            "F5 nao derruba login quando a sessao do Supabase ainda e valida.",
            "Logout limpa token persistido para evitar reautenticacao indevida.",
        ],
    },
    {
        "versao": "V10.1",
        "data": "2026-04-10",
        "titulo": "Confiabilidade de runtime por navegador",
        "adicoes": [
            "Chave de runtime por navegador (mrw_sid) para isolar sessoes.",
        ],
        "correcoes": [
            "Removida instabilidade por troca de cache key entre reruns.",
        ],
    },
]


def _render_release_card(item: Dict[str, object]) -> None:
    versao = str(item.get("versao") or "-")
    data = str(item.get("data") or "-")
    titulo = str(item.get("titulo") or "Atualizacao")
    adicoes = item.get("adicoes") or []
    correcoes = item.get("correcoes") or []

    st.markdown(
        f"""
        <div class="data-panel" style="margin-bottom: 14px;">
            <div class="data-label">{versao} | {data}</div>
            <div class="data-value" style="font-size: 1.04rem;">{titulo}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("**Adicoes**")
    if isinstance(adicoes, list) and adicoes:
        for row in adicoes:
            st.write(f"- {row}")
    else:
        st.caption("Sem adicoes registradas.")

    st.markdown("**Bugs corrigidos**")
    if isinstance(correcoes, list) and correcoes:
        for row in correcoes:
            st.write(f"- {row}")
    else:
        st.caption("Sem correcoes registradas.")

    st.divider()


def render(_ctx) -> None:
    st.markdown(
        """
        <div class="consulta-hero">
            <div class="consulta-hero__tag">RELEASE NOTES</div>
            <h1>Atualizacoes do Sistema</h1>
            <p>Historico de versoes, melhorias adicionadas e bugs corrigidos.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for item in CHANGELOG:
        _render_release_card(item)


def show(ctx) -> None:
    return render(ctx)
