from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import streamlit as st

from components.motor_rebobinagem_panel import render_rebobinagem_panel
from core.access_control import require_paid_access
from services.oficina_workshop import (
    build_calc_payload_from_parts,
    get_calculo,
    insert_calculo,
    list_calculos,
    parse_tags_csv,
    update_calculo,
    workshop_tables_available,
)


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _parse_int_list(raw: str) -> List[Any]:
    out: List[Any] = []
    for part in _to_text(raw).replace(";", ",").split(","):
        p = part.strip()
        if not p:
            continue
        try:
            out.append(int(p))
        except ValueError:
            out.append(p)
    return out


def _list_to_csv(nums: Any) -> str:
    if nums is None:
        return ""
    if isinstance(nums, list):
        return ", ".join(str(x) for x in nums)
    return _to_text(nums)


def _bench_test_state_key(scope: str) -> str:
    return f"bib_bench_tests_{scope}"


def _get_bench_tests(scope: str) -> List[Dict[str, Any]]:
    key = _bench_test_state_key(scope)
    value = st.session_state.get(key)
    if not isinstance(value, list):
        st.session_state[key] = []
        return st.session_state[key]  # type: ignore[return-value]
    return value


def _render_bench_tests_editor(scope: str) -> None:
    st.markdown("**Testes de bancada (opcional)**")
    st.caption(
        "Crie grupos como 'Teste corrente', 'Isolamento (megger)', 'Resistencia por fase' "
        "e adicione quantas linhas quiser (Teste 1/2/3...)."
    )

    tests = _get_bench_tests(scope)

    c1, c2, c3 = st.columns([1.2, 1.2, 1])
    with c1:
        group_name = st.text_input("Nome do grupo", value="", key=f"{scope}_bench_group_name")
    with c2:
        line_label = st.text_input("Nome do teste (ex.: Teste 1)", value="", key=f"{scope}_bench_line_label")
    with c3:
        line_value = st.text_input("Valor (ex.: 4A)", value="", key=f"{scope}_bench_line_value")

    a1, a2, a3 = st.columns([1, 1, 1])
    with a1:
        if st.button("Adicionar grupo", use_container_width=True, key=f"{scope}_bench_add_group"):
            name = _to_text(group_name) or "Grupo"
            tests.append({"nome": name, "linhas": []})
            st.session_state[_bench_test_state_key(scope)] = tests
            st.rerun()
    with a2:
        if st.button("Adicionar linha no grupo", use_container_width=True, key=f"{scope}_bench_add_line"):
            name = _to_text(group_name)
            if not name:
                st.warning("Informe o nome do grupo para adicionar a linha.")
            else:
                found = None
                for g in tests:
                    if _to_text(g.get("nome")).lower() == name.lower():
                        found = g
                        break
                if found is None:
                    found = {"nome": name, "linhas": []}
                    tests.append(found)
                linhas = found.get("linhas")
                if not isinstance(linhas, list):
                    linhas = []
                linhas.append(
                    {"teste": _to_text(line_label) or f"Teste {len(linhas)+1}", "valor": _to_text(line_value)}
                )
                found["linhas"] = linhas
                st.session_state[_bench_test_state_key(scope)] = tests
                st.rerun()
    with a3:
        st.checkbox("Confirmo limpar testes", key=f"{scope}_bench_confirm_clear")
        if st.button("Limpar testes", use_container_width=True, key=f"{scope}_bench_clear"):
            if st.session_state.get(f"{scope}_bench_confirm_clear"):
                st.session_state[_bench_test_state_key(scope)] = []
                st.rerun()
            else:
                st.warning("Marque a confirmação antes de limpar.")

    if not tests:
        st.info("Nenhum grupo de teste ainda.")
        return

    st.markdown("##### Grupos salvos (na edição atual)")
    for idx, g in enumerate(tests):
        nome = _to_text(g.get("nome")) or f"Grupo {idx+1}"
        linhas = g.get("linhas") if isinstance(g.get("linhas"), list) else []
        with st.expander(f"{nome} ({len(linhas)} linha(s))", expanded=False):
            if not linhas:
                st.caption("Sem linhas.")
            else:
                for j, ln in enumerate(linhas):
                    st.write(f"- **{_to_text(ln.get('teste')) or f'Teste {j+1}'}**: {_to_text(ln.get('valor')) or '—'}")
            r1, r2 = st.columns(2)
            with r1:
                if st.button("Remover última linha", use_container_width=True, key=f"{scope}_bench_pop_{idx}"):
                    if isinstance(linhas, list) and linhas:
                        linhas.pop()
                        g["linhas"] = linhas
                        st.session_state[_bench_test_state_key(scope)] = tests
                        st.rerun()
            with r2:
                if st.button("Remover grupo", use_container_width=True, key=f"{scope}_bench_del_{idx}"):
                    tests.pop(idx)
                    st.session_state[_bench_test_state_key(scope)] = tests
                    st.rerun()


