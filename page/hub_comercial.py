from __future__ import annotations

from typing import Dict, List
from urllib.parse import quote_plus

import streamlit as st

from core.development_mode import is_dev_mode, resolve_client_ip, use_isolated_mode_for_module
from core.feature_flags import get_feature_flags
from core.navigation import Route
from core.user_identity import resolve_current_user_identity
from services.modulo_comercial import (
    CommercialModuleStore,
    STATUS_ACTIVE,
    STATUS_PAUSED,
    build_empresa_activity_label,
    calcular_score_anuncio,
    formatar_tempo_publicacao,
    mensagem_contato_anuncio,
    mensagem_contato_vaga,
)


TERMS_TEXTS: List[str] = [
    "Os anuncios sao publicados pelos proprios usuarios.",
    "Voce sera direcionado para contato externo.",
    "A plataforma nao participa da contratacao.",
    "Indicadores baseados em atividade na plataforma, nao representando certificacao.",
    "O numero informado para envio via WhatsApp nao sera armazenado.",
]


def _to_text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _wa_link(numero: str, mensagem: str) -> str:
    numero_limpo = "".join(ch for ch in _to_text(numero) if ch.isdigit())
    return f"https://wa.me/{numero_limpo}?text={quote_plus(mensagem)}"


def _show_terms_block() -> None:
    st.markdown("### Termos e avisos")
    for row in TERMS_TEXTS:
        st.write(f"- {row}")


