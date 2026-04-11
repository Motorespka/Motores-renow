from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Dict

import streamlit as st


FEATURE_OVERRIDES_KEY = "_feature_flags_overrides"


def _as_bool(value, default: bool = False) -> bool:
    if value is None:
        return bool(default)
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on", "sim"}


def _read_secret_or_env(name: str, default: bool) -> bool:
    try:
        if name in st.secrets:
            return _as_bool(st.secrets.get(name), default=default)
    except Exception:
        pass
    return _as_bool(os.environ.get(name), default=default)


@dataclass(frozen=True)
class FeatureFlags:
    enable_dev_env: bool = False
    enable_dev_banner: bool = True
    enable_laudo_pro: bool = False
    enable_whatsapp_send: bool = False
    enable_classificados: bool = False
    enable_empresas: bool = False
    enable_vagas: bool = False
    enable_fornecedores: bool = False

    def any_marketplace_enabled(self) -> bool:
        return any(
            [
                self.enable_classificados,
                self.enable_empresas,
                self.enable_vagas,
                self.enable_fornecedores,
            ]
        )


def _base_flags() -> FeatureFlags:
    return FeatureFlags(
        enable_dev_env=_read_secret_or_env("ENABLE_DEV_ENV", False),
        enable_dev_banner=_read_secret_or_env("ENABLE_DEV_BANNER", True),
        enable_laudo_pro=_read_secret_or_env("ENABLE_LAUDO_PRO", False),
        enable_whatsapp_send=_read_secret_or_env("ENABLE_WHATSAPP_SEND", False),
        enable_classificados=_read_secret_or_env("ENABLE_CLASSIFICADOS", False),
        enable_empresas=_read_secret_or_env("ENABLE_EMPRESAS", False),
        enable_vagas=_read_secret_or_env("ENABLE_VAGAS", False),
        enable_fornecedores=_read_secret_or_env("ENABLE_FORNECEDORES", False),
    )


def _read_overrides() -> Dict[str, bool]:
    raw = st.session_state.get(FEATURE_OVERRIDES_KEY)
    if not isinstance(raw, dict):
        return {}
    out: Dict[str, bool] = {}
    for key, value in raw.items():
        if isinstance(key, str):
            out[key] = _as_bool(value, default=False)
    return out


def get_feature_flags() -> FeatureFlags:
    base = _base_flags()
    overrides = _read_overrides()
    if not overrides:
        return base

    payload = {
        "enable_dev_env": base.enable_dev_env,
        "enable_dev_banner": base.enable_dev_banner,
        "enable_laudo_pro": base.enable_laudo_pro,
        "enable_whatsapp_send": base.enable_whatsapp_send,
        "enable_classificados": base.enable_classificados,
        "enable_empresas": base.enable_empresas,
        "enable_vagas": base.enable_vagas,
        "enable_fornecedores": base.enable_fornecedores,
    }
    for key, value in overrides.items():
        if key in payload:
            payload[key] = bool(value)
    return FeatureFlags(**payload)


def list_flag_names() -> list[str]:
    return [
        "enable_dev_env",
        "enable_dev_banner",
        "enable_laudo_pro",
        "enable_whatsapp_send",
        "enable_classificados",
        "enable_empresas",
        "enable_vagas",
        "enable_fornecedores",
    ]


def set_feature_override(flag_name: str, enabled: bool) -> None:
    name = str(flag_name or "").strip()
    if name not in list_flag_names():
        return
    overrides = _read_overrides()
    overrides[name] = bool(enabled)
    st.session_state[FEATURE_OVERRIDES_KEY] = overrides


def clear_feature_overrides() -> None:
    st.session_state.pop(FEATURE_OVERRIDES_KEY, None)