def _render_bench_tests_view(payload: Dict[str, Any]) -> None:
    tests = payload.get("testes_bancada")
    if not isinstance(tests, list) or not tests:
        return
    st.markdown("#### Testes de bancada")
    for g in tests:
        if not isinstance(g, dict):
            continue
        nome = _to_text(g.get("nome")) or "Teste"
        linhas = g.get("linhas") if isinstance(g.get("linhas"), list) else []
        with st.expander(nome, expanded=False):
            if not linhas:
                st.caption("Sem linhas registradas.")
                continue
            for idx, ln in enumerate(linhas):
                if isinstance(ln, dict):
                    st.write(f"- **{_to_text(ln.get('teste')) or f'Teste {idx+1}'}**: {_to_text(ln.get('valor')) or '—'}")


def _render_mecanica_view(payload: Dict[str, Any]) -> None:
    m = payload.get("mecanica")
    if not isinstance(m, dict) or not any(_to_text(v) for v in m.values()):
        return
    st.markdown("#### Mecânica / montagem (referência)")
    with st.expander("Dados mecânicos salvos no cálculo", expanded=False):
        for k, v in m.items():
            st.write(f"- **{k}**: {_to_text(v) or '—'}")


def _hydrate_edit_session(rec: Dict[str, Any]) -> None:
    """Preenche `session_state` para o formulário de edição."""
    pl = rec.get("payload") if isinstance(rec.get("payload"), dict) else {}
    motor = pl.get("motor") if isinstance(pl.get("motor"), dict) else {}
    bp = pl.get("bobinagem_principal") if isinstance(pl.get("bobinagem_principal"), dict) else {}
    esq = pl.get("esquema") if isinstance(pl.get("esquema"), dict) else {}
    mec = pl.get("mecanica") if isinstance(pl.get("mecanica"), dict) else {}

    st.session_state["bib_e_titulo"] = _to_text(rec.get("titulo"))
    tags = rec.get("tags") or []
    st.session_state["bib_e_tags"] = ", ".join(str(t) for t in tags) if isinstance(tags, list) else _to_text(tags)
    st.session_state["bib_e_fases"] = _to_text(rec.get("fases")) or ""
    st.session_state["bib_e_cv"] = float(rec.get("potencia_cv") or 0.0)
    st.session_state["bib_e_rpm"] = int(rec.get("rpm") or 0)
    st.session_state["bib_e_polos"] = int(rec.get("polos") or 0)
    st.session_state["bib_e_tensao"] = float(rec.get("tensao_v") or 0.0)
    st.session_state["bib_e_ran"] = int(rec.get("ranhuras") or 0)

    st.session_state["bib_e_marca"] = _to_text(motor.get("marca"))
    st.session_state["bib_e_modelo"] = _to_text(motor.get("modelo"))
    st.session_state["bib_e_pot_txt"] = _to_text(motor.get("potencia"))
    st.session_state["bib_e_tensao_txt"] = _to_text(motor.get("tensao"))

    st.session_state["bib_e_passos"] = _list_to_csv(bp.get("passos"))
    st.session_state["bib_e_esp"] = _list_to_csv(bp.get("espiras"))
    fios = bp.get("fios")
    if isinstance(fios, list):
        st.session_state["bib_e_fios"] = ", ".join(str(x) for x in fios)
    else:
        st.session_state["bib_e_fios"] = _to_text(fios)
    st.session_state["bib_e_lig"] = _to_text(bp.get("ligacao"))
    st.session_state["bib_e_obs_bob"] = _to_text(bp.get("observacoes"))

    st.session_state["bib_e_ran_esq"] = _to_text(esq.get("ranhuras"))
    st.session_state["bib_e_dist"] = _to_text(esq.get("distribuicao_bobinas"))

    st.session_state["bib_e_notas"] = _to_text(rec.get("notas"))
    st.session_state["bib_e_rev_lbl"] = _to_text(rec.get("revision_label"))

    st.session_state["bib_e_mec_rl_drive"] = _to_text(mec.get("rolamento_drive"))
    st.session_state["bib_e_mec_rl_op"] = _to_text(mec.get("rolamento_oposto"))
    st.session_state["bib_e_mec_carcaca"] = _to_text(mec.get("carcaca_montagem"))
    st.session_state["bib_e_mec_acoplamento"] = _to_text(mec.get("acoplamento"))
    st.session_state["bib_e_mec_chaveta"] = _to_text(mec.get("chaveta_eixo"))
    st.session_state["bib_e_mec_obs"] = _to_text(mec.get("observacoes_mecanica"))

    st.session_state[_bench_test_state_key("edit")] = list(pl.get("testes_bancada") or [])


