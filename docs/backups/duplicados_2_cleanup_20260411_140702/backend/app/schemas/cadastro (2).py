from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, ConfigDict, Field


class CadastroAnalyzeResponse(BaseModel):
    ok: bool = True
    message: str = "Analise concluida."
    file_count: int = 0
    file_names: List[str] = Field(default_factory=list)
    image_urls: List[str] = Field(default_factory=list)
    normalized_data: Dict[str, Any] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


class CadastroSaveRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    normalized_data: Dict[str, Any]
    file_names: List[str] = Field(default_factory=list)
    image_urls: List[str] = Field(default_factory=list)


class CadastroSaveResponse(BaseModel):
    ok: bool = True
    message: str = "Motor salvo com sucesso."
    strategy: str = ""
    inserted_id: str | int | None = None
    warnings: List[str] = Field(default_factory=list)

