from __future__ import annotations

from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


ConferenceStatus = Literal["pending", "approved", "rejected"]


class ConferenceRecord(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    motor_id: str
    created_by: str
    status: ConferenceStatus = "pending"
    confidence: int = 0
    diff: Dict[str, Any] = Field(default_factory=dict)
    decision: Dict[str, Any] = Field(default_factory=dict)
    decided_by: Optional[str] = None
    decided_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ConferenceListResponse(BaseModel):
    total: int = 0
    items: list[ConferenceRecord] = Field(default_factory=list)


class ConferenceDiffResponse(BaseModel):
    ok: bool = True
    record: ConferenceRecord


class ConferenceDecisionRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    approved: bool
    reason: str = ""
    notes: str = ""


class ConferenceDecisionResponse(BaseModel):
    ok: bool = True
    record: ConferenceRecord

