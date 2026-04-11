from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
import uuid

import streamlit as st


TABLE_EMPRESAS = "marketplace_empresas"
TABLE_ANUNCIOS = "marketplace_anuncios"
TABLE_FORNECEDORES = "marketplace_fornecedores"
TABLE_VAGAS = "marketplace_vagas"
TABLE_BLOQUEIOS = "marketplace_bloqueios"
TABLE_TERMOS = "marketplace_termos_aceites"
TABLES_MODULE = {
    "empresas": TABLE_EMPRESAS,
    "anuncios": TABLE_ANUNCIOS,
    "fornecedores": TABLE_FORNECEDORES,
    "vagas": TABLE_VAGAS,
}

STATUS_ACTIVE = "active"
STATUS_PAUSED = "paused"
STATUS_REMOVED = "removed"


def _now_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def _to_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _to_text(value).lower() in {"1", "true", "yes", "sim", "on"}


def _parse_dt(value: Any) -> datetime | None:
    text = _to_text(value)
    if not text:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[:19], fmt)
        except Exception:
            continue
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except Exception:
        return None


def _safe_decimal(value: Any) -> Decimal | None:
    text = _to_text(value).replace("R$", "").replace(" ", "").replace(",", ".")
    if not text:
        return None
    try:
        return Decimal(text)
    except Exception:
        return None


def _gen_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def formatar_tempo_publicacao(created_at: Any) -> str:
    dt = _parse_dt(created_at)
    if not dt:
        return "-"
    delta = datetime.utcnow() - dt
    if delta < timedelta(minutes=1):
        return "agora"
    if delta < timedelta(hours=1):
        return f"{int(delta.total_seconds() // 60)} min"
    if delta < timedelta(days=1):
        return f"{int(delta.total_seconds() // 3600)} h"
    dias = delta.days
    if dias <= 30:
        return f"{dias} dia(s)"
    return dt.strftime("%d/%m/%Y")


@dataclass
class EmpresaPublica:
    id: str
    nome_publico: str
    cidade: str | None = None
    estado: str | None = None
    descricao: str | None = None
    whatsapp: str | None = None
    especialidades: str | None = None
    regiao_atendimento: str | None = None
    rota_entrega: str | None = None
    pedido_minimo_texto: str | None = None
    perfil_completo: bool = False
    last_login_at: str | None = None
    last_activity_at: str | None = None
    activity_score: int = 0
    calculos_count: int = 0
    anuncios_count: int = 0
    vagas_count: int = 0
    status: str = STATUS_ACTIVE
    user_id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class Anuncio:
    id: str
    titulo: str
    categoria: str
    descricao_curta: str
    cidade: str
    estado: str
    nome_publico: str
    whatsapp: str
    regiao_atendimento: str | None = None
    rota_entrega: str | None = None
    pedido_minimo_texto: str | None = None
    retirada_local: bool = False
    entrega_sob_consulta: bool = False
    preco_valor: Decimal | None = None
    preco_texto: str | None = None
    visualizacoes_count: int = 0
    cliques_contato_count: int = 0
    score_relevancia: float = 0.0
    created_at: str | None = None
    updated_at: str | None = None
    expires_at: str | None = None
    status: str = STATUS_ACTIVE
    user_id: str | None = None
    empresa_id: str | None = None


@dataclass
class Fornecedor:
    id: str
    nome_publico: str
    cidade: str
    estado: str
    descricao: str
    whatsapp: str
    regiao_atendimento: str | None = None
    rota_entrega: str | None = None
    pedido_minimo_texto: str | None = None
    retirada_local: bool = False
    entrega_sob_consulta: bool = False
    status: str = STATUS_ACTIVE
    created_at: str | None = None
    updated_at: str | None = None
    user_id: str | None = None
    empresa_id: str | None = None


@dataclass
class Vaga:
    id: str
    nome_empresa_snapshot: str
    titulo: str
    descricao: str
    cidade: str
    estado: str
    tipo_vaga: str
    regime: str | None = None
    faixa_salarial_texto: str | None = None
    contato_whatsapp: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    expires_at: str | None = None
    status: str = STATUS_ACTIVE
    user_id: str | None = None
    empresa_id: str | None = None


def get_status_atividade(last_activity_at: datetime | None) -> tuple[str, str | None]:
    if not last_activity_at:
        return "Nova na plataforma", None

    agora = datetime.utcnow()
    delta = agora - last_activity_at

    if delta <= timedelta(days=1):
        return "Ativa agora", None
    if delta <= timedelta(days=7):
        return "Ativa recentemente", None
    if delta <= timedelta(days=30):
        return "Pouco ativa", None
    return "Inativa", last_activity_at.strftime("%d/%m/%Y")


