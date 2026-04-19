from __future__ import annotations

import streamlit as st

from core.access_control import can_access_paid_features
from core.navigation import Route


def render(ctx) -> None:
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
        "- No **detalhe do motor**, pode abrir uma OS já associada ao `motor_id` (atalho quando existir).\n"
        "- Use a **busca global** no topo como atalho; os filtros finos ficam em cada página."
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
        "- **Nova OS:** título/referência, `motor_id` opcional (UUID do motor na base), etapa inicial, vínculo a um cálculo.\n"
        "- **Etapas típicas:** recebido → busca/criação de cálculo → limpeza → rebobinagem → impregnação → montagem → "
        "teste → peças → entrega → encerrado. Cada mudança fica na **linha do tempo**.\n"
        "- **Ficha mecânica:** rolamentos, alinhamento, torque, vibração, temperatura em teste, observações antes/depois.\n"
        "- **Texto para o cliente:** aparece no topo do PDF (garantia, escopo, observações de entrega).\n"
        "- **Anexos:** uma URL por linha (fotos no Storage, Google Drive, etc.); o PDF lista os links (não embute ficheiros grandes).\n"
        "- **Responsável na capa do PDF:** campo opcional na OS ou variável de ambiente `MOTORES_PDF_RESPONSAVEL`.\n"
        "- **Exportação:** JSON completo ou CSV (uma linha + coluna `payload_json`) para arquivo interno.\n"
        "- **Operação interna (sem cliente):** prazo AAAA-MM-DD, orçamento/custos em R$ (gravados em centavos) e "
        "referência curta — aparecem no PDF; não use para dados pessoais.\n"
        "- **Filtros:** etapa, texto no número/título/payload, motor id parcial, últimos N dias, só as minhas OS."
    )

    st.markdown("#### 4. PDF e identidade visual")
    st.markdown(
        "- O PDF tenta **DejaVu** (Linux/Streamlit Cloud) ou **Arial** (Windows) para português com acentos.\n"
        "- Coloque um logo em `assets/logo.png` (ou `logo_mrw.png`, `brand.png`) para aparecer na **capa**.\n"
        "- `MOTORES_PDF_EMPRESA`, `MOTORES_PDF_ENDERECO`, `MOTORES_PDF_RESPONSAVEL` personalizam o cabeçalho/capa.\n"
        "- `MOTORES_PDF_FONT_REGULAR` / `MOTORES_PDF_FONT_BOLD` forçam tipos TTF próprios, se necessário."
    )

    st.markdown("#### 5. Segurança (Supabase)")
    st.markdown(
        "- Migração **`20260418_0049_oficina_workshop_rls.sql`:** políticas RLS por `created_by` = `auth.uid()`.\n"
        "- Recomendação: mantenha `created_by` preenchido ao criar cálculos e OS (o Streamlit já envia o id da sessão).\n"
        "- Linhas antigas com `created_by` nulo continuam acessíveis a qualquer sessão autenticada até fazer **backfill**."
    )

    st.markdown("#### 6. Atualizações e ambiente")
    st.markdown(
        "- A página **Atualizações** lê `data/releases.json` (mesma fonte que o site Next.js).\n"
        "- **Python 3.11:** ficheiro `runtime.txt` na raiz para o Streamlit Cloud; dependências em `requirements.txt`.\n"
        "- CI no GitHub Actions executa `pytest` em 3.11 em cada push/PR."
    )

    c0, c1, c2 = st.columns(3)
    with c0:
        if st.button("Ir para Consulta", use_container_width=True, key="guia_consulta"):
            ctx.session.set_route(Route.CONSULTA)
            st.rerun()
    if can_access_paid_features(client=ctx.supabase):
        with c1:
            if st.button("Ir para Biblioteca de calculos", use_container_width=True, key="guia_bib"):
                ctx.session.set_route(Route.BIBLIOTECA_CALCULOS)
                st.rerun()
        with c2:
            if st.button("Ir para Ordens de servico", use_container_width=True, key="guia_os"):
                ctx.session.set_route(Route.ORDENS_SERVICO)
                st.rerun()
    else:
        with c1:
            st.caption("Plano PRO: atalhos para Biblioteca e Ordens de servico aparecem quando o plano incluir oficina.")
        with c2:
            st.empty()


def show(ctx):
    return render(ctx)
