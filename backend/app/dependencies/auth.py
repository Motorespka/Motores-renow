from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings
from app.integrations.supabase_rest import SupabaseRestClient, SupabaseRestError
from app.services.access_service import AccessContext, AccessService

bearer_scheme = HTTPBearer(auto_error=False)


def _unauthorized(detail: str = "Nao autenticado.") -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


async def get_access_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> str:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise _unauthorized("Token bearer ausente.")
    token = (credentials.credentials or "").strip()
    if not token:
        raise _unauthorized("Token vazio.")
    return token


async def get_current_access(token: str = Depends(get_access_token)) -> AccessContext:
    settings = get_settings()
    if not str(settings.supabase_url or "").strip() or not str(settings.supabase_anon_key or "").strip():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Backend sem SUPABASE_URL/SUPABASE_ANON_KEY. Configure backend/.env e reinicie o FastAPI.",
        )
    gateway = SupabaseRestClient(settings)
    service = AccessService(settings, gateway)
    try:
        return await service.resolve(token)
    except SupabaseRestError as exc:
        raise _unauthorized(f"Token invalido ({exc.status_code}).")
    except Exception:
        raise _unauthorized("Falha ao validar autenticacao.")


async def require_admin(access: AccessContext = Depends(get_current_access)) -> AccessContext:
    if not access.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso admin requerido.")
    return access


async def require_paid(access: AccessContext = Depends(get_current_access)) -> AccessContext:
    if not access.paid:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Plano pago requerido.")
    return access


async def require_cadastro(access: AccessContext = Depends(get_current_access)) -> AccessContext:
    if not access.cadastro_allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissao de cadastro requerida (admin, plano pago ou liberacao manual).",
        )
    return access
