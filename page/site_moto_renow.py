"""Conteúdo comercial e operacional no Streamlit (sem Next.js nem FastAPI)."""

from __future__ import annotations

import os
import re
from urllib.parse import quote_plus

import streamlit as st

from core.navigation import Route
from core.streamlit_perf import pop_page_ctx_pack, stash_page_ctx
from core.ui_feedback import mrw_render_banner_zone


def _read_secret_or_env(*names: str) -> str:
    for name in names:
        try:
            value = st.secrets.get(name)
            if value:
                return str(value).strip()
        except Exception:
            pass
        value = os.environ.get(name)
        if value:
            return str(value).strip()
    return ""


def _whatsapp_comercial_url(prefill: str = "") -> tuple[str, str]:
    """(url, aviso) — url vazio se número não configurado."""
    raw = _read_secret_or_env(
        "WHATSAPP_UPGRADE_NUMBER",
        "UPGRADE_WHATSAPP_NUMBER",
        "WHATSAPP_NUMBER",
        "WHATSAPP_SALES_NUMBER",
    )
    phone = re.sub(r"\D+", "", raw)
    if phone.startswith("00"):
        phone = phone[2:]
    if len(phone) == 11 and not phone.startswith("55"):
        phone = f"55{phone}"
    if len(phone) < 10:
        return "", "Configure WHATSAPP_NUMBER ou WHATSAPP_UPGRADE_NUMBER nos secrets / variáveis de ambiente."
    base = f"https://wa.me/{phone}"
    if prefill.strip():
        return f"{base}?text={quote_plus(prefill.strip())}", ""
    return base, ""


def _wa_cta(label: str, prefill: str) -> None:
    url, hint = _whatsapp_comercial_url(prefill)
    if url:
        if hasattr(st, "link_button"):
            st.link_button(label, url, use_container_width=True)
        else:
            st.markdown(f"[{label}]({url})")
    else:
        st.caption(hint or "WhatsApp não configurado.")


