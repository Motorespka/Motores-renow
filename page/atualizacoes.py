from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st

from core.development_mode import is_dev_mode
from core.streamlit_perf import maybe_fragment, pop_page_ctx_pack, stash_page_ctx
from core.ui_feedback import mrw_render_banner_zone

# Fonte única com o Next.js (Vercel): editar `data/releases.json` e fazer deploy do ficheiro no Streamlit Cloud.

_RELEASES_PATH = Path(__file__).resolve().parent.parent / "data" / "releases.json"


def _releases_changelogs() -> tuple[List[Dict[str, Any]], List[Dict[str, Any]], str]:
    """
    Le `data/releases.json` **sem** `st.cache_data`: evita lista de atualizacoes presa a versao antiga
    em sessoes longas / deploy onde o cache por mtime nao invalida como esperado.
    Retorna (changelog, dev_preview, meta_caption).
    """
    path = _RELEASES_PATH
    meta = f"`{path.name}`"
    if not path.is_file():
        return (
            [
                {
                    "versao": "ERRO",
                    "data": "-",
                    "titulo": "Ficheiro data/releases.json em falta no repositório",
                    "adicoes": [
                        "Inclua `data/releases.json` no deploy (Streamlit Cloud inclui ficheiros do repo).",
                        "Opcional: `python scripts/export_releases_json.py` para validar o JSON.",
                    ],
                    "correcoes": [],
                }
            ],
            [],
            meta + " em falta",
        )
    try:
        txt = path.read_text(encoding="utf-8")
        raw = json.loads(txt)
    except Exception:
        return (
            [
                {
                    "versao": "ERRO",
                    "data": "-",
                    "titulo": "Ficheiro data/releases.json inválido (JSON)",
                    "adicoes": [],
                    "correcoes": [],
                }
            ],
            [],
            meta + " invalido",
        )
    main = raw.get("changelog") if isinstance(raw.get("changelog"), list) else []
    dev = raw.get("dev_preview_changelog") if isinstance(raw.get("dev_preview_changelog"), list) else []
    try:
        mts = path.stat().st_mtime
        mhuman = datetime.fromtimestamp(mts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        top = str((main[0] or {}).get("versao") or "?") if main else "?"
        meta = f"Versao mais recente no ficheiro: **{top}** · ficheiro alterado em **{mhuman}** (servidor)."
    except Exception:
        meta = "Leitura directa do ficheiro (sem cache de pagina)."
    return main, dev, meta


def _render_release_card(item: Dict[str, object], preview: bool = False) -> None:
    versao = str(item.get("versao") or "-")
    data = str(item.get("data") or "-")
    titulo = str(item.get("titulo") or "Atualizacao")
    adicoes = item.get("adicoes") or []
    correcoes = item.get("correcoes") or []
    badge = "PREVIEW DEVELOPMENT | " if preview else ""

    st.markdown(
        f"""
        <div class="data-panel" style="margin-bottom: 14px;">
            <div class="data-label">{badge}{versao} | {data}</div>
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
    stash_page_ctx(_ctx)
    _atualizacoes_page_fragment()


@maybe_fragment
def _atualizacoes_page_fragment() -> None:
    mrw_render_banner_zone()
    if pop_page_ctx_pack().get("ctx") is None:
        return

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

    changelog, dev_preview, releases_meta = _releases_changelogs()
    st.caption(releases_meta)

    if is_dev_mode() and dev_preview:
        st.warning("MODO DEVELOPMENT: voce esta visualizando versoes de teste antes da liberacao geral.")
        for item in dev_preview:
            _render_release_card(item, preview=True)
        st.markdown("### Releases gerais")

    for item in changelog:
        _render_release_card(item)


def show(ctx) -> None:
    return render(ctx)