def calcular_score_anuncio(anuncio: Anuncio) -> float:
    score = 0.0
    score += int(anuncio.visualizacoes_count or 0) * 0.05
    score += int(anuncio.cliques_contato_count or 0) * 1.5

    created_dt = _parse_dt(anuncio.created_at)
    if created_dt:
        dias = max((datetime.utcnow() - created_dt).days, 0)
        score += max(10 - min(dias, 10), 0)

    updated_dt = _parse_dt(anuncio.updated_at)
    if updated_dt:
        dias_upd = max((datetime.utcnow() - updated_dt).days, 0)
        score += max(5 - min(dias_upd, 5), 0)

    if anuncio.regiao_atendimento:
        score += 1
    if anuncio.rota_entrega:
        score += 1
    if anuncio.pedido_minimo_texto:
        score += 1
    return round(score, 2)


def mensagem_contato_anuncio() -> str:
    return "Ola, vi seu anuncio no Uniao Motores e gostaria de mais informacoes."


def mensagem_contato_vaga() -> str:
    return "Ola, vi uma vaga no Uniao Motores e gostaria de mais informacoes."


class CommercialModuleStore:
    def __init__(self, client: Any, force_local: bool = False) -> None:
        self.client = client
        self.force_local = bool(force_local)

    def _session_key(self, table_name: str) -> str:
        return f"_comercial_local_{table_name}"

    def _use_local(self) -> bool:
        if self.force_local:
            return True
        if self.client is None:
            return True
        return bool(getattr(self.client, "is_local_runtime", False))

    def _get_local_rows(self, table_name: str) -> List[Dict[str, Any]]:
        key = self._session_key(table_name)
        raw = st.session_state.get(key)
        if not isinstance(raw, list):
            raw = []
        return [dict(item) for item in raw if isinstance(item, dict)]

    def _set_local_rows(self, table_name: str, rows: List[Dict[str, Any]]) -> None:
        st.session_state[self._session_key(table_name)] = [dict(item) for item in rows if isinstance(item, dict)]

    def _remote_select(self, table_name: str, limit: int = 500) -> List[Dict[str, Any]] | None:
        if self._use_local():
            return None
        try:
            res = self.client.table(table_name).select("*").order("updated_at", desc=True).limit(limit).execute()
            data = getattr(res, "data", None) or []
            if isinstance(data, list):
                return [dict(item) for item in data if isinstance(item, dict)]
        except Exception:
            return None
        return []

    def _remote_insert(self, table_name: str, payload: Dict[str, Any]) -> bool:
        if self._use_local():
            return False
        try:
            self.client.table(table_name).insert(payload).execute()
            return True
        except Exception:
            return False

    def _remote_update(self, table_name: str, row_id: str, payload: Dict[str, Any]) -> bool:
        if self._use_local():
            return False
        try:
            self.client.table(table_name).update(payload).eq("id", row_id).execute()
            return True
        except Exception:
            return False

    def _list_rows(self, table_name: str, include_inactive: bool = False) -> List[Dict[str, Any]]:
        remote = self._remote_select(table_name)
        if remote is not None:
            rows = remote
        else:
            rows = self._get_local_rows(table_name)
        if include_inactive:
            return rows
        return [row for row in rows if _to_text(row.get("status")).lower() not in {STATUS_REMOVED}]

    def _save_row(self, table_name: str, payload: Dict[str, Any], prefix: str) -> Dict[str, Any]:
        row = dict(payload or {})
        row_id = _to_text(row.get("id")) or _gen_id(prefix)
        now = _now_iso()
        row["id"] = row_id
        row["created_at"] = _to_text(row.get("created_at")) or now
        row["updated_at"] = now
        row["status"] = _to_text(row.get("status")) or STATUS_ACTIVE

        if self._remote_insert(table_name, row):
            return row

        rows = self._get_local_rows(table_name)
        filtered = [item for item in rows if _to_text(item.get("id")) != row_id]
        filtered.append(row)
        self._set_local_rows(table_name, filtered)
        return row

    def _set_row_status(self, table_name: str, row_id: str, status: str) -> bool:
        payload = {"status": status, "updated_at": _now_iso()}
        if self._remote_update(table_name, row_id, payload):
            return True

        rows = self._get_local_rows(table_name)
        updated = False
        for row in rows:
            if _to_text(row.get("id")) == row_id:
                row["status"] = status
                row["updated_at"] = payload["updated_at"]
                updated = True
                break
        if updated:
            self._set_local_rows(table_name, rows)
        return updated

    def _upsert_block(
        self,
        *,
        target_type: str,
        target_id: str,
        module_name: str,
        blocked: bool,
        reason: str,
        actor_user_id: str,
    ) -> bool:
        target_id = _to_text(target_id)
        if not target_id:
            return False

        rows = self._list_rows(TABLE_BLOQUEIOS, include_inactive=True)
        now = _now_iso()
        found = None
        for row in rows:
            if (
                _to_text(row.get("target_type")) == target_type
                and _to_text(row.get("target_id")) == target_id
                and _to_text(row.get("module_name")) == module_name
            ):
                found = row
                break

        payload = {
            "id": _to_text(found.get("id")) if isinstance(found, dict) else _gen_id("block"),
            "target_type": target_type,
            "target_id": target_id,
            "module_name": module_name,
            "blocked": bool(blocked),
            "reason": _to_text(reason),
            "updated_by": _to_text(actor_user_id),
            "updated_at": now,
            "created_at": _to_text((found or {}).get("created_at")) or now,
            "status": STATUS_ACTIVE,
        }

        if found and self._remote_update(TABLE_BLOQUEIOS, payload["id"], payload):
            return True
        if (not found) and self._remote_insert(TABLE_BLOQUEIOS, payload):
            return True

        if found:
            for idx, row in enumerate(rows):
                if _to_text(row.get("id")) == payload["id"]:
                    rows[idx] = payload
                    self._set_local_rows(TABLE_BLOQUEIOS, rows)
                    return True
        rows.append(payload)
        self._set_local_rows(TABLE_BLOQUEIOS, rows)
        return True

    def is_blocked(self, target_type: str, target_id: str, module_name: str) -> bool:
        target = _to_text(target_id)
        if not target:
            return False
        rows = self._list_rows(TABLE_BLOQUEIOS, include_inactive=True)
        for row in rows:
            if (
                _to_text(row.get("target_type")) == _to_text(target_type)
                and _to_text(row.get("target_id")) == target
                and _to_text(row.get("module_name")) == _to_text(module_name)
                and _to_bool(row.get("blocked"))
            ):
                return True
        return False

    def list_blocks(self, module_name: str = "") -> List[Dict[str, Any]]:
        rows = self._list_rows(TABLE_BLOQUEIOS, include_inactive=True)
        if not module_name:
            return rows
        module = _to_text(module_name)
        return [row for row in rows if _to_text(row.get("module_name")) == module]

    def block_user(self, user_id: str, module_name: str, blocked: bool, reason: str, actor_user_id: str) -> bool:
        return self._upsert_block(
            target_type="user",
            target_id=user_id,
            module_name=module_name,
            blocked=blocked,
            reason=reason,
            actor_user_id=actor_user_id,
        )

    def block_empresa(self, empresa_id: str, module_name: str, blocked: bool, reason: str, actor_user_id: str) -> bool:
        return self._upsert_block(
            target_type="empresa",
            target_id=empresa_id,
            module_name=module_name,
            blocked=blocked,
            reason=reason,
            actor_user_id=actor_user_id,
        )

    def save_empresa(self, payload: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        model = EmpresaPublica(
            id=_to_text(payload.get("id")) or _gen_id("emp"),
            nome_publico=_to_text(payload.get("nome_publico")),
            cidade=_to_text(payload.get("cidade")) or None,
            estado=_to_text(payload.get("estado")) or None,
            descricao=_to_text(payload.get("descricao")) or None,
            whatsapp=_to_text(payload.get("whatsapp")) or None,
            especialidades=_to_text(payload.get("especialidades")) or None,
            regiao_atendimento=_to_text(payload.get("regiao_atendimento")) or None,
            rota_entrega=_to_text(payload.get("rota_entrega")) or None,
            pedido_minimo_texto=_to_text(payload.get("pedido_minimo_texto")) or None,
            perfil_completo=_to_bool(payload.get("perfil_completo")),
            last_login_at=_to_text(payload.get("last_login_at")) or None,
            last_activity_at=_to_text(payload.get("last_activity_at")) or _now_iso(),
            activity_score=int(payload.get("activity_score") or 0),
            calculos_count=int(payload.get("calculos_count") or 0),
            anuncios_count=int(payload.get("anuncios_count") or 0),
            vagas_count=int(payload.get("vagas_count") or 0),
            status=_to_text(payload.get("status")) or STATUS_ACTIVE,
            user_id=_to_text(user_id),
        )
        return self._save_row(TABLE_EMPRESAS, asdict(model), prefix="emp")

    def list_empresas(self, *, cidade: str = "", estado: str = "", include_inactive: bool = False) -> List[Dict[str, Any]]:
        rows = self._list_rows(TABLE_EMPRESAS, include_inactive=include_inactive)
        cidade_f = _to_text(cidade).lower()
        estado_f = _to_text(estado).lower()
        out: List[Dict[str, Any]] = []
        for row in rows:
            if cidade_f and cidade_f not in _to_text(row.get("cidade")).lower():
                continue
            if estado_f and estado_f not in _to_text(row.get("estado")).lower():
                continue
            out.append(row)
        return out

    def save_anuncio(self, payload: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        model = Anuncio(
            id=_to_text(payload.get("id")) or _gen_id("ad"),
            titulo=_to_text(payload.get("titulo")),
            categoria=_to_text(payload.get("categoria")),
            descricao_curta=_to_text(payload.get("descricao_curta")),
            cidade=_to_text(payload.get("cidade")),
            estado=_to_text(payload.get("estado")),
            nome_publico=_to_text(payload.get("nome_publico")),
            whatsapp=_to_text(payload.get("whatsapp")),
            regiao_atendimento=_to_text(payload.get("regiao_atendimento")) or None,
            rota_entrega=_to_text(payload.get("rota_entrega")) or None,
            pedido_minimo_texto=_to_text(payload.get("pedido_minimo_texto")) or None,
            retirada_local=_to_bool(payload.get("retirada_local")),
            entrega_sob_consulta=_to_bool(payload.get("entrega_sob_consulta")),
            preco_valor=_safe_decimal(payload.get("preco_valor")),
            preco_texto=_to_text(payload.get("preco_texto")) or None,
            visualizacoes_count=int(payload.get("visualizacoes_count") or 0),
            cliques_contato_count=int(payload.get("cliques_contato_count") or 0),
            score_relevancia=0.0,
            expires_at=_to_text(payload.get("expires_at")) or None,
            status=_to_text(payload.get("status")) or STATUS_ACTIVE,
            user_id=_to_text(user_id),
            empresa_id=_to_text(payload.get("empresa_id")) or None,
        )
        row = asdict(model)
        row["preco_valor"] = str(model.preco_valor) if model.preco_valor is not None else None
        row["score_relevancia"] = calcular_score_anuncio(
            Anuncio(
                **{
                    **model.__dict__,
                    "created_at": _now_iso(),
                    "updated_at": _now_iso(),
                }
            )
        )
        return self._save_row(TABLE_ANUNCIOS, row, prefix="ad")

    def list_anuncios(
        self,
        *,
        cidade: str = "",
        estado: str = "",
        com_rota: bool = False,
        retirada_local: bool = False,
        pedido_minimo: bool = False,
        include_inactive: bool = False,
    ) -> List[Dict[str, Any]]:
        rows = self._list_rows(TABLE_ANUNCIOS, include_inactive=include_inactive)
        out: List[Dict[str, Any]] = []
        cidade_f = _to_text(cidade).lower()
        estado_f = _to_text(estado).lower()
        for row in rows:
            if cidade_f and cidade_f not in _to_text(row.get("cidade")).lower():
                continue
            if estado_f and estado_f not in _to_text(row.get("estado")).lower():
                continue
            if com_rota and not _to_text(row.get("rota_entrega")):
                continue
            if retirada_local and not _to_bool(row.get("retirada_local")):
                continue
            if pedido_minimo and not _to_text(row.get("pedido_minimo_texto")):
                continue
            out.append(row)
        out.sort(key=lambda item: _to_text(item.get("updated_at")), reverse=True)
        return out

    def save_fornecedor(self, payload: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        model = Fornecedor(
            id=_to_text(payload.get("id")) or _gen_id("forn"),
            nome_publico=_to_text(payload.get("nome_publico")),
            cidade=_to_text(payload.get("cidade")),
            estado=_to_text(payload.get("estado")),
            descricao=_to_text(payload.get("descricao")),
            whatsapp=_to_text(payload.get("whatsapp")),
            regiao_atendimento=_to_text(payload.get("regiao_atendimento")) or None,
            rota_entrega=_to_text(payload.get("rota_entrega")) or None,
            pedido_minimo_texto=_to_text(payload.get("pedido_minimo_texto")) or None,
            retirada_local=_to_bool(payload.get("retirada_local")),
            entrega_sob_consulta=_to_bool(payload.get("entrega_sob_consulta")),
            status=_to_text(payload.get("status")) or STATUS_ACTIVE,
            user_id=_to_text(user_id),
            empresa_id=_to_text(payload.get("empresa_id")) or None,
        )
        return self._save_row(TABLE_FORNECEDORES, asdict(model), prefix="forn")

    def list_fornecedores(
        self,
        *,
        cidade: str = "",
        com_rota: bool = False,
        retirada_local: bool = False,
        pedido_minimo: bool = False,
        include_inactive: bool = False,
    ) -> List[Dict[str, Any]]:
        rows = self._list_rows(TABLE_FORNECEDORES, include_inactive=include_inactive)
        cidade_f = _to_text(cidade).lower()
        out: List[Dict[str, Any]] = []
        for row in rows:
            atende = _to_text(row.get("regiao_atendimento")).lower()
            cidade_row = _to_text(row.get("cidade")).lower()
            if cidade_f and cidade_f not in cidade_row and cidade_f not in atende:
                continue
            if com_rota and not _to_text(row.get("rota_entrega")):
                continue
            if retirada_local and not _to_bool(row.get("retirada_local")):
                continue
            if pedido_minimo and not _to_text(row.get("pedido_minimo_texto")):
                continue
            out.append(row)
        out.sort(key=lambda item: _to_text(item.get("updated_at")), reverse=True)
        return out

    def save_vaga(self, payload: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        model = Vaga(
            id=_to_text(payload.get("id")) or _gen_id("vaga"),
            nome_empresa_snapshot=_to_text(payload.get("nome_empresa_snapshot")),
            titulo=_to_text(payload.get("titulo")),
            descricao=_to_text(payload.get("descricao")),
            cidade=_to_text(payload.get("cidade")),
            estado=_to_text(payload.get("estado")),
            tipo_vaga=_to_text(payload.get("tipo_vaga")),
            regime=_to_text(payload.get("regime")) or None,
            faixa_salarial_texto=_to_text(payload.get("faixa_salarial_texto")) or None,
            contato_whatsapp=_to_text(payload.get("contato_whatsapp")) or None,
            expires_at=_to_text(payload.get("expires_at")) or None,
            status=_to_text(payload.get("status")) or STATUS_ACTIVE,
            user_id=_to_text(user_id),
            empresa_id=_to_text(payload.get("empresa_id")) or None,
        )
        return self._save_row(TABLE_VAGAS, asdict(model), prefix="vaga")

    def list_vagas(
        self,
        *,
        cidade: str = "",
        estado: str = "",
        include_inactive: bool = False,
    ) -> List[Dict[str, Any]]:
        rows = self._list_rows(TABLE_VAGAS, include_inactive=include_inactive)
        cidade_f = _to_text(cidade).lower()
        estado_f = _to_text(estado).lower()
        out: List[Dict[str, Any]] = []
        for row in rows:
            if cidade_f and cidade_f not in _to_text(row.get("cidade")).lower():
                continue
            if estado_f and estado_f not in _to_text(row.get("estado")).lower():
                continue
            out.append(row)
        out.sort(key=lambda item: _to_text(item.get("updated_at")), reverse=True)
        return out

    def record_terms_acceptance(
        self,
        *,
        user_id: str,
        versao: str,
        contexto: str,
        ip: str,
    ) -> Dict[str, Any]:
        payload = {
            "id": _gen_id("term"),
            "user_id": _to_text(user_id),
            "versao": _to_text(versao) or "v1",
            "contexto": _to_text(contexto),
            "ip": _to_text(ip),
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
            "status": STATUS_ACTIVE,
        }
        return self._save_row(TABLE_TERMOS, payload, prefix="term")

    def list_terms_acceptance(self, *, user_id: str = "") -> List[Dict[str, Any]]:
        rows = self._list_rows(TABLE_TERMOS, include_inactive=True)
        user = _to_text(user_id)
        if not user:
            return rows
        return [row for row in rows if _to_text(row.get("user_id")) == user]

    def set_item_status(self, module_name: str, item_id: str, status: str) -> bool:
        table = TABLES_MODULE.get(_to_text(module_name))
        if not table:
            return False
        if status not in {STATUS_ACTIVE, STATUS_PAUSED, STATUS_REMOVED}:
            return False
        return self._set_row_status(table, _to_text(item_id), status)


def build_empresa_activity_label(row: Dict[str, Any]) -> Tuple[str, str | None]:
    dt = _parse_dt(row.get("last_activity_at"))
    return get_status_atividade(dt)

