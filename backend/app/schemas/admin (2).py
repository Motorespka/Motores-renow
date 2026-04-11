from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class AdminUserSummary(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    email: str | None = None
    username: str | None = None
    nome: str | None = None
    role: str | None = None
    plan: str | None = None
    ativo: bool | None = None


class AdminUserUpdatePayload(BaseModel):
    username: Optional[str] = None
    nome: Optional[str] = None
    role: Optional[Literal["user", "admin"]] = None
    plan: Optional[str] = None
    ativo: Optional[bool] = None


class MessageResponse(BaseModel):
    ok: bool = True
    message: str = Field(default="success")

