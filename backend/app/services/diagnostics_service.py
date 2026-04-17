from __future__ import annotations

from typing import Any, Dict, List

from app.integrations.supabase_rest import SupabaseRestClient
from app.services.access_service import AccessContext


class DiagnosticsService:
    def __init__(self, gateway: SupabaseRestClient):
        self.gateway = gateway

    async def list(self, access: AccessContext, *, motor_id: str = "", limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        limit = max(1, min(int(limit or 20), 100))
        offset = max(0, int(offset or 0))
        params: Dict[str, Any] = {
            "select": "*",
            "order": "created_at.desc",
            "limit": str(limit),
            "offset": str(offset),
        }
        if motor_id:
            params["motor_id"] = f"eq.{motor_id}"
        rows = await self.gateway.select("diagnostics", token=access.token, params=params)
        return {"total": len(rows), "items": rows}

    async def get(self, access: AccessContext, diagnostic_id: str) -> Dict[str, Any] | None:
        row = await self.gateway.select_one(
            "diagnostics",
            token=access.token,
            params={"select": "*", "id": f"eq.{diagnostic_id}"},
        )
        return row

    async def run(self, access: AccessContext, *, motor_id: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        # MVP: persist a simple heuristic diagnostic record. Later: call real diagnostic engine.
        limit = max(1, min(int(limit or 10), 50))
        created: List[Dict[str, Any]] = []

        motor_ids: List[str] = []
        if motor_id:
            motor_ids = [motor_id]
        else:
            motors = await self.gateway.select(
                "vw_consulta_motores",
                token=access.token,
                params={"select": "id", "order": "created_at.desc", "limit": str(limit)},
            )
            for row in motors:
                mid = str(row.get("id") or row.get("Id") or "").strip()
                if mid:
                    motor_ids.append(mid)

        for idx, mid in enumerate(motor_ids[:limit]):
            score = max(0, min(100, 88 - idx * 5))
            payload = {
                "motor_id": mid,
                "created_by": access.user_id,
                "status": "done",
                "score": score,
                "summary": "Diagnostico MVP (heuristico).",
                "recommendations": [
                    {"code": "inspect_bearings", "label": "Inspecionar rolamentos", "priority": "medium"},
                    {"code": "check_insulation", "label": "Medir isolacao (megger)", "priority": "high"},
                ],
                "evidence": {"source": "mvp", "note": "Gerado sem modelo/IA nesta fase."},
            }
            rows = await self.gateway.insert("diagnostics", token=access.token, payload=payload)
            if rows:
                created.append(rows[0])
        return created

