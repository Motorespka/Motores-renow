from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


DiagnosticStatus = Literal["pending", "running", "done", "error"]


class DiagnosticRecord(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    motor_id: str
    created_by: str
    status: DiagnosticStatus = "pending"
    score: int = 0
    summary: str = ""
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    evidence: Dict[str, Any] = Field(default_factory=dict)
    error: str = ""
    created_at: str | None = None
    updated_at: str | None = None


class DiagnosticListResponse(BaseModel):
    total: int = 0
    items: List[DiagnosticRecord] = Field(default_factory=list)


class DiagnosticRunRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    motor_id: Optional[str] = None
    limit: int = 10


class DiagnosticRunResponse(BaseModel):
    ok: bool = True
    message: str = "Diagnostico gerado."
    created: int = 0
    items: List[DiagnosticRecord] = Field(default_factory=list)

