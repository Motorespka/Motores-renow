from __future__ import annotations

from typing import List, Dict

import streamlit as st


CHANGELOG: List[Dict[str, object]] = [
    {
        "versao": "V21.2",
        "data": "2026-04-12",
        "titulo": "Roadmap V200: IA com 10 keys, perfil por acesso e recusas de seguranca",
        "adicoes": [
            "Documento de planejamento V200 criado para IA operacional do Motores-Renow.",
            "Escopo por perfil definido: admin analisa sistema, pago gera calculos, free limitado.",
            "Estrategia de key ring com 10 chaves e fallback em backend registrada.",
            "Politica de recusa obrigatoria para pedidos como criar tabela, conceder acesso e expor keys.",
        ],
        "correcoes": [
            "Roadmap V200 deixa de ficar vago e passa a ter diretriz tecnica objetiva para IA segura.",
        ],
    },
    {
        "versao": "V21.1",
        "data": "2026-04-12",
        "titulo": "Atualizacao automatica sem precisar de F5",
        "adicoes": [
            "Auto-refresh global adicionado no App para manter telas atualizadas automaticamente.",
            "Intervalo inteligente por rota: paginas de consulta atualizam mais rapido e formularios com intervalo maior.",
            "Flag ENABLE_LIVE_UPDATES adicionada para ligar/desligar o comportamento sem alterar codigo.",
        ],
        "correcoes": [
            "Removida dependencia manual de F5 para refletir mudancas recentes no site.",
        ],
    },
    {
        "versao": "V21.0",
        "data": "2026-04-11",
        "titulo": "Modulo isolado de development + hub comercial + laudo pro",
        "adicoes": [
            "Feature flags centralizadas para development, laudo pro, WhatsApp e modulo comercial.",
            "Controle de MODO DEVELOPMENT no admin com banner forte de ambiente de teste.",
            "Nova rota Hub Comercial com Classificados, Empresas, Fornecedores, Vagas e Termos.",
            "Moderacao minima no admin para pausar/remover itens e bloquear usuario/empresa por modulo.",
            "Laudo tecnico profissional aditivo no Diagnostico, com formatacao premium.",
            "WhatsApp do laudo com numero temporario (sem persistencia em banco).",
        ],
        "correcoes": [
            "Estrutura nova isolada do fluxo principal, sem alterar cadastro/consulta existentes.",
            "Persistencia do novo modulo preparada com fallback local para evitar impacto em producao.",
        ],
    },
    {
        "versao": "V20.9",
        "data": "2026-04-11",
        "titulo": "Patch surpresa: parser tecnico fase 1",
        "adicoes": [
            "Camada parser_tecnico adicionada no backend com normalizacao de passo/espiras e ligacao eletrica.",
            "Estrutura candidate_alternatives preparada para evolucao futura (Fase 2).",
            "Camada sugestao_historica adicionada como opcional, sem ativacao de consulta pesada.",
        ],
        "correcoes": [
            "Heuristica de ruido OCR reforcada com marcacao obrigatoria de revisao.",
            "Status de revisao padronizado em ok/revisar com TODO explicito para evolucao do validator.",
        ],
    },
    {
        "versao": "V20.8",
        "data": "2026-04-11",
        "titulo": "Hotfix de roteamento Consulta/Cadastro",
        "adicoes": [
            "Consulta volta a respeitar a rota escolhida no menu, sem redirecionamento forcado.",
        ],
        "correcoes": [
            "Removida regra que convertia automaticamente 'consulta' em 'cadastro' para usuarios com acesso de cadastro.",
        ],
    },
    {
        "versao": "V20.7",
        "data": "2026-04-11",
        "titulo": "Hotfix de compatibilidade Streamlit Cloud",
        "adicoes": [
            "Reset de scroll mantido com renderizacao compatível na API components.html.",
        ],
        "correcoes": [
            "Removido parametro invalido que causava TypeError ao abrir telas no Streamlit Cloud.",
        ],
    },
    {
        "versao": "V20.6",
        "data": "2026-04-11",
        "titulo": "Compatibilidade ampliada com RLS",
        "adicoes": [
            "Cadastro agora envia hints de ownership (user_id/owner_id/created_by...) para atender policies RLS comuns.",
            "Fallback admin aceita multiplos nomes de secret para service role.",
        ],
        "correcoes": [
            "Mensagem de bloqueio RLS atualizada com nomes alternativos de chave administrativa.",
        ],
    },
    {
        "versao": "V20.5",
        "data": "2026-04-11",
        "titulo": "Scroll reset reforcado na navegacao",
        "adicoes": [
            "Navegacao lateral agora faz rerun imediato apos trocar rota.",
            "Reset de scroll executa no fim da renderizacao e atinge containers do Streamlit.",
        ],
        "correcoes": [
            "Corrigido caso de abrir nova tela mantendo posicao de scroll anterior.",
        ],
    },
    {
        "versao": "V20.4",
        "data": "2026-04-11",
        "titulo": "Fallback RLS no cadastro",
        "adicoes": [
            "Quando o insert em motores falha por RLS, o sistema tenta fallback com service role (se configurada).",
        ],
        "correcoes": [
            "Mensagem de erro de cadastro agora orienta claramente quando falta permissao RLS.",
        ],
    },
    {
        "versao": "V20.3",
        "data": "2026-04-11",
        "titulo": "Navegacao com scroll reset",
        "adicoes": [
            "Toda troca de tela agora reposiciona automaticamente no topo da pagina.",
        ],
        "correcoes": [
            "Removido comportamento de abrir nova tela no mesmo ponto de scroll da tela anterior.",
        ],
    },
    {
        "versao": "V20.2",
        "data": "2026-04-11",
        "titulo": "Remocao de O.S. no cadastro tecnico",
        "adicoes": [
            "Fluxo de cadastro focado somente em motor tecnico.",
        ],
        "correcoes": [
            "Removido bloco de Cadastro de O.S. que causava erro de API na tabela ordens_servico.",
        ],
    },
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
