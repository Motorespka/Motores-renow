from __future__ import annotations

import streamlit as st

from core.access_control import can_access_paid_features
from core.navigation import Route
from core.streamlit_perf import maybe_fragment, pop_page_ctx_pack, stash_page_ctx
from core.ui_feedback import mrw_render_banner_zone


def render(ctx) -> None:
    stash_page_ctx(ctx)
    _guia_oficina_page_fragment()


@maybe_fragment
def _guia_oficina_page_fragment() -> None:
    mrw_render_banner_zone()
    ctx = pop_page_ctx_pack().get("ctx")
    if ctx is None:
        return

    st.markdown("### Guia da oficina (Moto-Renow)")
    st.caption(
        "Fluxo recomendado entre **Consulta**, **Biblioteca de cálculos**, **Ordens de serviço** e **PDF de entrega**. "
        "Funcionalidades PRO exigem plano pago."
    )

    st.info(
        "**Resumo:** recebe o motor → regista ou encontra um **cálculo** na biblioteca → abre uma **OS** e avança as "
        "etapas → preenche **ficha mecânica** e **testes** → escreve **notas ao cliente** e **URLs de anexos** → "
        "exporta **PDF** (e opcionalmente **JSON/CSV** para arquivo)."
    )

    st.markdown("#### 1. Consulta e motor")
    st.markdown(
        "- Na **Consulta**, localize o motor pelo número de série, fabricante ou texto livre.\n"
        "- No **detalhe do motor**, pode abrir uma **ordem de serviço** ligada a esse motor (quando existir atalho).\n"
        "- Use a **busca** no topo como atalho; os filtros mais finos ficam em cada página."
    )

    st.markdown("#### 2. Biblioteca de cálculos (PRO)")
    st.markdown(
        "- Guarde **receitas reutilizáveis** (passos, espiras, fio, ligação, esquema).\n"
        "- **Testes de bancada** em grupos (ex.: corrente, isolamento) com linhas nome/valor; opcional **limite/critério** "
        "e **resultado OK/FORA** para registo objetivo no PDF.\n"
        "- **Mecânica** opcional (rolamentos, carcaça, acoplamento) para referência de montagem.\n"
        "- Use **tags** e a pesquisa; filtre por tag ou **só os meus** (registos com o seu utilizador).\n"
        "- **Revisões:** crie uma nova revisão a partir de um registo existente para histórico sem perder o original."
    )

    st.markdown("#### 3. Ordem de serviço (PRO)")
    st.markdown(
        "- **Nova OS:** título ou referência interna, identificador do motor (opcional), etapa inicial e vínculo a um cálculo da biblioteca.\n"
        "- **Etapas típicas:** recebido → busca/criação de cálculo → limpeza → rebobinagem → impregnação → montagem → "
        "teste → peças → entrega → encerrado. Cada mudança fica na **linha do tempo**.\n"
        "- **Ficha mecânica:** rolamentos, alinhamento, torque, vibração, temperatura em teste, observações antes/depois.\n"
        "- **Texto para o cliente:** aparece no topo do PDF (garantia, escopo, observações de entrega).\n"
        "- **Anexos:** uma URL por linha (fotos na nuvem, partilha, etc.); o PDF lista os links (não embute ficheiros grandes).\n"
        "- **Responsável na capa do PDF:** pode preencher na própria OS ou pedir ao administrador para configurar texto fixo no servidor.\n"
        "- **Exportação:** ficheiros para arquivo interno (JSON completo ou CSV resumido), úteis para cópia de segurança.\n"
        "- **Operação interna (sem cliente):** prazo em data, orçamento e custos em reais e referência curta — aparecem no PDF; "
        "não use para dados pessoais.\n"
        "- **Filtros:** etapa, texto na OS, parte do identificador do motor, últimos dias, só as minhas ordens."
    )

    st.markdown("#### 4. PDF e identidade visual")
    st.markdown(
        "- O PDF usa fontes comuns do sistema para **português com acentos** (o servidor escolhe automaticamente).\n"
        "- **Logo na capa:** o administrador configura no **servidor** uma imagem de marca; se não estiver definida, o PDF segue só com texto.\n"
        "- **Cabeçalho da empresa:** nome, morada e responsável podem ser definidos pelo administrador nas **definições do servidor** "
        "(aqui ficam só as indicações de fluxo).\n"
        "- **Tipos de letra próprios:** só em casos especiais, também via configuração no servidor."
    )

    st.markdown("#### 5. Segurança e partilha de dados")
    st.markdown(
        "- Na **cloud**, as ordens e cálculos podem ficar visíveis sobretudo a **quem os criou** (políticas de acesso na base de dados).\n"
        "- Ao criar cálculos e OS, a aplicação regista **quem está ligado** — ajuda a saber de quem é cada ficha.\n"
        "- Registos antigos sem autor definido podem continuar visíveis a toda a equipa até o administrador alinhar dados em falta."
    )

    st.markdown("#### 6. Atualizações e ambiente")
    st.markdown(
        "- A página **Atualizações** mostra **o que mudou** entre versões (notas para a equipa).\n"
        "- O **servidor na nuvem** usa a versão de Python e bibliotecas acordadas com o administrador; em caso de dúvida, peça ao admin.\n"
        "- **Qualidade:** há testes automáticos no repositório antes de publicar alterações (processo interno de equipa)."
    )

    st.markdown("#### 7. Teclado e ritmo (producao)")
    st.markdown(
        "- **Tab** / **Shift+Tab**: navegar entre campos e botoes.\n"
        "- **Enter**: em **formularios**, envia quando o foco esta no botao de envio.\n"
        "- **Espaco**: alternar checkbox.\n"
        "- **Busca no topo:** o historico de termos atualiza-se sozinho; a zona de busca é mais leve para não atrasar o resto do ecrã.\n"
        "- **Ctrl+S** do navegador guarda a **pagina**, não a ficha na base — use sempre o botao **Salvar** / **Guardar** da aplicação."
    )

    c0, c1, c2, c3 = st.columns(4)
    with c0:
        if st.button("Ir para Consulta", use_container_width=True, key="guia_consulta"):
            ctx.session.set_route(Route.CONSULTA)
            st.rerun()
    with c1:
        if st.button("Ferramentas bobinagem", use_container_width=True, key="guia_ferr"):
            ctx.session.set_route(Route.FERRAMENTAS_BOBINAGEM)
            st.rerun()
    if can_access_paid_features(client=ctx.supabase):
        with c2:
            if st.button("Ir para Biblioteca de calculos", use_container_width=True, key="guia_bib"):
                ctx.session.set_route(Route.BIBLIOTECA_CALCULOS)
                st.rerun()
        with c3:
            if st.button("Ir para Ordens de servico", use_container_width=True, key="guia_os"):
                ctx.session.set_route(Route.ORDENS_SERVICO)
                st.rerun()
    else:
        with c2:
            st.caption("Plano PRO: atalhos para Biblioteca e Ordens de servico aparecem quando o plano incluir oficina.")
        with c3:
            st.empty()


def show(ctx):
    return render(ctx)
