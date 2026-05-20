#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-Brain: rodízio round-robin de chaves Gemini (14+ keys no .env).

Uso:
    from config.api_manager import get_gemini_api_manager
    mgr = get_gemini_api_manager()
    alias, key = mgr.acquire_key()
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Optional

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from services.gemini_key_manager import GeminiKeyManager, mask_key  # noqa: E402

_DEFAULT_STATUS = _REPO_ROOT / "logs" / "gemini_keys_status.json"

# Modelos 1.5 descontinuados na API v1beta — mapear para 2.5 suportados.
_LEGACY_MODEL_MAP: dict[str, str] = {
    "gemini-1.5-pro": "gemini-2.5-flash",
    "gemini-1.5-pro-latest": "gemini-2.5-flash",
    "gemini-1.5-flash": "gemini-2.5-flash-lite",
    "gemini-1.5-flash-latest": "gemini-2.5-flash-lite",
    "gemini-1.5-flash-8b": "gemini-2.5-flash-lite",
    "gemini-pro": "gemini-2.5-flash",
}

_singleton: Optional["GeminiApiManager"] = None


def _read_secret_or_env(*names: str) -> str:
    for name in names:
        v = (os.environ.get(name) or "").strip()
        if v:
            return v
    try:
        import streamlit as st  # type: ignore

        sec = getattr(st, "secrets", None)
        if sec is not None:
            for name in names:
                raw = sec.get(name, None)  # type: ignore[attr-defined]
                if raw is not None and str(raw).strip():
                    return str(raw).strip()
    except Exception:
        pass
    return ""


def _normalize_model_name(name: str) -> str:
    n = (name or "").strip()
    if not n:
        return ""
    return _LEGACY_MODEL_MAP.get(n, n)


def resolve_gemini_models() -> tuple[str, str]:
    """Primario + fallback a partir de Secrets/.env (ignora GEMINI_MODEL legado 1.5 se houver DEFAULT)."""
    primary = _read_secret_or_env("GEMINI_MODEL_DEFAULT", "GEMINI_MODEL") or "gemini-2.5-flash"
    fallback = _read_secret_or_env("GEMINI_MODEL_FALLBACK") or "gemini-2.5-flash-lite"
    primary = _normalize_model_name(primary) or "gemini-2.5-flash"
    fallback = _normalize_model_name(fallback) or "gemini-2.5-flash-lite"
    if fallback == primary:
        fallback = "gemini-2.5-flash-lite" if primary != "gemini-2.5-flash-lite" else "gemini-2.5-flash"
    return primary, fallback


def _model_chain(primary: str, fallback: str) -> list[str]:
    chain: list[str] = []
    for m in (primary, fallback, "gemini-2.5-flash", "gemini-2.5-flash-lite"):
        m = _normalize_model_name(m)
        if m and m not in chain:
            chain.append(m)
    return chain


def _is_model_not_found(exc: BaseException) -> bool:
    msg = (str(exc) or "").lower()
    return "404" in msg or "not found" in msg or "is not supported" in msg


_DEFAULT_PRIMARY, _DEFAULT_FALLBACK = resolve_gemini_models()


