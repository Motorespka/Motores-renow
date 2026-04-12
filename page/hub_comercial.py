from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List
from urllib.parse import quote_plus

import streamlit as st

from core.development_mode import is_dev_mode, resolve_client_ip, use_isolated_mode_for_module
from core.feature_flags import get_feature_flags
from core.navigation import Route
from core.user_identity import resolve_current_user_identity
from services.modulo_comercial import (
    CHAT_TERM_CONTEXT,
    CHAT_TERM_VERSION,
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
    "Os contatos publicos exibidos nos anuncios/perfis sao informados pelo proprio anunciante.",
    "No chat interno, e proibido compartilhar dados pessoais, financeiros ou sensiveis.",
]

CHAT_MAX_LENGTH = 500
LEGAL_REPO_BASE_URL = "https://github.com/Motorespka/Motores-renow/blob/main"
LEGAL_DOCS = [
    ("Termo de Uso do Modulo Comercial e Chat (v1.0)", "docs/legal/TERMO_USO_CHAT_MARKETPLACE_V1_0.md"),
    ("Politica de Privacidade e Retencao (v1.0)", "docs/legal/POLITICA_PRIVACIDADE_RETENCAO_V1_0.md"),
]

SENSITIVE_CHAT_PATTERNS = [
    ("e-mail", re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)),
    ("telefone", re.compile(r"(?:\+?\d[\d\s\-\(\)]{7,}\d)")),
    ("cpf", re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}\-?\d{2}\b")),
    ("cnpj", re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}\-?\d{2}\b")),
    ("link externo", re.compile(r"(https?://|www\.)", re.IGNORECASE)),
    ("dados de endereco", re.compile(r"\b(rua|avenida|av\.|bairro|cep)\b", re.IGNORECASE)),
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


def _legal_doc_url(relative_path: str) -> str:
    rel = str(relative_path or "").replace("\\", "/").lstrip("/")
    return f"{LEGAL_REPO_BASE_URL}/{rel}"


@st.cache_data(show_spinner=False)
def _load_legal_doc(relative_path: str) -> str:
    rel = str(relative_path or "").replace("\\", "/").lstrip("/")
    doc_path = Path(__file__).resolve().parents[1] / rel
    try:
        return doc_path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _render_legal_doc_links(section_key: str) -> None:
    st.caption("Documentos legais:")
    for label, rel in LEGAL_DOCS:
        st.markdown(f"- [{label}]({_legal_doc_url(rel)})")

    cols = st.columns(2)
    for idx, (label, rel) in enumerate(LEGAL_DOCS):
        content = _load_legal_doc(rel)
        if not content:
            continue
        cols[idx % 2].download_button(
            label=f"Baixar {label}",
            data=content,
            file_name=Path(rel).name,
            mime="text/markdown",
            key=f"{section_key}_legal_dl_{idx}",
            use_container_width=True,
        )


def _chat_terms_accepted(store: CommercialModuleStore, identity: Dict[str, str]) -> bool:
    return store.has_terms_acceptance(
        user_id=identity.get("user_id", ""),
        contexto=CHAT_TERM_CONTEXT,
        versao=CHAT_TERM_VERSION,
    )


def _detect_sensitive_chat_payload(text: str) -> List[str]:
    content = _to_text(text)
    if not content:
        return []
    flags: List[str] = []
    for label, pattern in SENSITIVE_CHAT_PATTERNS:
        if pattern.search(content):
            flags.append(label)
    return flags


