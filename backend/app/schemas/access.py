from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class AccessProfile(BaseModel):
    model_config = ConfigDict(extra="allow")

    user_id: str
    email: str
    username: str = ""
    nome: str = ""
    display_name: str = "Usuario"
    role: str = ""
    plan: str = "free"
    ativo: bool = False
    is_admin: bool = False
    cadastro_allowed: bool = False
    tier: str = "anon"
    source: str = "none"


class MeResponse(BaseModel):
    authenticated: bool
    profile: AccessProfile
