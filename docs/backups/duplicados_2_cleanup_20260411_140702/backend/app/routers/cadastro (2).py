from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.core.config import get_settings
from app.dependencies.auth import require_cadastro
from app.integrations.supabase_rest import SupabaseRestClient
from app.schemas.cadastro import (
    CadastroAnalyzeResponse,
    CadastroSaveRequest,
    CadastroSaveResponse,
)
from app.services.access_service import AccessContext
from app.services.cadastro_service import (
    CadastroService,
    CadastroValidationError,
    UploadedImage,
)

router = APIRouter(prefix="/cadastro", tags=["cadastro"])


def _service() -> CadastroService:
    settings = get_settings()
    gateway = SupabaseRestClient(settings)
    return CadastroService(settings=settings, gateway=gateway)


@router.post("/analyze", response_model=CadastroAnalyzeResponse)
async def analyze_uploads(
    files: List[UploadFile] = File(...),
    access: AccessContext = Depends(require_cadastro),
) -> CadastroAnalyzeResponse:
    service = _service()
    uploaded: List[UploadedImage] = []
    for item in files:
        data = await item.read()
        uploaded.append(
            UploadedImage(
                file_name=item.filename or "upload.bin",
                mime_type=item.content_type or "",
                data=data,
            )
        )
    try:
        result = await service.analyze(access=access, files=uploaded)
        return CadastroAnalyzeResponse(**result)
    except CadastroValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Falha na analise: {exc}")


@router.post("/save", response_model=CadastroSaveResponse)
async def save_cadastro(
    payload: CadastroSaveRequest,
    access: AccessContext = Depends(require_cadastro),
) -> CadastroSaveResponse:
    service = _service()
    try:
        result = await service.save(
            access=access,
            normalized_data=payload.normalized_data,
            file_names=payload.file_names,
            image_urls=payload.image_urls,
        )
        return CadastroSaveResponse(**result)
    except CadastroValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Falha ao salvar: {exc}")

