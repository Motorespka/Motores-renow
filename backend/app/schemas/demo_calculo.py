from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field


class DemoCalculoStats(BaseModel):
    oficial_total: int
    file_complete: int
    with_geometry: int
    index_generated_at: str = ""


class DemoCalculoSuggestRequest(BaseModel):
    diametro_mm: float = Field(..., gt=0)
    pacote_mm: float = Field(..., gt=0)
    carcaca: str = ""
    passo: str = ""
    ligacao: str = ""
    fio_engenheiro: str = ""
    espiras_engenheiro: str = ""


class ProportionalHitOut(BaseModel):
    sha: str
    arquivo_rel: str
    score: float
    diametro_mm: float
    pacote_mm: float
    carcaca: str
    passo_principal: str
    ligacao: str
    fio_principal: str
    espiras_historico: float
    espiras_calculadas: float
    fio_sugerido_awg: Optional[float] = None
    pacote_ratio: float = 0.0
    area_ratio: float = 0.0


class DemoCalculoSuggestResponse(BaseModel):
    modo_processamento: str = "proporcional"
    gemini_usado: bool = False
    sugestao_espira: Optional[float] = None
    sugestao_fio_awg: Optional[float] = None
    justificativa_tecnica: str = ""
    alerta_risco: str = ""
    dispersao_espiras: float = 0.0
    espiras_media_top5: Optional[float] = None
    fio_medio_top5: Optional[float] = None
    passo_moda: str = ""
    carcaca_moda: str = ""
    n_file_catalog: int
    n_matches: int
    top_matches: List[ProportionalHitOut]
    validation_status: str = ""
    validation_message: str = ""


class DemoCalculoSaveRequest(BaseModel):
    diametro_mm: float
    pacote_mm: float
    carcaca: str
    passo: str
    ligacao: str = ""
    fio_principal: str
    espiras_principal: str
    observacoes: str = ""


class DemoCalculoSaveResponse(BaseModel):
    ok: bool = True
    sha256_arquivo: str
    arquivo_rel: str
    saved_at: str
    message: str


class GeminiKeysStatusResponse(BaseModel):
    total_keys: int
    rotation: str
    eligible_now: int
    model: str
    keys_preview: List[dict[str, Any]]
