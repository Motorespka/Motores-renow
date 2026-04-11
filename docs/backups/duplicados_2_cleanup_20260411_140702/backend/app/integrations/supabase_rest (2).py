from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional
import re

import httpx

from app.core.config import Settings


class SupabaseRestError(RuntimeError):
    def __init__(self, status_code: int, detail: str):
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class SupabaseRestClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_url = settings.supabase_url.rstrip("/")

    def _headers(self, *, token: str | None, use_service_role: bool = False, prefer: str | None = None) -> Dict[str, str]:
        key = self.settings.supabase_anon_key
        if use_service_role and self.settings.supabase_service_role_key:
            key = self.settings.supabase_service_role_key
        auth_token = key if use_service_role else (token or key)

        headers: Dict[str, str] = {
            "apikey": key,
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        }
        if prefer:
            headers["Prefer"] = prefer
        return headers

    async def auth_user(self, token: str) -> Dict[str, Any]:
        url = f"{self.base_url}/auth/v1/user"
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, headers=self._headers(token=token))
        if response.status_code >= 400:
            raise SupabaseRestError(response.status_code, response.text)
        payload = response.json()
        return payload if isinstance(payload, dict) else {}

    async def select(
        self,
        table: str,
        *,
        token: str | None = None,
        use_service_role: bool = False,
        params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/rest/v1/{table}"
        query = dict(params or {})
        if "select" not in query:
            query["select"] = "*"

        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                url,
                params=query,
                headers=self._headers(token=token, use_service_role=use_service_role),
            )
        if response.status_code >= 400:
            raise SupabaseRestError(response.status_code, response.text)
        payload = response.json()
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        return []

    async def select_one(
        self,
        table: str,
        *,
        token: str | None = None,
        use_service_role: bool = False,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any] | None:
        query = dict(params or {})
        query["limit"] = 1
        rows = await self.select(table, token=token, use_service_role=use_service_role, params=query)
        return rows[0] if rows else None

    async def update(
        self,
        table: str,
        *,
        payload: Dict[str, Any],
        filters: Dict[str, str],
        token: str | None = None,
        use_service_role: bool = False,
    ) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/rest/v1/{table}"
        params = {"select": "*"}
        params.update(filters)
        headers = self._headers(
            token=token,
            use_service_role=use_service_role,
            prefer="return=representation",
        )
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.patch(url, params=params, json=payload, headers=headers)
        if response.status_code >= 400:
            raise SupabaseRestError(response.status_code, response.text)
        body = response.json()
        if isinstance(body, list):
            return [item for item in body if isinstance(item, dict)]
        return []

    async def insert(
        self,
        table: str,
        *,
        payload: Dict[str, Any] | List[Dict[str, Any]],
        token: str | None = None,
        use_service_role: bool = False,
    ) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/rest/v1/{table}"
        headers = self._headers(
            token=token,
            use_service_role=use_service_role,
            prefer="return=representation",
        )
        params: Dict[str, Any] = {"select": "*"}
        async with httpx.AsyncClient(timeout=25.0) as client:
            response = await client.post(url, params=params, json=payload, headers=headers)
        if response.status_code >= 400:
            raise SupabaseRestError(response.status_code, response.text)
        body = response.json()
        if isinstance(body, list):
            return [item for item in body if isinstance(item, dict)]
        return [body] if isinstance(body, dict) else []

    async def upsert(
        self,
        table: str,
        *,
        payload: Dict[str, Any] | List[Dict[str, Any]],
        token: str | None = None,
        use_service_role: bool = False,
        on_conflict: str | None = None,
    ) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/rest/v1/{table}"
        params: Dict[str, Any] = {"select": "*"}
        if on_conflict:
            params["on_conflict"] = on_conflict
        headers = self._headers(
            token=token,
            use_service_role=use_service_role,
            prefer="resolution=merge-duplicates,return=representation",
        )
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(url, params=params, json=payload, headers=headers)
        if response.status_code >= 400:
            raise SupabaseRestError(response.status_code, response.text)
        body = response.json()
        if isinstance(body, list):
            return [item for item in body if isinstance(item, dict)]
        return [body] if isinstance(body, dict) else []

    async def delete(
        self,
        table: str,
        *,
        filters: Dict[str, str],
        token: str | None = None,
        use_service_role: bool = False,
    ) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/rest/v1/{table}"
        params = {"select": "*"}
        params.update(filters)
        headers = self._headers(
            token=token,
            use_service_role=use_service_role,
            prefer="return=representation",
        )
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.delete(url, params=params, headers=headers)
        if response.status_code >= 400:
            raise SupabaseRestError(response.status_code, response.text)
        body = response.json()
        if isinstance(body, list):
            return [item for item in body if isinstance(item, dict)]
        return []

    async def upload_storage_object(
        self,
        *,
        bucket: str,
        path: str,
        data: bytes,
        content_type: str = "application/octet-stream",
        token: str | None = None,
        use_service_role: bool = False,
        upsert: bool = True,
    ) -> str:
        safe_bucket = str(bucket or "").strip()
        safe_path = str(path or "").strip().lstrip("/")
        if not safe_bucket or not safe_path:
            raise ValueError("bucket/path invalidos para upload.")

        url = f"{self.base_url}/storage/v1/object/{safe_bucket}/{safe_path}"
        headers = self._headers(token=token, use_service_role=use_service_role)
        headers["Content-Type"] = content_type or "application/octet-stream"
        if upsert:
            headers["x-upsert"] = "true"

        async with httpx.AsyncClient(timeout=35.0) as client:
            response = await client.post(url, headers=headers, content=data)
        if response.status_code >= 400:
            raise SupabaseRestError(response.status_code, response.text)
        return f"{self.base_url}/storage/v1/object/public/{safe_bucket}/{safe_path}"

    @staticmethod
    def build_or_ilike(fields: Iterable[str], query: str) -> str:
        q = (query or "").strip()
        if not q:
            return ""
        # Hardening: bloqueia caracteres que podem quebrar a sintaxe do PostgREST `or=...`.
        # Mantem letras/numeros/espaco/_/- e reduz para um termo limpo.
        safe = re.sub(r"[^\w\s\-]+", " ", q, flags=re.UNICODE)
        safe = re.sub(r"\s+", " ", safe).strip()
        if not safe:
            return ""
        return "(" + ",".join(f"{field}.ilike.*{safe}*" for field in fields) + ")"