def _start_secure_chat(
    *,
    store: CommercialModuleStore,
    identity: Dict[str, str],
    contexto_tipo: str,
    contexto_id: str,
    contexto_titulo: str,
    owner_user_id: str,
    owner_nome: str,
) -> None:
    if not _chat_terms_accepted(store, identity):
        st.warning("Para abrir chat, aceite primeiro os termos na aba Chat.")
        return

    requester_id = identity.get("user_id", "")
    if not _to_text(requester_id):
        st.error("Usuario nao autenticado para abrir chat.")
        return

    thread = store.get_or_create_chat_thread(
        contexto_tipo=contexto_tipo,
        contexto_id=contexto_id,
        contexto_titulo=contexto_titulo,
        requester_user_id=requester_id,
        requester_nome=identity.get("display_name", ""),
        owner_user_id=owner_user_id,
        owner_nome=owner_nome,
    )
    if not thread:
        st.warning("Nao foi possivel abrir chat para este item.")
        return

    st.session_state["hub_chat_thread_id"] = thread.get("id")
    st.success("Chat pronto. Abra a aba Chat para continuar com seguranca.")


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
            owner_id = _to_text(row.get("user_id"))
            if owner_id and owner_id != _to_text(identity.get("user_id")):
                if st.button(
                    "Abrir chat seguro",
                    key=f"chat_anuncio_{_to_text(row.get('id'))}",
                    use_container_width=True,
                ):
                    _start_secure_chat(
                        store=store,
                        identity=identity,
                        contexto_tipo="anuncio",
                        contexto_id=_to_text(row.get("id")),
                        contexto_titulo=_to_text(row.get("titulo")) or "Anuncio",
                        owner_user_id=owner_id,
                        owner_nome=_to_text(row.get("nome_publico")) or "Anunciante",
                    )


