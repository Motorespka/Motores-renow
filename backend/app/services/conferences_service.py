from __future__ import annotations

from typing import Any, Dict, List

from app.integrations.supabase_rest import SupabaseRestClient
from app.services.access_service import AccessContext


class ConferencesService:
    def __init__(self, gateway: SupabaseRestClient):
        self.gateway = gateway

    async def list(self, access: AccessContext, *, status: str = "", limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        limit = max(1, min(int(limit or 20), 100))
        offset = max(0, int(offset or 0))
        params: Dict[str, Any] = {
            "select": "*",
            "order": "created_at.desc",
            "limit": str(limit),
            "offset": str(offset),
        }
        if status:
            params["status"] = f"eq.{status}"
        rows = await self.gateway.select("conferences", token=access.token, params=params)
        return {"total": len(rows), "items": rows}

    async def diff(self, access: AccessContext, motor_id: str) -> Dict[str, Any]:
        # MVP: create/update a pending conference record with a trivial diff placeholder.
        payload = {
            "motor_id": motor_id,
            "created_by": access.user_id,
            "status": "pending",
            "confidence": 86,
            "diff": {
                "potencia": {"ocr": "10 CV", "normalized": "10 CV", "ok": True},
                "rpm": {"ocr": "1750", "normalized": "1750", "ok": True},
            },
            "decision": {},
        }
        rows = await self.gateway.upsert(
            "conferences",
            token=access.token,
            payload=payload,
            on_conflict="motor_id",
        )
        if rows:
            return rows[0]
        # fallback: fetch by motor_id
        row = await self.gateway.select_one(
            "conferences",
            token=access.token,
            params={"select": "*", "motor_id": f"eq.{motor_id}"},
        )
        return row or {}

    async def decide(self, access: AccessContext, motor_id: str, *, approved: bool, reason: str = "", notes: str = "") -> Dict[str, Any]:
        status = "approved" if approved else "rejected"
        decision = {"approved": approved, "reason": reason, "notes": notes}
        rows = await self.gateway.update(
            "conferences",
            token=access.token,
            payload={
                "status": status,
                "decision": decision,
                "decided_by": access.user_id,
                # PostgREST expects a timestamp value; we set server-side default later.
                # For now, omit decided_at here and rely on trigger/DB update (or client readback).
            },
            filters={"motor_id": f"eq.{motor_id}"},
        )
        if rows:
            return rows[0]
        # If not existing, create then decide
        row = await self.diff(access, motor_id)
        if row.get("id"):
            rows2 = await self.gateway.update(
                "conferences",
                token=access.token,
                payload={
                    "status": status,
                    "decision": decision,
                    "decided_by": access.user_id,
                    "decided_at": "now()",
                },
                filters={"id": f"eq.{row.get('id')}"},
            )
            if rows2:
                return rows2[0]
        return row

