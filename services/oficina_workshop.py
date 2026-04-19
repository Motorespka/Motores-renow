"""
Biblioteca de cálculos de rebobinagem + ordens de serviço (oficina).

Tabelas: ``rebobinagem_calculos``, ``oficina_ordens_servico`` (Postgres via migração;
SQLite local criada em ``services/database._ensure_base_tables``).
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

TABLE_CALC = "rebobinagem_calculos"
TABLE_OS = "oficina_ordens_servico"

OS_ETAPAS = (
    "recebido",
    "busca_calculo",
    "calculo_encontrado",
    "calculo_criado",
    "limpeza",
    "rebobinagem",
    "impregnacao",
    "montagem",
    "teste",
    "troca_pecas",
    "entrega",
    "encerrado",
)


def _is_local_client(client: Any) -> bool:
    return bool(getattr(client, "is_local_runtime", False))


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _now_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def _row_to_dict(row: Any) -> Dict[str, Any]:
    if isinstance(row, dict):
        return dict(row)
    try:
        return dict(row)
    except Exception:
        return {}


def build_calc_payload_from_parts(
    *,
    motor: Dict[str, Any],
    bobinagem_principal: Dict[str, Any],
    bobinagem_auxiliar: Optional[Dict[str, Any]] = None,
    esquema: Optional[Dict[str, Any]] = None,
    mecanica: Optional[Dict[str, Any]] = None,
    testes_bancada: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "motor": motor if isinstance(motor, dict) else {},
        "bobinagem_principal": bobinagem_principal if isinstance(bobinagem_principal, dict) else {},
        "bobinagem_auxiliar": bobinagem_auxiliar if isinstance(bobinagem_auxiliar, dict) else {},
        "esquema": esquema if isinstance(esquema, dict) else {},
    }
    if isinstance(mecanica, dict) and mecanica:
        out["mecanica"] = mecanica
    if isinstance(testes_bancada, list) and testes_bancada:
        out["testes_bancada"] = testes_bancada
    return out


def parse_tags_csv(raw: str) -> List[str]:
    parts = re.split(r"[,;]+", _to_text(raw))
    return [p.strip() for p in parts if p.strip()]


def _row_tag_match(row: Dict[str, Any], tag_needle: str) -> bool:
    if not tag_needle:
        return True
    tags = row.get("tags") or []
    if not isinstance(tags, list):
        return tag_needle in _to_text(tags).lower()
    for t in tags:
        if tag_needle in str(t).lower():
            return True
    return False


def list_calculos(
    client: Any,
    *,
    q: str = "",
    limit: int = 80,
    tag: str = "",
    only_created_by: str = "",
) -> List[Dict[str, Any]]:
    lim = max(1, min(int(limit), 200))
    owner = _to_text(only_created_by)
    try:
        if _is_local_client(client):
            res = client.table(TABLE_CALC).select("*").order("updated_at", desc=True).limit(lim * 3).execute()
        elif owner:
            res = (
                client.table(TABLE_CALC)
                .select("*")
                .eq("created_by", owner)
                .order("updated_at", desc=True)
                .limit(lim * 3)
                .execute()
            )
        else:
            qb = client.table(TABLE_CALC).select("*").order("updated_at", desc=True).limit(lim * 3)
            res = qb.execute()
    except Exception:
        return []

    rows = [_row_to_dict(r) for r in (res.data or [])]
    if owner and _is_local_client(client):
        rows = [r for r in rows if _to_text(r.get("created_by")) == owner]
    tg = _to_text(tag).lower()
    if tg:
        rows = [r for r in rows if _row_tag_match(r, tg)]
    qt = _to_text(q).lower()
    if not qt:
        return rows[:lim]
    out: List[Dict[str, Any]] = []
    for r in rows:
        blob = json.dumps(r, ensure_ascii=False, default=str).lower()
        tit = _to_text(r.get("titulo")).lower()
        notas = _to_text(r.get("notas")).lower()
        tags = r.get("tags") or []
        tag_s = " ".join(str(t) for t in tags).lower() if isinstance(tags, list) else _to_text(tags).lower()
        if qt in blob or qt in tit or qt in notas or qt in tag_s:
            out.append(r)
        if len(out) >= lim:
            break
    return out


def get_calculo(client: Any, calc_id: str) -> Optional[Dict[str, Any]]:
    cid = _to_text(calc_id)
    if not cid:
        return None
    try:
        res = client.table(TABLE_CALC).select("*").eq("id", cid).limit(1).execute()
    except Exception:
        return None
    rows = res.data or []
    if not rows:
        return None
    return _row_to_dict(rows[0])


def insert_calculo(
    client: Any,
    *,
    titulo: str,
    notas: str = "",
    tags: Optional[List[str]] = None,
    fases: str = "",
    potencia_cv: Optional[float] = None,
    rpm: Optional[int] = None,
    polos: Optional[int] = None,
    tensao_v: Optional[float] = None,
    ranhuras: Optional[int] = None,
    payload: Dict[str, Any],
    revision_of: Optional[str] = None,
    revision_label: str = "",
    created_by: Optional[str] = None,
) -> Dict[str, Any]:
    tags = tags or []
    row: Dict[str, Any] = {
        "titulo": titulo.strip() or "Sem titulo",
        "notas": notas.strip(),
        "tags": tags,
        "fases": fases.strip(),
        "potencia_cv": potencia_cv,
        "rpm": rpm,
        "polos": polos,
        "tensao_v": tensao_v,
        "ranhuras": ranhuras,
        "payload": payload or {},
        "revision_label": revision_label.strip(),
    }
    if revision_of:
        row["revision_of"] = revision_of.strip()
    if created_by:
        row["created_by"] = created_by.strip()

    if not _is_local_client(client):
        row["id"] = str(uuid.uuid4())

    res = client.table(TABLE_CALC).insert(row).execute()
    data = res.data or []
    if data:
        return _row_to_dict(data[0])
    raise RuntimeError("Insert calculo retornou vazio.")


def update_calculo(
    client: Any,
    calc_id: str,
    *,
    titulo: str,
    notas: str = "",
    tags: Optional[List[str]] = None,
    fases: str = "",
    potencia_cv: Optional[float] = None,
    rpm: Optional[int] = None,
    polos: Optional[int] = None,
    tensao_v: Optional[float] = None,
    ranhuras: Optional[int] = None,
    payload: Dict[str, Any],
    revision_label: str = "",
) -> None:
    cid = _to_text(calc_id)
    if not cid:
        raise ValueError("calc_id vazio.")
    tags = tags or []
    row: Dict[str, Any] = {
        "titulo": titulo.strip() or "Sem titulo",
        "notas": notas.strip(),
        "tags": tags,
        "fases": fases.strip(),
        "potencia_cv": potencia_cv,
        "rpm": rpm,
        "polos": polos,
        "tensao_v": tensao_v,
        "ranhuras": ranhuras,
        "payload": payload or {},
        "revision_label": _to_text(revision_label),
    }
    client.table(TABLE_CALC).update(row).eq("id", cid).execute()


def _parse_ts(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s.replace(" ", "T", 1) if "T" not in s and " " in s else s)
    except Exception:
        return None


def list_ordens_servico(
    client: Any,
    *,
    limit: int = 60,
    etapa: str = "",
    motor_q: str = "",
    texto: str = "",
    since_days: int = 0,
    only_created_by: str = "",
) -> List[Dict[str, Any]]:
    lim = max(1, min(int(limit), 200))
    fetch = min(lim * 8, 500)
    try:
        res = client.table(TABLE_OS).select("*").order("updated_at", desc=True).limit(fetch).execute()
    except Exception:
        return []

    rows = [_row_to_dict(r) for r in (res.data or [])]
    et = _to_text(etapa).lower()
    mq = _to_text(motor_q).lower()
    tx = _to_text(texto).lower()
    owner = _to_text(only_created_by)
    cutoff: Optional[datetime] = None
    if since_days > 0:
        cutoff = datetime.now(timezone.utc) - timedelta(days=int(since_days))

    out: List[Dict[str, Any]] = []
    for r in rows:
        if owner and _to_text(r.get("created_by")) != owner:
            continue
        if et and _to_text(r.get("etapa")).lower() != et:
            continue
        mid = _to_text(r.get("motor_id")).lower()
        if mq and mq not in mid:
            continue
        if cutoff:
            ts = _parse_ts(r.get("updated_at")) or _parse_ts(r.get("created_at"))
            if ts is None:
                continue
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            if ts < cutoff:
                continue
        if tx:
            blob = f"{r.get('numero')} {r.get('titulo')} {json.dumps(r.get('payload'), default=str)}".lower()
            if tx not in blob:
                continue
        out.append(r)
        if len(out) >= lim:
            break
    return out


def get_ordem_servico(client: Any, os_id: str) -> Optional[Dict[str, Any]]:
    oid = _to_text(os_id)
    if not oid:
        return None
    try:
        res = client.table(TABLE_OS).select("*").eq("id", oid).limit(1).execute()
    except Exception:
        return None
    rows = res.data or []
    if not rows:
        return None
    return _row_to_dict(rows[0])


def _next_os_numero_local(client: Any) -> str:
    try:
        res = client.table(TABLE_OS).select("id").order("id", desc=True).limit(1).execute()
        last = (res.data or [{}])[0].get("id")
        n = int(last) + 1 if last is not None else 1
    except Exception:
        n = 1
    return f"OS-LOC-{n:05d}"


def _next_os_numero_cloud(client: Any) -> str:
    stamp = datetime.utcnow().strftime("%Y%m%d")
    suf = uuid.uuid4().hex[:6].upper()
    return f"OS-{stamp}-{suf}"


def insert_ordem_servico(
    client: Any,
    *,
    titulo: str,
    motor_id: Optional[str] = None,
    etapa: str = "recebido",
    calc_id: Optional[str] = None,
    created_by: Optional[str] = None,
) -> Dict[str, Any]:
    etapa = _to_text(etapa) or "recebido"
    if etapa not in OS_ETAPAS:
        etapa = "recebido"
    numero = _next_os_numero_local(client) if _is_local_client(client) else _next_os_numero_cloud(client)
    payload: Dict[str, Any] = {"eventos": [{"data": _now_iso(), "etapa": etapa, "nota": "Abertura da OS."}]}
    row: Dict[str, Any] = {
        "numero": numero,
        "titulo": titulo.strip() or "Ordem de servico",
        "motor_id": _to_text(motor_id) or None,
        "etapa": etapa,
        "payload": payload,
    }
    if calc_id:
        row["calc_id"] = _to_text(calc_id)
    if created_by:
        row["created_by"] = created_by.strip()
    if not _is_local_client(client):
        row["id"] = str(uuid.uuid4())

    res = client.table(TABLE_OS).insert(row).execute()
    data = res.data or []
    if data:
        return _row_to_dict(data[0])
    raise RuntimeError("Insert OS retornou vazio.")


def append_os_event(
    client: Any,
    os_id: str,
    *,
    etapa: str,
    nota: str,
) -> Dict[str, Any]:
    row = get_ordem_servico(client, os_id)
    if not row:
        raise RuntimeError("OS nao encontrada.")
    etapa = _to_text(etapa) or row.get("etapa") or "recebido"
    if etapa not in OS_ETAPAS:
        etapa = str(row.get("etapa") or "recebido")
    payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
    ev = payload.get("eventos")
    if not isinstance(ev, list):
        ev = []
    ev.append({"data": _now_iso(), "etapa": etapa, "nota": _to_text(nota) or "(sem nota)"})
    payload["eventos"] = ev[-120:]
    upd = {"etapa": etapa, "payload": payload}
    client.table(TABLE_OS).update(upd).eq("id", str(row["id"])).execute()
    out = get_ordem_servico(client, str(row["id"]))
    return out or row


def link_os_to_calculo(client: Any, os_id: str, calc_id: Optional[str]) -> None:
    cid = _to_text(calc_id) if calc_id else None
    client.table(TABLE_OS).update({"calc_id": cid}).eq("id", _to_text(os_id)).execute()


def summarize_open_os_by_creator(client: Any, *, limit: int = 200) -> List[Dict[str, Any]]:
    """
    OS nao encerradas agrupadas por ``created_by`` (proxy de responsavel na oficina).
    Conta quantas tem ``payload.prazo_entrega_previsto`` (AAAA-MM-DD) ja vencido (referencia interna).
    """
    from datetime import datetime, timezone

    rows = list_ordens_servico(client, limit=min(int(limit), 200), since_days=0)
    today = datetime.now(timezone.utc).date()
    acc: Dict[str, Dict[str, int]] = {}
    for r in rows:
        et = _to_text(r.get("etapa")).lower()
        if et == "encerrado":
            continue
        owner = _to_text(r.get("created_by")) or "(sem created_by)"
        slot = acc.setdefault(owner, {"abertas": 0, "prazo_interno_vencido": 0})
        slot["abertas"] += 1
        pl = r.get("payload") if isinstance(r.get("payload"), dict) else {}
        pz = _to_text(pl.get("prazo_entrega_previsto"))[:10]
        if len(pz) >= 10:
            try:
                if datetime.strptime(pz, "%Y-%m-%d").date() < today:
                    slot["prazo_interno_vencido"] += 1
            except Exception:
                pass
    return [
        {"responsavel_created_by": k, **v}
        for k, v in sorted(acc.items(), key=lambda kv: (-kv[1]["abertas"], kv[0]))
    ]


def merge_ordem_servico_payload(client: Any, os_id: str, patch: Dict[str, Any]) -> None:
    """Mescla ``patch`` no payload JSON da OS (merge superficial de dicts aninhados para ficha_mecanica)."""
    row = get_ordem_servico(client, os_id)
    if not row:
        raise RuntimeError("OS nao encontrada.")
    payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
    payload = dict(payload)
    for key, val in (patch or {}).items():
        if key == "ficha_mecanica" and isinstance(val, dict):
            prev = payload.get("ficha_mecanica")
            if isinstance(prev, dict):
                merged = dict(prev)
                merged.update(val)
                payload["ficha_mecanica"] = merged
            else:
                payload["ficha_mecanica"] = dict(val)
        else:
            payload[key] = val
    client.table(TABLE_OS).update({"payload": payload}).eq("id", str(row["id"])).execute()


def workshop_tables_available(client: Any) -> bool:
    try:
        client.table(TABLE_CALC).select("id").limit(1).execute()
        client.table(TABLE_OS).select("id").limit(1).execute()
        return True
    except Exception:
        return False
