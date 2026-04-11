from __future__ import annotations

from typing import Any, Dict, List

from app.integrations.supabase_rest import SupabaseRestClient, SupabaseRestError
from app.services.access_service import AccessContext


class MotorService:
    def __init__(self, gateway: SupabaseRestClient):
        self.gateway = gateway

    async def list_motors(self, access: AccessContext, *, search: str = "", limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        limit = max(1, min(limit, 100))
        offset = max(0, offset)

        rows = await self._select_motors(access.token, search=search, limit=limit, offset=offset)
        if access.paid:
            return {"mode": "full", "total": len(rows), "items": rows}

        teaser = []
        for row in rows:
            teaser.append(
                {
                    "id": row.get("id") or row.get("Id"),
                    "marca": row.get("marca") or row.get("Marca") or "Motor",
                    "modelo": (
                        row.get("modelo")
                        or row.get("Modelo")
                        or row.get("modelo_iec")
                        or row.get("modelo_nema")
                        or f"Registro {row.get('id') or row.get('Id') or '-'}"
                    ),
                    "potencia": row.get("potencia") or row.get("Potencia") or "-",
                }
            )
        return {"mode": "teaser", "total": len(teaser), "items": teaser}

    async def get_motor_detail(self, access: AccessContext, motor_id: str) -> Dict[str, Any] | None:
        if not access.paid:
            return None

        for table, key in [("vw_consulta_motores", "id"), ("motores", "id"), ("vw_motores_para_site", "Id"), ("arquivos_motor", "id")]:
            try:
                row = await self.gateway.select_one(
                    table,
                    token=access.token,
                    params={
                        "select": "*",
                        key: f"eq.{motor_id}",
                    },
                )
                if row:
                    return row
            except SupabaseRestError:
                continue
        return None

    async def _select_motors(self, token: str, *, search: str, limit: int, offset: int) -> List[Dict[str, Any]]:
        search = (search or "").strip()
        params = {
            "select": "*",
            "order": "created_at.desc",
            "limit": str(limit),
            "offset": str(offset),
        }
        if search:
            params["or"] = SupabaseRestClient.build_or_ilike(
                ["marca", "modelo", "modelo_iec", "modelo_nema", "potencia", "rpm", "tensao", "corrente", "polos", "tipo_motor", "fases"],
                search,
            )

        candidates = [
            ("vw_consulta_motores", "created_at.desc"),
            ("vw_consulta_motores", "updated_at.desc"),
            ("vw_consulta_motores", None),
            ("vw_motores_para_site", "CreatedAt.desc"),
            ("vw_motores_para_site", "UpdatedAt.desc"),
            ("vw_motores_para_site", None),
            ("motores", "created_at.desc"),
            ("motores", "updated_at.desc"),
            ("motores", None),
        ]
        for table, order in candidates:
            local = dict(params)
            if order is None:
                local.pop("order", None)
            else:
                local["order"] = order
            try:
                rows = await self.gateway.select(table, token=token, params=local)
                if rows:
                    return rows
            except SupabaseRestError:
                continue
        return []