def _render_header(dev_mode: bool, isolated_mode: bool) -> None:
    st.markdown(
        """
        <div class="consulta-hero">
            <div class="consulta-hero__tag">MODULO COMERCIAL</div>
            <h1>Classificados, Empresas, Fornecedores e Vagas</h1>
            <p>Camada adicional isolada do fluxo principal de cadastro/consulta/diagnostico.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if dev_mode:
        st.warning("MODO DEVELOPMENT: dados deste modulo estao isolados da operacao principal.")
    if isolated_mode:
        st.caption("Persistencia local/isolada ativa para este modulo.")


def _render_classificados_tab(store: CommercialModuleStore, identity: Dict[str, str], dev_mode: bool) -> None:
    st.markdown("### Classificados por cidade")
    st.caption("Contato externo direto: a plataforma nao intermedeia negociacao.")

    with st.expander("Publicar anuncio", expanded=False):
        if store.is_blocked("user", identity.get("user_id", ""), "anuncios"):
            st.error("Seu usuario esta bloqueado para publicar anuncios neste modulo.")
        else:
            with st.form("form_novo_anuncio", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    titulo = st.text_input("Titulo")
                    categoria = st.text_input("Categoria")
                    descricao = st.text_area("Descricao curta", height=90)
                    preco_valor = st.text_input("Preco (numero opcional)")
                    preco_texto = st.text_input("Preco texto (ex.: Sob consulta)")
                with c2:
                    cidade = st.text_input("Cidade")
                    estado = st.text_input("Estado")
                    nome_publico = st.text_input("Nome publico")
                    whatsapp = st.text_input("WhatsApp")
                    regiao = st.text_input("Regiao de atendimento")
                    rota = st.text_input("Rota de entrega")
                    pedido_min = st.text_input("Pedido minimo")
                    retirada_local = st.toggle("Retirada local")
                    entrega_consulta = st.toggle("Entrega sob consulta")
                enviado = st.form_submit_button("Publicar anuncio", use_container_width=True)
                if enviado:
                    if not titulo or not cidade or not estado or not whatsapp:
                        st.error("Preencha titulo, cidade, estado e WhatsApp.")
                    else:
                        row = store.save_anuncio(
                            {
                                "titulo": titulo,
                                "categoria": categoria,
                                "descricao_curta": descricao,
                                "cidade": cidade,
                                "estado": estado,
                                "nome_publico": nome_publico or identity.get("display_name"),
                                "whatsapp": whatsapp,
                                "regiao_atendimento": regiao,
                                "rota_entrega": rota,
                                "pedido_minimo_texto": pedido_min,
                                "retirada_local": retirada_local,
                                "entrega_sob_consulta": entrega_consulta,
                                "preco_valor": preco_valor,
                                "preco_texto": preco_texto,
                            },
                            user_id=identity.get("user_id", ""),
                        )
                        st.success(f"Anuncio publicado ({row.get('id')}).")

    fc1, fc2, fc3, fc4 = st.columns(4)
    cidade_f = fc1.text_input("Filtrar cidade", key="filtro_anuncio_cidade")
    estado_f = fc2.text_input("Filtrar estado", key="filtro_anuncio_estado")
    rota_f = fc3.checkbox("Somente com rota")
    retirada_f = fc4.checkbox("Somente retirada local")
    pedido_f = st.checkbox("Somente com pedido minimo informado")

    rows = store.list_anuncios(
        cidade=cidade_f,
        estado=estado_f,
        com_rota=rota_f,
        retirada_local=retirada_f,
        pedido_minimo=pedido_f,
        include_inactive=dev_mode,
    )
    if not rows:
        st.info("Nenhum anuncio encontrado.")
        return

    for row in rows:
        status = _to_text(row.get("status")) or STATUS_ACTIVE
        if status not in {STATUS_ACTIVE, STATUS_PAUSED}:
            continue
        with st.container(border=True):
            st.markdown(f"**{_to_text(row.get('titulo')) or '-'}**")
            st.caption(f"Categoria: {_to_text(row.get('categoria')) or '-'}")
            st.write(_to_text(row.get("descricao_curta")) or "-")

            p1, p2, p3 = st.columns(3)
            p1.caption(f"Preco: {_to_text(row.get('preco_texto')) or _to_text(row.get('preco_valor')) or 'Sob consulta'}")
            p2.caption(f"Cidade/UF: {_to_text(row.get('cidade'))}/{_to_text(row.get('estado'))}")
            p3.caption(f"Publicado ha: {formatar_tempo_publicacao(row.get('created_at'))}")

            l1, l2, l3 = st.columns(3)
            l1.caption(f"Regiao: {_to_text(row.get('regiao_atendimento')) or '-'}")
            l2.caption(f"Rota: {_to_text(row.get('rota_entrega')) or '-'}")
            l3.caption(f"Pedido minimo: {_to_text(row.get('pedido_minimo_texto')) or '-'}")
            st.caption(
                f"Retirada local: {'sim' if row.get('retirada_local') else 'nao'} | "
                f"Entrega sob consulta: {'sim' if row.get('entrega_sob_consulta') else 'nao'}"
            )

            score = calcular_score_anuncio(
                anuncio=type(
                    "AdObj",
                    (),
                    {
                        "visualizacoes_count": int(row.get("visualizacoes_count") or 0),
                        "cliques_contato_count": int(row.get("cliques_contato_count") or 0),
                        "created_at": row.get("created_at"),
                        "updated_at": row.get("updated_at"),
                        "regiao_atendimento": row.get("regiao_atendimento"),
                        "rota_entrega": row.get("rota_entrega"),
                        "pedido_minimo_texto": row.get("pedido_minimo_texto"),
                    },
                )()
            )
            st.caption(f"Score relevancia: {score}")

            contato_msg = mensagem_contato_anuncio()
            wa = _to_text(row.get("whatsapp"))
            if wa:
                st.link_button("Falar com anunciante", _wa_link(wa, contato_msg), use_container_width=True)


def _render_empresas_tab(store: CommercialModuleStore, identity: Dict[str, str], dev_mode: bool) -> None:
    st.markdown("### Empresas com atividade na plataforma")
    st.caption(
        "Indicadores baseados em atividade na plataforma, nao representando garantia, certificacao ou recomendacao."
    )

    with st.expander("Cadastrar/atualizar perfil da empresa", expanded=False):
        if store.is_blocked("user", identity.get("user_id", ""), "empresas"):
            st.error("Seu usuario esta bloqueado para alterar empresas neste modulo.")
        else:
            with st.form("form_empresa", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    nome_publico = st.text_input("Nome publico")
                    cidade = st.text_input("Cidade")
                    estado = st.text_input("Estado")
                    whatsapp = st.text_input("WhatsApp")
                    especialidades = st.text_input("Especialidades")
                with c2:
                    descricao = st.text_area("Descricao", height=90)
                    regiao = st.text_input("Regiao de atendimento")
                    rota = st.text_input("Rota de entrega")
                    pedido_min = st.text_input("Pedido minimo")
                    perfil_completo = st.toggle("Perfil completo")
                submitted = st.form_submit_button("Salvar empresa", use_container_width=True)
                if submitted:
                    if not nome_publico:
                        st.error("Nome publico e obrigatorio.")
                    else:
                        row = store.save_empresa(
                            {
                                "nome_publico": nome_publico,
                                "cidade": cidade,
                                "estado": estado,
                                "descricao": descricao,
                                "whatsapp": whatsapp,
                                "especialidades": especialidades,
                                "regiao_atendimento": regiao,
                                "rota_entrega": rota,
                                "pedido_minimo_texto": pedido_min,
                                "perfil_completo": perfil_completo,
                            },
                            user_id=identity.get("user_id", ""),
                        )
                        st.success(f"Empresa salva ({row.get('id')}).")

    f1, f2 = st.columns(2)
    cidade_f = f1.text_input("Filtrar cidade", key="empresa_cidade")
    estado_f = f2.text_input("Filtrar estado", key="empresa_estado")
    rows = store.list_empresas(cidade=cidade_f, estado=estado_f, include_inactive=dev_mode)
    if not rows:
        st.info("Nenhuma empresa cadastrada.")
        return

    for row in rows:
        status = _to_text(row.get("status")) or STATUS_ACTIVE
        if status not in {STATUS_ACTIVE, STATUS_PAUSED}:
            continue
        with st.container(border=True):
            st.markdown(f"**{_to_text(row.get('nome_publico')) or '-'}**")
            st.caption(f"{_to_text(row.get('cidade'))}/{_to_text(row.get('estado'))}")
            st.write(_to_text(row.get("descricao")) or "-")
            atividade, data_ref = build_empresa_activity_label(row)
            if data_ref:
                st.caption(f"Atividade: {atividade} (ultima referencia: {data_ref})")
            else:
                st.caption(f"Atividade: {atividade}")
            st.caption(
                f"Especialidades: {_to_text(row.get('especialidades')) or '-'} | "
                f"Regiao: {_to_text(row.get('regiao_atendimento')) or '-'} | "
                f"Rota: {_to_text(row.get('rota_entrega')) or '-'} | "
                f"Pedido minimo: {_to_text(row.get('pedido_minimo_texto')) or '-'}"
            )
            wa = _to_text(row.get("whatsapp"))
            if wa:
                st.link_button(
                    "Contato da empresa",
                    _wa_link(wa, "Ola, vi seu perfil no Uniao Motores e gostaria de mais informacoes."),
                    use_container_width=True,
                )


def _render_fornecedores_tab(store: CommercialModuleStore, identity: Dict[str, str], dev_mode: bool) -> None:
    st.markdown("### Fornecedores com logistica real")
    st.caption("Atende cidade/regiao, rota de entrega, pedido minimo e condicoes de retirada.")

    with st.expander("Cadastrar fornecedor", expanded=False):
        if store.is_blocked("user", identity.get("user_id", ""), "fornecedores"):
            st.error("Seu usuario esta bloqueado para cadastrar fornecedores.")
        else:
            with st.form("form_fornecedor", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    nome_publico = st.text_input("Nome publico")
                    cidade = st.text_input("Cidade base")
                    estado = st.text_input("Estado")
                    whatsapp = st.text_input("WhatsApp")
                    descricao = st.text_area("Descricao", height=90)
                with c2:
                    regiao = st.text_input("Atende (cidades/regiao)")
                    rota = st.text_input("Rota")
                    pedido_min = st.text_input("Pedido minimo")
                    retirada_local = st.toggle("Retirada local")
                    entrega_sob_consulta = st.toggle("Entrega sob consulta")
                submitted = st.form_submit_button("Salvar fornecedor", use_container_width=True)
                if submitted:
                    if not nome_publico or not cidade or not whatsapp:
                        st.error("Nome, cidade e WhatsApp sao obrigatorios.")
                    else:
                        row = store.save_fornecedor(
                            {
                                "nome_publico": nome_publico,
                                "cidade": cidade,
                                "estado": estado,
                                "descricao": descricao,
                                "whatsapp": whatsapp,
                                "regiao_atendimento": regiao,
                                "rota_entrega": rota,
                                "pedido_minimo_texto": pedido_min,
                                "retirada_local": retirada_local,
                                "entrega_sob_consulta": entrega_sob_consulta,
                            },
                            user_id=identity.get("user_id", ""),
                        )
                        st.success(f"Fornecedor salvo ({row.get('id')}).")

    ff1, ff2, ff3, ff4 = st.columns(4)
    cidade_f = ff1.text_input("Atende minha cidade", key="forn_cidade")
    rota_f = ff2.checkbox("Com rota definida")
    retirada_f = ff3.checkbox("Com retirada local")
    pedido_f = ff4.checkbox("Com pedido minimo")

    rows = store.list_fornecedores(
        cidade=cidade_f,
        com_rota=rota_f,
        retirada_local=retirada_f,
        pedido_minimo=pedido_f,
        include_inactive=dev_mode,
    )
    if not rows:
        st.info("Nenhum fornecedor encontrado.")
        return

    for row in rows:
        status = _to_text(row.get("status")) or STATUS_ACTIVE
        if status not in {STATUS_ACTIVE, STATUS_PAUSED}:
            continue
        with st.container(border=True):
            st.markdown(f"**{_to_text(row.get('nome_publico'))}**")
            st.write(_to_text(row.get("descricao")) or "-")
            st.caption(f"Atende: {_to_text(row.get('regiao_atendimento')) or _to_text(row.get('cidade'))}")
            st.caption(f"Rota: {_to_text(row.get('rota_entrega')) or '-'}")
            st.caption(f"Pedido minimo: {_to_text(row.get('pedido_minimo_texto')) or '-'}")
            st.caption(
                f"Retirada local: {'sim' if row.get('retirada_local') else 'nao'} | "
                f"Entrega: {'sob consulta' if row.get('entrega_sob_consulta') else 'sem informacao'}"
            )
            wa = _to_text(row.get("whatsapp"))
            if wa:
                st.link_button(
                    "Falar com fornecedor",
                    _wa_link(wa, "Ola, vi seu perfil no Uniao Motores e gostaria de solicitar atendimento."),
                    use_container_width=True,
                )


def _render_vagas_tab(store: CommercialModuleStore, identity: Dict[str, str], dev_mode: bool) -> None:
    st.markdown("### Vagas / Contratar")
    st.caption("Nao ha candidatura interna. Contato direto externo via WhatsApp.")

    with st.expander("Publicar vaga", expanded=False):
        if store.is_blocked("user", identity.get("user_id", ""), "vagas"):
            st.error("Seu usuario esta bloqueado para publicar vagas.")
        else:
            with st.form("form_vaga", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    nome_empresa = st.text_input("Empresa")
                    titulo = st.text_input("Titulo da vaga")
                    descricao = st.text_area("Descricao", height=90)
                    tipo_vaga = st.text_input("Tipo de vaga")
                with c2:
                    cidade = st.text_input("Cidade")
                    estado = st.text_input("Estado")
                    regime = st.text_input("Regime")
                    faixa = st.text_input("Faixa salarial (texto)")
                    whatsapp = st.text_input("WhatsApp para contato")
                submitted = st.form_submit_button("Publicar vaga", use_container_width=True)
                if submitted:
                    if not nome_empresa or not titulo or not cidade or not whatsapp:
                        st.error("Empresa, titulo, cidade e WhatsApp sao obrigatorios.")
                    else:
                        row = store.save_vaga(
                            {
                                "nome_empresa_snapshot": nome_empresa,
                                "titulo": titulo,
                                "descricao": descricao,
                                "cidade": cidade,
                                "estado": estado,
                                "tipo_vaga": tipo_vaga or "Operacional",
                                "regime": regime,
                                "faixa_salarial_texto": faixa,
                                "contato_whatsapp": whatsapp,
                            },
                            user_id=identity.get("user_id", ""),
                        )
                        st.success(f"Vaga publicada ({row.get('id')}).")

    fv1, fv2 = st.columns(2)
    cidade_f = fv1.text_input("Filtrar cidade", key="vaga_cidade")
    estado_f = fv2.text_input("Filtrar estado", key="vaga_estado")
    rows = store.list_vagas(cidade=cidade_f, estado=estado_f, include_inactive=dev_mode)
    if not rows:
        st.info("Nenhuma vaga publicada.")
        return

    for row in rows:
        status = _to_text(row.get("status")) or STATUS_ACTIVE
        if status not in {STATUS_ACTIVE, STATUS_PAUSED}:
            continue
        with st.container(border=True):
            st.markdown(f"**{_to_text(row.get('titulo')) or '-'}**")
            st.caption(f"Empresa: {_to_text(row.get('nome_empresa_snapshot')) or '-'}")
            st.write(_to_text(row.get("descricao")) or "-")
            st.caption(f"Cidade/UF: {_to_text(row.get('cidade'))}/{_to_text(row.get('estado'))}")
            st.caption(
                f"Tipo: {_to_text(row.get('tipo_vaga')) or '-'} | "
                f"Regime: {_to_text(row.get('regime')) or '-'} | "
                f"Faixa: {_to_text(row.get('faixa_salarial_texto')) or '-'}"
            )
            wa = _to_text(row.get("contato_whatsapp"))
            if wa:
                st.link_button("Contato da vaga", _wa_link(wa, mensagem_contato_vaga()), use_container_width=True)


def _render_termos_tab(store: CommercialModuleStore, identity: Dict[str, str]) -> None:
    _show_terms_block()

    with st.form("form_aceite_termos", clear_on_submit=True):
        contexto = st.selectbox(
            "Contexto do aceite",
            ["classificados", "empresas", "fornecedores", "vagas", "whatsapp_laudo"],
            index=0,
        )
        versao = st.text_input("Versao dos termos", value="v1.0")
        aceito = st.form_submit_button("Registrar aceite", use_container_width=True)
        if aceito:
            if not identity.get("user_id"):
                st.error("Usuario nao identificado para registrar aceite.")
            else:
                row = store.record_terms_acceptance(
                    user_id=identity.get("user_id", ""),
                    versao=versao,
                    contexto=contexto,
                    ip=resolve_client_ip(),
                )
                st.success(f"Aceite registrado em {row.get('created_at')}.")

    st.markdown("### Meus aceites registrados")
    rows = store.list_terms_acceptance(user_id=identity.get("user_id", ""))
    if not rows:
        st.caption("Nenhum aceite registrado ainda.")
        return
    for row in sorted(rows, key=lambda item: _to_text(item.get("created_at")), reverse=True)[:20]:
        st.caption(
            f"{_to_text(row.get('created_at'))} | versao={_to_text(row.get('versao'))} | "
            f"contexto={_to_text(row.get('contexto'))} | ip={_to_text(row.get('ip')) or '-'}"
        )


def render(ctx) -> None:
    flags = get_feature_flags()
    dev_mode = is_dev_mode()
    modules_enabled = flags.any_marketplace_enabled() or dev_mode

    if not modules_enabled:
        st.info("Modulo comercial desativado por flags. Ative no admin em ambiente development.")
        if st.button("Voltar para consulta", use_container_width=True):
            ctx.session.set_route(Route.CONSULTA)
            st.rerun()
        return

    identity = resolve_current_user_identity()
    isolated_mode = use_isolated_mode_for_module(ctx.supabase)
    store = CommercialModuleStore(ctx.supabase, force_local=isolated_mode)

    _render_header(dev_mode=dev_mode, isolated_mode=isolated_mode)

    tab_labels = []
    renderers = []
    if flags.enable_classificados or dev_mode:
        tab_labels.append("Classificados")
        renderers.append(lambda: _render_classificados_tab(store, identity, dev_mode))
    if flags.enable_empresas or dev_mode:
        tab_labels.append("Empresas")
        renderers.append(lambda: _render_empresas_tab(store, identity, dev_mode))
    if flags.enable_fornecedores or dev_mode:
        tab_labels.append("Fornecedores")
        renderers.append(lambda: _render_fornecedores_tab(store, identity, dev_mode))
    if flags.enable_vagas or dev_mode:
        tab_labels.append("Vagas")
        renderers.append(lambda: _render_vagas_tab(store, identity, dev_mode))
    tab_labels.append("Termos")
    renderers.append(lambda: _render_termos_tab(store, identity))

    tabs = st.tabs(tab_labels)
    for tab, render_fn in zip(tabs, renderers):
        with tab:
            render_fn()


def show(ctx) -> None:
    return render(ctx)