def _render_empresas_tab(store: CommercialModuleStore, identity: Dict[str, str], dev_mode: bool) -> None:
    st.markdown("### Empresas com atividade na plataforma")
    st.caption(
        "Indicadores baseados em atividade na plataforma, nao representando garantia, certificacao ou recomendacao."
    )
    my_empresa = store.find_user_empresa(identity.get("user_id", ""))

    with st.expander("Cadastrar/atualizar perfil da empresa", expanded=False):
        if store.is_blocked("user", identity.get("user_id", ""), "empresas"):
            st.error("Seu usuario esta bloqueado para alterar empresas neste modulo.")
        else:
            with st.form("form_empresa", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    nome_publico = st.text_input("Nome publico", value=_to_text((my_empresa or {}).get("nome_publico")))
                    cidade = st.text_input("Cidade", value=_to_text((my_empresa or {}).get("cidade")))
                    estado = st.text_input("Estado", value=_to_text((my_empresa or {}).get("estado")))
                    whatsapp = st.text_input("WhatsApp comercial", value=_to_text((my_empresa or {}).get("whatsapp")))
                    especialidades = st.text_input(
                        "Especialidades",
                        value=_to_text((my_empresa or {}).get("especialidades")),
                    )
                with c2:
                    descricao = st.text_area("Descricao", value=_to_text((my_empresa or {}).get("descricao")), height=90)
                    regiao = st.text_input(
                        "Regiao de atendimento",
                        value=_to_text((my_empresa or {}).get("regiao_atendimento")),
                    )
                    perfil_completo = st.toggle(
                        "Perfil completo",
                        value=bool((my_empresa or {}).get("perfil_completo")),
                    )
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
                                "perfil_completo": perfil_completo,
                            },
                            user_id=identity.get("user_id", ""),
                        )
                        st.success(f"Empresa salva ({row.get('id')}).")
                        my_empresa = row

    if my_empresa:
        st.markdown("#### Equipe da empresa")
        st.caption("Cadastre somente nomes profissionais e funcao. Nao use dados pessoais sensiveis.")
        with st.form("form_membro_empresa", clear_on_submit=True):
            m1, m2 = st.columns(2)
            with m1:
                nome_profissional = st.text_input("Nome profissional")
            with m2:
                funcao = st.selectbox("Funcao", ["atendente", "vendedor", "tecnico", "admin"], index=0)
            add_membro = st.form_submit_button("Adicionar membro", use_container_width=True)
            if add_membro:
                if not _to_text(nome_profissional):
                    st.error("Informe o nome profissional.")
                else:
                    row = store.save_empresa_membro(
                        {
                            "empresa_id": _to_text(my_empresa.get("id")),
                            "nome_profissional": nome_profissional,
                            "funcao": funcao,
                        },
                        created_by_user_id=identity.get("user_id", ""),
                    )
                    st.success(f"Membro salvo ({row.get('id')}).")

        membros = store.list_empresa_membros(empresa_id=_to_text(my_empresa.get("id")), include_inactive=True)
        if not membros:
            st.caption("Nenhum membro cadastrado.")
        for membro in membros:
            status = _to_text(membro.get("status")) or STATUS_ACTIVE
            with st.container(border=True):
                st.caption(
                    f"{_to_text(membro.get('nome_profissional')) or '-'} | "
                    f"funcao={_to_text(membro.get('funcao')) or '-'} | status={status}"
                )
                cbtn1, cbtn2 = st.columns(2)
                if status == STATUS_ACTIVE:
                    if cbtn1.button("Pausar", key=f"membro_pause_{_to_text(membro.get('id'))}", use_container_width=True):
                        store.set_empresa_membro_status(_to_text(membro.get("id")), STATUS_PAUSED)
                        st.rerun()
                    if cbtn2.button("Remover", key=f"membro_remove_{_to_text(membro.get('id'))}", use_container_width=True):
                        store.set_empresa_membro_status(_to_text(membro.get("id")), "removed")
                        st.rerun()
                elif status == STATUS_PAUSED:
                    if cbtn1.button("Reativar", key=f"membro_resume_{_to_text(membro.get('id'))}", use_container_width=True):
                        store.set_empresa_membro_status(_to_text(membro.get("id")), STATUS_ACTIVE)
                        st.rerun()
                    if cbtn2.button("Remover", key=f"membro_remove_{_to_text(membro.get('id'))}", use_container_width=True):
                        store.set_empresa_membro_status(_to_text(membro.get("id")), "removed")
                        st.rerun()

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
            membros_count = len(store.list_empresa_membros(empresa_id=_to_text(row.get("id")), include_inactive=False))
            st.caption(
                f"Especialidades: {_to_text(row.get('especialidades')) or '-'} | "
                f"Regiao: {_to_text(row.get('regiao_atendimento')) or '-'} | "
                f"Membros ativos: {membros_count}"
            )
            wa = _to_text(row.get("whatsapp"))
            if wa:
                st.link_button(
                    "Contato da empresa",
                    _wa_link(wa, "Ola, vi seu perfil no Uniao Motores e gostaria de mais informacoes."),
                    use_container_width=True,
                )
            owner_id = _to_text(row.get("user_id"))
            if owner_id and owner_id != _to_text(identity.get("user_id")):
                if st.button("Abrir chat seguro", key=f"chat_empresa_{_to_text(row.get('id'))}", use_container_width=True):
                    _start_secure_chat(
                        store=store,
                        identity=identity,
                        contexto_tipo="empresa",
                        contexto_id=_to_text(row.get("id")),
                        contexto_titulo=_to_text(row.get("nome_publico")) or "Empresa",
                        owner_user_id=owner_id,
                        owner_nome=_to_text(row.get("nome_publico")) or "Empresa",
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
            owner_id = _to_text(row.get("user_id"))
            if owner_id and owner_id != _to_text(identity.get("user_id")):
                if st.button(
                    "Abrir chat seguro",
                    key=f"chat_fornecedor_{_to_text(row.get('id'))}",
                    use_container_width=True,
                ):
                    _start_secure_chat(
                        store=store,
                        identity=identity,
                        contexto_tipo="fornecedor",
                        contexto_id=_to_text(row.get("id")),
                        contexto_titulo=_to_text(row.get("nome_publico")) or "Fornecedor",
                        owner_user_id=owner_id,
                        owner_nome=_to_text(row.get("nome_publico")) or "Fornecedor",
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
            owner_id = _to_text(row.get("user_id"))
            if owner_id and owner_id != _to_text(identity.get("user_id")):
                if st.button("Abrir chat seguro", key=f"chat_vaga_{_to_text(row.get('id'))}", use_container_width=True):
                    _start_secure_chat(
                        store=store,
                        identity=identity,
                        contexto_tipo="vaga",
                        contexto_id=_to_text(row.get("id")),
                        contexto_titulo=_to_text(row.get("titulo")) or "Vaga",
                        owner_user_id=owner_id,
                        owner_nome=_to_text(row.get("nome_empresa_snapshot")) or "Empresa",
                    )


def _find_by_id(rows: List[Dict[str, str]], row_id: str) -> Dict[str, str] | None:
    target = _to_text(row_id)
    if not target:
        return None
    for row in rows:
        if _to_text(row.get("id")) == target:
            return row
    return None


def _resolve_external_chat_link(store: CommercialModuleStore, thread: Dict[str, str]) -> tuple[str, str]:
    context_type = _to_text(thread.get("contexto_tipo"))
    context_id = _to_text(thread.get("contexto_id"))

    if context_type == "fornecedor":
        row = _find_by_id(store.list_fornecedores(include_inactive=True), context_id)
        wa = _to_text((row or {}).get("whatsapp"))
        if wa:
            return _wa_link(wa, "Ola, vamos continuar nosso atendimento fora da plataforma."), "Ir para WhatsApp do fornecedor"

    if context_type == "anuncio":
        row = _find_by_id(store.list_anuncios(include_inactive=True), context_id)
        wa = _to_text((row or {}).get("whatsapp"))
        if wa:
            return _wa_link(wa, mensagem_contato_anuncio()), "Ir para WhatsApp do anunciante"

    if context_type == "vaga":
        row = _find_by_id(store.list_vagas(include_inactive=True), context_id)
        wa = _to_text((row or {}).get("contato_whatsapp"))
        if wa:
            return _wa_link(wa, mensagem_contato_vaga()), "Ir para WhatsApp da vaga"

    if context_type == "empresa":
        row = _find_by_id(store.list_empresas(include_inactive=True), context_id)
        wa = _to_text((row or {}).get("whatsapp"))
        if wa:
            return _wa_link(wa, "Ola, vamos continuar nosso atendimento fora da plataforma."), "Ir para WhatsApp da empresa"

    return "", ""


def _render_chat_tab(store: CommercialModuleStore, identity: Dict[str, str], dev_mode: bool) -> None:
    st.markdown("### Chat seguro (triagem)")
    st.caption("Use o chat apenas para triagem comercial. Negociacao final e fechamento devem ocorrer fora da plataforma.")

    st.warning(
        "A plataforma nao se responsabiliza por negociacoes, pagamentos, contratacoes, entregas, garantias ou promessas feitas entre usuarios."
    )
    st.info("E proibido compartilhar e-mail, telefone, CPF/CNPJ, links externos, enderecos e quaisquer dados sensiveis no chat.")

    user_id = _to_text(identity.get("user_id"))
    if not user_id:
        st.error("Usuario nao autenticado para usar chat.")
        return

    if not _chat_terms_accepted(store, identity):
        st.markdown("#### Aceite obrigatorio para liberar o chat")
        st.write("- Conversas sao apenas para triagem inicial.")
        st.write("- Nao envie dados pessoais, dados financeiros ou links externos.")
        st.write("- O fechamento deve ocorrer fora da plataforma, por sua conta e risco.")
        _render_legal_doc_links("chat_aceite")
        with st.form("chat_terms_required", clear_on_submit=False):
            confirm_terms = st.checkbox("Li e aceito o Termo de Uso do Modulo Comercial e Chat (v1.0).")
            confirm_privacy = st.checkbox("Li e concordo com a Politica de Privacidade e Retencao (v1.0).")
            submit_terms = st.form_submit_button("Aceitar e liberar chat", use_container_width=True)
            if submit_terms:
                if not (confirm_terms and confirm_privacy):
                    st.error("Confirme os dois aceites para liberar o chat.")
                else:
                    store.record_terms_acceptance(
                        user_id=user_id,
                        versao=CHAT_TERM_VERSION,
                        contexto=CHAT_TERM_CONTEXT,
                        ip="",
                    )
                    st.success("Termo aceito. Chat liberado.")
                    st.rerun()
        return

    threads = store.list_chat_threads_for_user(user_id=user_id, include_inactive=dev_mode)
    if not threads:
        st.info("Nenhuma conversa ainda. Abra um chat seguro a partir de anuncios, empresas, fornecedores ou vagas.")
        return

    thread_ids = [_to_text(row.get("id")) for row in threads if _to_text(row.get("id"))]
    if not thread_ids:
        st.info("Nenhuma conversa valida encontrada.")
        return

    preferred_thread = _to_text(st.session_state.get("hub_chat_thread_id"))
    if preferred_thread not in thread_ids:
        preferred_thread = thread_ids[0]
    default_index = thread_ids.index(preferred_thread)

    labels = []
    for row in threads:
        titulo = _to_text(row.get("contexto_titulo")) or _to_text(row.get("contexto_tipo")) or "Conversa"
        ultimo = _to_text(row.get("last_message_at")) or _to_text(row.get("updated_at")) or "-"
        labels.append(f"{titulo} | ultima atividade: {ultimo}")

    selected_thread_id = st.selectbox(
        "Conversas",
        options=thread_ids,
        index=default_index,
        format_func=lambda tid: labels[thread_ids.index(tid)],
    )
    st.session_state["hub_chat_thread_id"] = selected_thread_id
    selected_thread = store.get_chat_thread(thread_id=selected_thread_id, user_id=user_id)
    if not selected_thread:
        st.warning("Conversa indisponivel.")
        return

    external_url, external_label = _resolve_external_chat_link(store, selected_thread)
    if external_url:
        st.link_button(external_label, external_url, use_container_width=True)

    st.markdown("#### Mensagens")
    messages = store.list_chat_messages(thread_id=selected_thread_id, user_id=user_id, limit=200)
    if not messages:
        st.caption("Ainda sem mensagens nesta conversa.")
    for row in messages:
        sender = _to_text(row.get("sender_display_name")) or "Usuario"
        ts = _to_text(row.get("created_at")) or "-"
        text = _to_text(row.get("message_text"))
        with st.container(border=True):
            st.caption(f"{sender} | {ts}")
            st.write(text or "-")

    with st.form("chat_send_form", clear_on_submit=True):
        msg = st.text_area("Mensagem", height=90, max_chars=CHAT_MAX_LENGTH)
        submit_msg = st.form_submit_button("Enviar mensagem", use_container_width=True)
        if submit_msg:
            content = _to_text(msg)
            if not content:
                st.error("Digite uma mensagem.")
            else:
                sensitive = _detect_sensitive_chat_payload(content)
                if sensitive:
                    itens = ", ".join(sorted(set(sensitive)))
                    st.error(f"Mensagem bloqueada por conter possivel dado sensivel: {itens}.")
                else:
                    row = store.save_chat_message(
                        thread_id=selected_thread_id,
                        sender_user_id=user_id,
                        sender_display_name=identity.get("display_name", ""),
                        message_text=content,
                    )
                    if not row:
                        st.error("Nao foi possivel enviar a mensagem.")
                    else:
                        st.success("Mensagem enviada.")
                        st.rerun()


def _render_termos_tab(store: CommercialModuleStore, identity: Dict[str, str]) -> None:
    _show_terms_block()
    _render_legal_doc_links("termos_tab")

    with st.form("form_aceite_termos", clear_on_submit=True):
        contexto = st.selectbox(
            "Contexto do aceite",
            ["classificados", "empresas", "fornecedores", "vagas", "whatsapp_laudo", CHAT_TERM_CONTEXT],
            index=0,
        )
        versao = st.text_input("Versao dos termos", value="v1.0")
        aceito = st.form_submit_button("Registrar aceite", use_container_width=True)
        if aceito:
            if not identity.get("user_id"):
                st.error("Usuario nao identificado para registrar aceite.")
            else:
                ip_value = ""
                if contexto != CHAT_TERM_CONTEXT:
                    ip_value = resolve_client_ip()
                row = store.record_terms_acceptance(
                    user_id=identity.get("user_id", ""),
                    versao=versao,
                    contexto=contexto,
                    ip=ip_value,
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
            f"contexto={_to_text(row.get('contexto'))} | ip={'oculto' if _to_text(row.get('ip')) else '-'}"
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
    if flags.enable_chat or dev_mode:
        tab_labels.append("Chat")
        renderers.append(lambda: _render_chat_tab(store, identity, dev_mode))
    tab_labels.append("Termos")
    renderers.append(lambda: _render_termos_tab(store, identity))

    tabs = st.tabs(tab_labels)
    for tab, render_fn in zip(tabs, renderers):
        with tab:
            render_fn()


def show(ctx) -> None:
    return render(ctx)

