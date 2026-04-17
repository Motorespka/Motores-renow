from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel, ConfigDict, Field


class SettingsMeResponse(BaseModel):
    ui_prefs: Dict[str, Any] = Field(default_factory=dict)
    feature_flags: Dict[str, Any] = Field(default_factory=dict)


class SettingsMeUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    ui_prefs: Dict[str, Any] | None = None
    feature_flags: Dict[str, Any] | None = None


class MessageResponse(BaseModel):
    ok: bool = True
    message: str = "success"