def _merge_payload_save(
    old_pl: Dict[str, Any],
    *,
    motor: Dict[str, Any],
    bp: Dict[str, Any],
    esq: Dict[str, Any],
    mec: Dict[str, Any],
    tests: List[Dict[str, Any]],
) -> Dict[str, Any]:
    aux = old_pl.get("bobinagem_auxiliar") if isinstance(old_pl.get("bobinagem_auxiliar"), dict) else {}
    merged = {**dict(old_pl or {})}
    np = build_calc_payload_from_parts(motor=motor, bobinagem_principal=bp, bobinagem_auxiliar=aux, esquema=esq)
    merged.update(np)
    if tests:
        merged["testes_bancada"] = tests
    else:
        merged.pop("testes_bancada", None)
    if mec and any(_to_text(v) for v in mec.values()):
        merged["mecanica"] = mec
    else:
        merged.pop("mecanica", None)
    return merged


def _collect_mecanica_from_state(prefix: str) -> Dict[str, str]:
    keys = {
        "rolamento_drive": f"{prefix}mec_rl_drive",
        "rolamento_oposto": f"{prefix}mec_rl_op",
        "carcaca_montagem": f"{prefix}mec_carcaca",
        "acoplamento": f"{prefix}mec_acoplamento",
        "chaveta_eixo": f"{prefix}mec_chaveta",
        "observacoes_mecanica": f"{prefix}mec_obs",
    }
    out: Dict[str, str] = {}
    for k, sk in keys.items():
        v = _to_text(st.session_state.get(sk))
        if v:
            out[k] = v
    return out