def _site_moto_renow_body() -> None:
    mrw_render_banner_zone()
    app_ctx = pop_page_ctx_pack().get("ctx")
    if app_ctx is None:
        return

    st.markdown(
        """
        <div class="consulta-hero">
            <div class="consulta-hero__tag">MOTO-RENOW</div>
            <h1>Sobre a plataforma</h1>
            <p>Informação para donos de oficina, técnicos e gestores — tudo aqui na app, sem site externo obrigatório.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_inicio, tab_oficinas, tab_eng, tab_func, tab_planos, tab_como = st.tabs(
        ["Início", "Para oficinas", "Manutenção elétrica", "Funcionalidades", "Planos", "Como começar"]
    )

    with tab_inicio:
        st.markdown(
            """
### Menos improviso na bancada

A Moto-Renow organiza **fichas de motor**, **filas de trabalho** e **leitura técnica** no mesmo sítio onde a equipa opera.

- **Plano comercial**, faturação e dados sensíveis tratam-se no **WhatsApp** — aqui não pedimos cartão nem referências bancárias.
- **Primeiro** percorra a Consulta e o painel; **depois** combinamos o que faz sentido para a vossa operação.

**Atalhos na barra lateral:** Consulta, Guia da oficina, Visão geral, Atualizações, e módulos PRO quando o plano permitir.
            """.strip()
        )
        st.divider()
        st.markdown("**Falar com a equipa (comercial / plano)**")
        _wa_cta(
            "Abrir WhatsApp — plano ou demo",
            "Olá! Quero saber mais sobre a Moto-Renow para a minha oficina (sem pagamento pela app).",
        )

    with tab_oficinas:
        st.markdown(
            """
### Para donos e gestores

**O que costuma doer**
- Fila parada e ninguém sabe em que etapa está o motor.
- Retrabalho por diagnóstico fraco ou falta de contexto entre turnos.
- Cliente a perguntar “já está?” sem um estado único na oficina.
- Histórico técnico espalhado (papel, mensagens soltas).
- Compras de material sem rasto ligado à OS.

**O que a ferramenta ajuda a ver**
- Um sítio para **ficha** e **OS**, com estado visível para a equipa.
- **Indicadores simples** para entupimentos — sem projeto de BI.
- **Transparência:** não prometemos ERP completo nem substituir o cérebro do técnico.

**Comercial:** propostas e condições **só no WhatsApp**; esta app não recolhe dados de pagamento.
            """.strip()
        )
        _wa_cta(
            "WhatsApp — sou dono/gestor",
            "Olá! Sou dono/gestor de oficina de motores e quero perceber se a Moto-Renow encaixa na nossa operação.",
        )

    with tab_eng:
        st.markdown(
            """
### Motores elétricos — manutenção

**Onde ajuda**
- **Consulta e rasto:** placa, frame, dados e histórico para reduzir ambiguidade entre desmontagem, rebobinagem e ensaio.
- **OS por etapas:** estado visível — menos retrabalho entre turnos.
- **Conferência:** segundo olhar antes de fechar trabalho sensível (quando o fluxo estiver activo no vosso plano).
- **Biblioteca / receitas** (plano PRO): padronizar rebobinagens e revisões.

**Critério técnico**
- A plataforma **apoia** decisão e registo; **não substitui** ensaio, instrumentação calibrada nem experiência do técnico.
- Normas, laudos legais e responsabilidade civil **mantêm-se** com a oficina e com quem assina o trabalho.
            """.strip()
        )
        _wa_cta(
            "WhatsApp — nível técnico",
            "Olá! Sou técnico/engenheiro de manutenção de motores elétricos e quero alinhar profundidade técnica da Moto-Renow.",
        )

    with tab_func:
        st.markdown(
            """
### Mapa de capacidades (resumo)

Use o separador **Funcionalidades** como **lista de conversa** com a equipa: nem tudo estará ligado na mesma versão.

**Entrada e triagem:** ficha do motor, checklist de entrada, prioridade interna.

**Diagnóstico:** registo de leituras e hipóteses; alertas de revisão técnica quando o parser pede conferência humana.

**Bancada:** OS com etapas, materiais por OS, tempo em etapa, rasto de peças trocadas.

**Qualidade:** checklist de saída, resumo para cliente, histórico do mesmo motor quando voltar.

**Gestão:** indicadores simples, carga por técnico, motivos de retrabalho (quando configurado).

**Stock leve:** alertas de consumíveis, lista para compras internas — sem ser ERP completo.

Para o **detalhe linha a linha** do roadmap, peça documentação ou walkthrough no WhatsApp.
            """.strip()
        )

    with tab_planos:
        st.markdown(
            """
### Planos (visão geral)

| Nível | Foco |
|-------|------|
| **Essencial** | Consulta e registo técnico rápido na bancada. |
| **Oficina** | OS, fila e visibilidade para a equipa. |
| **Pro** | Fluxos mais profundos, conferência, biblioteca — conforme o vosso caso. |

**Valores** são **sob consulta** e acertam-se **no WhatsApp** — não há checkout nesta aplicação.
            """.strip()
        )
        _wa_cta(
            "WhatsApp — planos e condições",
            "Olá! Quero detalhe dos planos Moto-Renow (módulos e utilizadores). Prefiro acertar tudo por WhatsApp.",
        )

    with tab_como:
        st.markdown(
            """
### Como começar

1. **Combinar o plano** no WhatsApp (sem dados de pagamento aqui).
2. **Receber acesso** (credenciais / convite) e fazer login nesta app.
3. **Entrar pela Visão geral** e pela **Consulta** — perceber fila e fichas.
4. **Alinhar hábitos** da oficina: quem abre OS, quem fecha, quando atualizar estado.

Dúvidas comerciais ou contratuais: **sempre pelo canal directo** acordado com a equipa Moto-Renow.
            """.strip()
        )

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("Ir para a Consulta", use_container_width=True, key="site_go_consulta"):
            app_ctx.session.set_route(Route.CONSULTA)
            st.rerun()
    with c2:
        if st.button("Ir para o Guia da oficina", use_container_width=True, key="site_go_guia"):
            app_ctx.session.set_route(Route.GUIA_OFICINA)
            st.rerun()


def render(ctx) -> None:
    stash_page_ctx(ctx)
    _site_moto_renow_body()


def show(ctx) -> None:
    return render(ctx)
