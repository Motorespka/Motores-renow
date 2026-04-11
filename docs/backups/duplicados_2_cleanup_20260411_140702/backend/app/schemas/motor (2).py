from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field


class MotorRecord(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str | int | None = None
    marca: str | None = None
    modelo: str | None = None
    potencia: str | None = None
    rpm: str | None = None


class MotorListResponse(BaseModel):
    mode: str = Field(description="teaser|full")
    total: int
    items: List[MotorRecord]


class MotorDetailResponse(BaseModel):
    item: MotorRecord
    raw: Dict[str, Any]