def render(ctx) -> None:
    if not require_paid_access("Biblioteca de calculos", client=ctx.supabase):
        return

    st.markdown("### Biblioteca de calculos (rebobinagem)")
    st.caption(
        "Guarde receitas reutilizaveis (passo, espiras, fio, ligacao). "
        "Pesquise, edite registos existentes ou crie revisoes. Dados mecanicos sao referencia de montagem."
    )

    if not workshop_tables_available(ctx.supabase):
        st.error(
            "Tabelas `rebobinagem_calculos` / `oficina_ordens_servico` indisponiveis neste banco. "
            "No Supabase Cloud, execute o SQL em `backend/migrations/20260418_0044_rebobinagem_calculos_oficina_os.sql`. "
            "No modo DEV local, reinicie o app para criar as tabelas SQLite."
        )
        return

    uid = _to_text(st.session_state.get("auth_user_id") or st.session_state.get("auth_user_email"))

    parent_id = st.session_state.get("bib_calc_revision_parent")
    if parent_id and st.button("Cancelar modo revisao", key="bib_cancel_rev"):
        st.session_state.pop("bib_calc_revision_parent", None)
        st.rerun()

    edit_id: Optional[str] = st.session_state.get("bib_edit_id")
    if edit_id and st.button("Cancelar edicao", key="bib_cancel_edit"):
        st.session_state.pop("bib_edit_id", None)
        st.session_state.pop(_bench_test_state_key("edit"), None)
        st.rerun()

    q = st.text_input("Buscar (titulo, tags, notas, conteudo)", value="", key="bib_q")
    rows = list_calculos(ctx.supabase, q=q, limit=100)
    st.caption(f"{len(rows)} registro(s) listados.")

    sel_options = {f"{r.get('id')} — {r.get('titulo', '')}": str(r.get("id")) for r in rows if r.get("id") is not None}
    pick = st.selectbox("Abrir registro", options=[""] + list(sel_options.keys()), key="bib_pick")
    selected_id = sel_options.get(pick) if pick else None

    if selected_id:
        rec = get_calculo(ctx.supabase, selected_id)
        if rec:
            st.markdown("#### Registro selecionado")
            c1, c2 = st.columns(2)
            with c1:
                st.write("**Titulo:**", rec.get("titulo"))
                st.write("**Fases:**", rec.get("fases") or "—")
                st.write("**Tags:**", rec.get("tags") or [])
            with c2:
                st.write("**Pot. (CV):**", rec.get("potencia_cv"))
                st.write("**RPM / polos / tensao / ranhuras:**", rec.get("rpm"), "/", rec.get("polos"), "/", rec.get("tensao_v"), "/", rec.get("ranhuras"))
            if rec.get("revision_of"):
                st.caption(f"Revisao de: `{rec.get('revision_of')}` — {rec.get('revision_label') or ''}")
            if rec.get("notas"):
                st.markdown(rec.get("notas"))

            payload = rec.get("payload") if isinstance(rec.get("payload"), dict) else {}
            _render_bench_tests_view(payload)
            _render_mecanica_view(payload)
            merged: Dict[str, Any] = {
                "motor": payload.get("motor") or {},
                "bobinagem_principal": payload.get("bobinagem_principal") or {},
                "bobinagem_auxiliar": payload.get("bobinagem_auxiliar") or {},
                "esquema": payload.get("esquema") or {},
            }
            with st.expander("Coerencia (read-only)", expanded=False):
                fake_row = {"dados_tecnicos_json": merged}
                render_rebobinagem_panel(fake_row, key_prefix=f"bib_rb_{selected_id}", title="Validacao rapida")

            dl = json.dumps(rec, ensure_ascii=False, indent=2, default=str)
            st.download_button("Baixar JSON", data=dl, file_name=f"calculo_{selected_id}.json", mime="application/json", key="bib_dl")

            b1, b2, b3 = st.columns(3)
            with b1:
                if st.button("Preparar nova revisao a partir deste", key="bib_rev_btn"):
                    st.session_state["bib_calc_revision_parent"] = str(rec.get("id"))
                    st.rerun()
            with b2:
                if st.button("Carregar para edicao", key="bib_load_edit"):
                    st.session_state["bib_edit_id"] = str(rec.get("id"))
                    _hydrate_edit_session(rec)
                    st.rerun()
            with b3:
                pass

    if edit_id:
        st.markdown("---")
        st.markdown("#### Editar registro")
        st.caption(f"Alterando id `{edit_id}`. Salvar grava no mesmo registro.")
        _render_bench_tests_editor("edit")

        with st.form("bib_edit_calc"):
            titulo_e = st.text_input("Titulo", key="bib_e_titulo")
            tags_e = st.text_input("Tags (virgula)", key="bib_e_tags")
            fases_e = st.selectbox("Fases", ["", "Trifasico", "Monofasico"], key="bib_e_fases")
            n1, n2, n3, n4 = st.columns(4)
            with n1:
                pot_cv_e = st.number_input("Potencia (CV)", min_value=0.0, step=0.5, key="bib_e_cv")
            with n2:
                rpm_e = st.number_input("RPM", min_value=0, step=10, key="bib_e_rpm")
            with n3:
                polos_e = st.number_input("Polos", min_value=0, step=2, key="bib_e_polos")
            with n4:
                tensao_e = st.number_input("Tensao nominal (V)", min_value=0.0, step=10.0, key="bib_e_tensao")
            ranh_e = st.number_input("Ranhuras", min_value=0, step=1, key="bib_e_ran")
            st.markdown("**Motor**")
            em1, em2 = st.columns(2)
            with em1:
                marca_e = st.text_input("Marca", key="bib_e_marca")
                modelo_e = st.text_input("Modelo", key="bib_e_modelo")
            with em2:
                pot_txt_e = st.text_input("Potencia texto (opcional)", key="bib_e_pot_txt")
                tensao_txt_e = st.text_input("Tensao texto", key="bib_e_tensao_txt")
            st.markdown("**Bobinagem principal**")
            passos_e = st.text_area("Passos (virgula)", key="bib_e_passos")
            esp_e = st.text_area("Espiras (virgula)", key="bib_e_esp")
            fios_e = st.text_area("Fios", key="bib_e_fios")
            lig_e = st.text_input("Ligacao", key="bib_e_lig")
            obs_b_e = st.text_area("Obs. bobinagem", key="bib_e_obs_bob")
            st.markdown("**Esquema**")
            ranh_esq_e = st.text_input("Ranhuras (esquema)", key="bib_e_ran_esq")
            dist_e = st.text_input("Distribuicao bobinas", key="bib_e_dist")
            st.markdown("**Mecanica / montagem (opcional)**")
            mx1, mx2 = st.columns(2)
            with mx1:
                st.text_input("Rolamento lado acoplamento", key="bib_e_mec_rl_drive")
                st.text_input("Rolamento lado oposto", key="bib_e_mec_rl_op")
            with mx2:
                st.text_input("Carcaça / flange (B3, B5...)", key="bib_e_mec_carcaca")
                st.text_input("Acoplamento / carga", key="bib_e_mec_acoplamento")
            st.text_input("Chaveta / ponteira eixo", key="bib_e_mec_chaveta")
            st.text_area("Observacoes mecanicas", key="bib_e_mec_obs")
            notas_e = st.text_area("Notas da biblioteca", key="bib_e_notas")
            rev_lbl_e = st.text_input("Rotulo revisao (metadata)", key="bib_e_rev_lbl")
            save_e = st.form_submit_button("Salvar alteracoes", use_container_width=True)

        if save_e and edit_id:
            old = get_calculo(ctx.supabase, edit_id)
            old_pl = old.get("payload") if isinstance(old.get("payload"), dict) else {}
            motor: Dict[str, Any] = {
                "marca": _to_text(marca_e),
                "modelo": _to_text(modelo_e),
                "potencia": _to_text(pot_txt_e) or (str(pot_cv_e) if pot_cv_e else ""),
                "rpm": str(int(rpm_e)) if rpm_e else "",
                "polos": str(int(polos_e)) if polos_e else "",
                "tensao": _to_text(tensao_txt_e) or (str(tensao_e) if tensao_e else ""),
                "fases": _to_text(fases_e),
            }
            bp: Dict[str, Any] = {
                "passos": _parse_int_list(passos_e),
                "espiras": _parse_int_list(esp_e),
                "fios": [x.strip() for x in _to_text(fios_e).split(",") if x.strip()],
                "ligacao": _to_text(lig_e),
                "observacoes": _to_text(obs_b_e),
            }
            esq: Dict[str, Any] = {
                "ranhuras": _to_text(ranh_esq_e) or (str(int(ranh_e)) if ranh_e else ""),
                "distribuicao_bobinas": _to_text(dist_e),
            }
            mec_e = _collect_mecanica_from_state("bib_e_")
            tests_e = _get_bench_tests("edit")
            merged_pl = _merge_payload_save(old_pl, motor=motor, bp=bp, esq=esq, mec=mec_e, tests=tests_e)
            try:
                update_calculo(
                    ctx.supabase,
                    edit_id,
                    titulo=titulo_e or "Sem titulo",
                    notas=notas_e,
                    tags=parse_tags_csv(tags_e),
                    fases=fases_e,
                    potencia_cv=float(pot_cv_e) if pot_cv_e else None,
                    rpm=int(rpm_e) if rpm_e else None,
                    polos=int(polos_e) if polos_e else None,
                    tensao_v=float(tensao_e) if tensao_e else None,
                    ranhuras=int(ranh_e) if ranh_e else None,
                    payload=merged_pl,
                    revision_label=rev_lbl_e,
                )
                st.success("Registro atualizado.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))

    if edit_id:
        st.stop()

    st.markdown("---")
    st.markdown("#### Novo calculo (ou revisao)")
    if parent_id:
        st.info(f"Modo revisao: novo registro apontara para `{parent_id}`.")

    st.divider()
    _render_bench_tests_editor("novo")

    with st.form("bib_novo_calc"):
        titulo = st.text_input("Titulo (ex.: WEG 10CV 4 polos 220/380)", key="bib_titulo")
        tags_raw = st.text_input("Tags (separadas por virgula)", value="", key="bib_tags")
        fases = st.selectbox("Fases", ["", "Trifasico", "Monofasico"], key="bib_fases")
        n1, n2, n3, n4 = st.columns(4)
        with n1:
            pot_cv = st.number_input("Potencia (CV)", min_value=0.0, value=0.0, step=0.5, key="bib_cv")
        with n2:
            rpm = st.number_input("RPM", min_value=0, value=0, step=10, key="bib_rpm")
        with n3:
            polos = st.number_input("Polos", min_value=0, value=0, step=2, key="bib_polos")
        with n4:
            tensao = st.number_input("Tensao nominal (V)", min_value=0.0, value=0.0, step=10.0, key="bib_tensao")
        ranhuras = st.number_input("Ranhuras", min_value=0, value=0, step=1, key="bib_ran")
        st.markdown("**Motor (placa / referencia)**")
        m1, m2 = st.columns(2)
        with m1:
            marca = st.text_input("Marca", key="bib_marca")
            modelo = st.text_input("Modelo", key="bib_modelo")
        with m2:
            pot_txt = st.text_input("Potencia texto (opcional)", key="bib_pot_txt")
            tensao_txt = st.text_input("Tensao texto (ex.: 220/380)", key="bib_tensao_txt")

        st.markdown("**Bobinagem principal**")
        passos_raw = st.text_area("Passos (numeros separados por virgula)", value="", key="bib_passos")
        espiras_raw = st.text_area("Espiras (numeros separados por virgula)", value="", key="bib_esp")
        fios_raw = st.text_area("Fios (lista, ex.: 18,18 ou AWG20)", value="", key="bib_fios")
        ligacao = st.text_input("Ligacao", key="bib_lig")
        obs_bob = st.text_area("Observacoes bobinagem", value="", key="bib_obs_bob")
        st.markdown("**Esquema**")
        ranh_esq = st.text_input("Ranhuras (esquema, texto)", key="bib_ran_esq")
        dist = st.text_input("Distribuicao bobinas", key="bib_dist")
        st.markdown("**Mecanica / montagem (opcional)**")
        mcol1, mcol2 = st.columns(2)
        with mcol1:
            st.text_input("Rolamento lado acoplamento", key="bib_mec_rl_drive")
            st.text_input("Rolamento lado oposto", key="bib_mec_rl_op")
        with mcol2:
            st.text_input("Carcaça / flange (B3, B5...)", key="bib_mec_carcaca")
            st.text_input("Acoplamento / carga", key="bib_mec_acoplamento")
        st.text_input("Chaveta / ponteira eixo", key="bib_mec_chaveta")
        st.text_area("Observacoes mecanicas", key="bib_mec_obs")
        notas = st.text_area("Notas da biblioteca", value="", key="bib_notas")
        rev_label = st.text_input("Rotulo da revisao (se revisao)", value="", key="bib_rev_lbl")
        save = st.form_submit_button("Salvar na biblioteca", use_container_width=True)

    if save:
        motor = {
            "marca": _to_text(marca),
            "modelo": _to_text(modelo),
            "potencia": _to_text(pot_txt) or (str(pot_cv) if pot_cv else ""),
            "rpm": str(int(rpm)) if rpm else "",
            "polos": str(int(polos)) if polos else "",
            "tensao": _to_text(tensao_txt) or (str(tensao) if tensao else ""),
            "fases": _to_text(fases),
        }
        bp = {
            "passos": _parse_int_list(passos_raw),
            "espiras": _parse_int_list(espiras_raw),
            "fios": [x.strip() for x in _to_text(fios_raw).split(",") if x.strip()],
            "ligacao": _to_text(ligacao),
            "observacoes": _to_text(obs_bob),
        }
        esq = {
            "ranhuras": _to_text(ranh_esq) or (str(int(ranhuras)) if ranhuras else ""),
            "distribuicao_bobinas": _to_text(dist),
        }
        mec_n = _collect_mecanica_from_state("bib_")
        tests_state = _get_bench_tests("novo")
        payload = _merge_payload_save({}, motor=motor, bp=bp, esq=esq, mec=mec_n, tests=tests_state)
        try:
            out = insert_calculo(
                ctx.supabase,
                titulo=titulo or "Sem titulo",
                notas=notas,
                tags=parse_tags_csv(tags_raw),
                fases=fases,
                potencia_cv=float(pot_cv) if pot_cv else None,
                rpm=int(rpm) if rpm else None,
                polos=int(polos) if polos else None,
                tensao_v=float(tensao) if tensao else None,
                ranhuras=int(ranhuras) if ranhuras else None,
                payload=payload,
                revision_of=str(parent_id) if parent_id else None,
                revision_label=rev_label,
                created_by=uid or None,
            )
            st.success(f"Salvo com id `{out.get('id')}`.")
            st.session_state.pop("bib_calc_revision_parent", None)
            st.session_state.pop(_bench_test_state_key("novo"), None)
            st.rerun()
        except Exception as exc:
            st.error(str(exc))


def show(ctx):
    return render(ctx)
