from __future__ import annotations

import re
from typing import Any, Dict

import streamlit as st


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _humanize_identifier(value: str) -> str:
    txt = _to_text(value)
    if not txt:
        return ""

    # Remove sufixo comum gerado por fallback de username: nome_abcdef1234
    txt = re.sub(r"_([0-9a-f]{8,})$", "", txt, flags=re.IGNORECASE)
    txt = txt.replace("_", " ").replace(".", " ").strip()
    if not txt:
        return ""
    return txt[:1].upper() + txt[1:]


def resolve_current_user_identity() -> Dict[str, str]:
    profile = st.session_state.get("auth_user_profile")
    if not isinstance(profile, dict):
        profile = {}

    user_id = _to_text(st.session_state.get("auth_user_id") or profile.get("id"))
    email = _to_text(st.session_state.get("auth_user_email") or profile.get("email")).lower()
    username = _to_text(profile.get("username"))
    nome = _to_text(profile.get("nome"))

    email_local = ""
    if email and "@" in email:
        email_local = email.split("@", 1)[0].strip()

    display_name = (
        nome
        or _humanize_identifier(username)
        or _humanize_identifier(email_local)
        or _humanize_identifier(user_id)
        or "Usuario"
    )

    return {
        "user_id": user_id,
        "email": email,
        "username": username,
        "nome": nome,
        "display_name": display_name,
    }