class GeminiApiManager:
    """Facade round-robin sobre GeminiKeyManager para campo e batch."""

    def __init__(
        self,
        *,
        status_path: Path | None = None,
        model: str = "",
        max_calls_per_key_per_run: int = 0,
    ) -> None:
        self._status_path = Path(status_path or _DEFAULT_STATUS)
        prim, fb = resolve_gemini_models()
        if model:
            prim = _normalize_model_name(model) or prim
        self._model_primary = prim
        self._model_fallback = fb
        self._km = GeminiKeyManager(
            status_path=str(self._status_path),
            model_default=prim,
            enabled=True,
        )
        self._km.configure_rotation(strategy="round_robin", max_calls_per_key_per_run=max_calls_per_key_per_run)
        self._loaded = False

    def ensure_loaded(self) -> int:
        if not self._loaded or not self._km._keys_by_alias:
            n = self._km.load_keys()
            self._km.configure_rotation(strategy="round_robin")
            self._loaded = True
            return n
        return len(self._km._keys_by_alias)

    def acquire_key(self, *, require_ok: bool = False) -> tuple[str, str]:
        """Retorna (alias, api_key) ou levanta RuntimeError se esgotado."""
        self.ensure_loaded()
        got = self._km.get_available_key(require_status_ok=require_ok)
        if not got:
            info = self._km.explain_no_keys(require_status_ok=require_ok)
            raise RuntimeError(f"Sem chaves Gemini disponiveis: {info.get('reason')}")
        return got

    def report_success(self, alias: str) -> None:
        self._km.mark_success(alias)

    def report_failure(self, alias: str, exc: BaseException) -> None:
        self._km.mark_failure(alias, exc)

    def call_json(self, prompt: str, *, require_ok: bool = False, max_attempts: int = 3) -> dict[str, Any]:
        """Chama Gemini com resposta JSON; round-robin entre chaves."""
        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise RuntimeError(f"google-generativeai nao instalado: {exc}") from exc

        from services.gemini_ocr_fallback import _extract_json

        self.ensure_loaded()
        last_err: Optional[Exception] = None
        gen_cfg = {"response_mime_type": "application/json", "temperature": 0.1}
        models = _model_chain(self._model_primary, self._model_fallback)

        for _ in range(max(1, max_attempts)):
            try:
                alias, key = self.acquire_key(require_ok=require_ok)
            except RuntimeError as exc:
                raise RuntimeError(str(exc)) from exc
            genai.configure(api_key=key)
            for model_name in models:
                try:
                    gm = genai.GenerativeModel(model_name)
                    resp = gm.generate_content(prompt, generation_config=gen_cfg)
                    text = (getattr(resp, "text", None) or "").strip()
                    data = _extract_json(text)
                    self._km.model_default = model_name
                    self._model_primary = model_name
                    self._km.mark_success(alias)
                    self._km.save_status()
                    if isinstance(data, dict):
                        return data
                    raise ValueError("Resposta Gemini nao e um objeto JSON.")
                except Exception as exc:
                    last_err = exc
                    if _is_model_not_found(exc):
                        continue
                    self._km.mark_failure(alias, exc)
                    self._km.save_status()
                    break
            else:
                if last_err is not None:
                    self._km.mark_failure(alias, last_err)
                    self._km.save_status()
                continue
        raise RuntimeError(f"Gemini falhou apos {max_attempts} tentativa(s): {last_err}")

    def status_summary(self) -> dict[str, Any]:
        self.ensure_loaded()
        n = len(self._km._keys_by_alias)
        explain = self._km.explain_no_keys(require_status_ok=False)
        keys_preview = []
        for alias in sorted(self._km._keys_by_alias.keys())[:20]:
            st = self._km._status.get(alias)
            keys_preview.append(
                {
                    "alias": alias,
                    "masked": mask_key(self._km._keys_by_alias.get(alias, "")),
                    "status": st.status if st else "unknown",
                    "eligible_ok": bool(st.eligible_ok) if st else False,
                    "cooldown_until": st.cooldown_until if st else "",
                }
            )
        return {
            "total_keys": n,
            "rotation": "round_robin",
            "model": self._km.model_default,
            "model_primary": self._model_primary,
            "model_fallback": self._model_fallback,
            "status_path": str(self._status_path),
            "eligible_now": explain.get("counts", {}).get("eligible_now", 0),
            "keys_preview": keys_preview,
        }


def get_gemini_api_manager(*, reload: bool = False) -> GeminiApiManager:
    global _singleton
    if _singleton is None or reload:
        max_per = int(os.environ.get("GEMINI_MAX_CALLS_PER_KEY_PER_RUN", "0") or "0")
        _singleton = GeminiApiManager(max_calls_per_key_per_run=max_per)
    return _singleton
