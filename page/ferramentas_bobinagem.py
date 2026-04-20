"""Ferramentas de oficina: equivalencia de fio, espiras e tensao (rebobinagem)."""

from __future__ import annotations

import streamlit as st

from core.navigation import Route
from core.streamlit_perf import maybe_fragment, pop_page_ctx_pack, stash_page_ctx
from core.ui_feedback import mrw_render_banner_zone
from services.motor_rebobinagem.wire_gauge import AWG_SOLID_CU_MM2, awg_integer_to_mm2
from services.oficina_rebobinagem_equiv import (
    area_total_mm2,
    equivalent_num_parallel,
    parallel_branch_current_split,
    series_total_turns,
    suggest_awg_combos_for_area,
    turns_for_voltage_ratio,
)


def _awg_options() -> list[str]:
    return [str(x) for x in sorted(AWG_SOLID_CU_MM2.keys())]


def render(ctx) -> None:
    stash_page_ctx(ctx)
    _ferramentas_bobinagem_fragment()


@maybe_fragment
def _ferramentas_bobinagem_fragment() -> None:
    mrw_render_banner_zone()
    pack = pop_page_ctx_pack()
    ctx = pack.get("ctx")
    if ctx is None:
        return

    st.markdown("### Ferramentas de bobinagem")
    st.caption(
        "Equivalencia aproximada de **fio (AWG)**, **espiras vs tensao** e notas sobre **serie/paralelo**. "
        "Nao substitui calculo de projeto, norma de isolamento nem ensaio a vazio/carga."
    )

    t1, t2, t3, t4 = st.tabs(
        [
            "1) Trocar fio (mesma secao)",
            "2) Tensao e espiras",
            "3) Serie e paralelo (notas)",
            "4) Sugerir bitolas (area alvo)",
        ]
    )

    with t1:
        st.markdown("**Cenario tipico:** um fio (ou N em paralelo) de AWG conhecido; nao tem a mesma bitola a mao.")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            n_par = st.number_input("Fios em paralelo (vias)", min_value=1, max_value=16, value=1, step=1, key="fb_npar")
        with c2:
            awg_from = st.selectbox("AWG original", _awg_options(), index=11, key="fb_awg_from")  # 19
        with c3:
            awg_to = st.selectbox("AWG a usar", _awg_options(), index=13, key="fb_awg_to")  # 21
        with c4:
            st.caption("Secao de referencia (cobre nu)")

        af = int(awg_from)
        ato = int(awg_to)
        a0 = awg_integer_to_mm2(af)
        a1 = awg_integer_to_mm2(ato)
        tot = area_total_mm2(int(n_par), af)
        st.info(
            f"Secao alvo: **{tot:.4f} mm2** (≈ {n_par} x AWG {af} ~ {a0:g} mm2 cada) "
            f"→ fio de substituicao: AWG {ato} ≈ **{a1:g} mm2** / via."
        )
        eq = equivalent_num_parallel(int(n_par), af, ato)
        if eq:
            st.success(
                f"Para aproximar a **mesma area de cobre** com AWG {ato}: use **{eq['n_parallel_ceil']}** "
                f"condutor(es) em paralelo (piso: {eq['n_parallel_floor']}; area ~{eq['area_ceil_mm2']:.4f} mm2 com teto, "
                f"~{eq['area_floor_mm2']:.4f} mm2 com piso). Razao: **{eq['ratio']:.3f}** vias equivalentes."
            )
        st.warning(
            "Ajuste ranhura, esmagamento, isolante e arrefecimento — esta ferramenta so trata de **secao aproximada**."
        )

    with t2:
        st.markdown("**Lei ideal:** espiras de referencia proporcionais a **tensao** (ligacao e fluxo admitidos const.)")
        r1 = st.columns(3)
        r2 = st.columns(3)
        presets = [("110", "127"), ("220", "240"), ("380", "400"), ("220", "380"), ("110", "220"), ("200", "380")]
        for i, (la, lb) in enumerate(presets):
            row = r1 if i < 3 else r2
            with row[i % 3]:
                if st.button(f"{la} V → {lb} V", key=f"fb_vpreset_{i}"):
                    st.session_state["fb_v_old"] = float(la)
                    st.session_state["fb_v_new"] = float(lb)
        v1, v2, v3 = st.columns(3)
        with v1:
            n0 = st.number_input("Espiras de referencia (contagem)", min_value=1.0, value=100.0, step=1.0, key="fb_n0")
        with v2:
            v_old = st.number_input("Tensao de referencia (V)", min_value=1.0, value=220.0, step=1.0, key="fb_v_old")
        with v3:
            v_new = st.number_input("Tensao nova (V)", min_value=1.0, value=380.0, step=1.0, key="fb_v_new")
        tnv = turns_for_voltage_ratio(n0, v_old, v_new)
        if tnv is not None:
            fator = v_new / v_old
            st.success(
                f"Espiras aproximadas: **{tnv:.1f}**  (N2 = N1 x {fator:.4f}). "
                f"Ex.: de **{v_old:.0f}** V para **{v_new:.0f}** V, multiplique a contagem de espiras pelo factor **{fator:.4f}**."
            )
        st.caption("Estrela/triangulo, fator de bobina e inducao reais alteram o resultado: valide com desenho e leis locais.")

    with t3:
        st.markdown(
            """
- **Espiras em serie no mesmo caminho (mesma corrente):** a soma de espiras no *ramo* importa para a f.e.m. (ex.: bobinas em cadeia na mesma fase).
- **Ramos em paralelo (K grupos identicos em paralelo):** a corrente total reparte-se de forma aproximada; cada ramo deve levar a **bitola/paralelo** adequado para **I_remo / K** (e verificar a ligacao, passo e tensao de isolamento).
- Trocar mentalmente *serie* por *paralelo* de **enrolamentos de fase** sem recalcular o projeto muda a tensao e o desbalanco — nao basta trocar nomes: use o separador *Tensao e espiras* e o desenho original.
            """
        )
        a1, a2, a3 = st.columns(3)
        with a1:
            t_a = st.number_input("Espiras grupo A", value=0.0, key="fb_sera")
        with a2:
            t_b = st.number_input("Espiras grupo B (serie)", value=0.0, key="fb_serb")
        with a3:
            t_c = st.number_input("Espiras grupo C (serie)", value=0.0, key="fb_serc")
        s = [x for x in (t_a, t_b, t_c) if x and x > 0]
        if s:
            st.caption(f"Soma (serie no mesmo fio de fase): **{series_total_turns(s):.1f}** espiras.")
        i_tot = st.number_input("Corrente total de fase (A) — so para repartir", value=0.0, key="fb_itot")
        k_br = st.number_input("Numero de ramos em paralelo (K)", min_value=1, max_value=12, value=2, key="fb_kbr")
        if i_tot > 0 and k_br >= 1:
            i_b = parallel_branch_current_split(i_tot, k_br)
            st.caption(f"Se os ramos forem simetricos: corrente **aproximada** por ramo = **{i_b:.3f}** A (I total / {k_br}).")

    with t4:
        st.markdown("Indique uma **area alvo (mm2)**; sugerimos combinacoes AWG x fios em paralelo.")
        tgt = st.number_input("Area alvo (mm2 de cobre)", min_value=0.01, value=0.653, format="%.4f", key="fb_tgt")
        maxp = st.slider("Max. condutores em paralelo a considerar", 1, 8, 4, key="fb_maxp")
        sugs = suggest_awg_combos_for_area(tgt, max_parallel=maxp)
        if sugs:
            st.dataframe(sugs, use_container_width=True, hide_index=True)
        st.caption("As linhas com menor `rel_error` aproximam-se melhor da area pedida.")

    cba, cbb = st.columns(2)
    with cba:
        if st.button("Voltar ao guia oficina", use_container_width=True, key="fb_guia"):
            ctx.session.set_route(Route.GUIA_OFICINA)
            st.rerun()
    with cbb:
        if st.button("Ir a Consulta", use_container_width=True, key="fb_consulta"):
            ctx.session.set_route(Route.CONSULTA)
            st.rerun()


def show(ctx) -> None:
    return render(ctx)
