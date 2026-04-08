from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

DB = os.path.join("data", "motores.db")
STORAGE_ROOT = os.path.join("data", "dev_storage")

MOTORES_COLUMNS: Dict[str, str] = {
    "dados": "TEXT",
    "marca": "TEXT",
    "modelo": "TEXT",
    "potencia": "TEXT",
    "rpm": "TEXT",
    "tensao": "TEXT",
    "corrente": "TEXT",
    "observacoes": "TEXT",
    "dados_tecnicos_json": "TEXT",
    "leitura_gemini_json": "TEXT",
    "texto_bruto_extraido": "TEXT",
    "arquivo_origem": "TEXT",
    "imagens_origem": "TEXT",
    "imagens_urls": "TEXT",
    "bobinagem_principal_json": "TEXT",
    "bobinagem_auxiliar_json": "TEXT",
    "mecanica_json": "TEXT",
    "esquema_json": "TEXT",
    "created_at": "TEXT",
    "updated_at": "TEXT",
}

ORDENS_SERVICO_COLUMNS: Dict[str, str] = {
    "cliente": "TEXT",
    "marca": "TEXT",
    "potencia": "TEXT",
    "rpm": "TEXT",
    "tensao": "TEXT",
    "corrente": "TEXT",
    "diagnostico": "TEXT",
    "status": "TEXT",
    "created_at": "TEXT",
    "updated_at": "TEXT",
}

LIST_JSON_COLUMNS = {"imagens_origem", "imagens_urls"}
DICT_JSON_COLUMNS = {
    "dados_tecnicos_json",
    "leitura_gemini_json",
    "bobinagem_principal_json",
    "bobinagem_auxiliar_json",
    "mecanica_json",
    "esquema_json",
}
JSON_COLUMNS = LIST_JSON_COLUMNS | DICT_JSON_COLUMNS


def _now_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def _ensure_data_dir() -> None:
    os.makedirs("data", exist_ok=True)
    os.makedirs(STORAGE_ROOT, exist_ok=True)


def conectar(db_path: str = DB) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (table_name,),
    )
    return cur.fetchone() is not None


def _existing_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table_name})")
    return {str(row["name"]) for row in cur.fetchall()}


def _ensure_columns(
    conn: sqlite3.Connection,
    table_name: str,
    expected_columns: Dict[str, str],
) -> None:
    existing = _existing_columns(conn, table_name)
    cur = conn.cursor()
    for col, col_type in expected_columns.items():
        if col not in existing:
            # Nao destrutivo: apenas adiciona colunas ausentes.
            cur.execute(f"ALTER TABLE {table_name} ADD COLUMN {col} {col_type}")


def _ensure_base_tables(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS motores (
            id INTEGER PRIMARY KEY AUTOINCREMENT
        )
        """
    )
    _ensure_columns(conn, "motores", MOTORES_COLUMNS)

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS ordens_servico (
            id INTEGER PRIMARY KEY AUTOINCREMENT
        )
        """
    )
    _ensure_columns(conn, "ordens_servico", ORDENS_SERVICO_COLUMNS)

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios_app (
            id TEXT PRIMARY KEY,
            email TEXT,
            username TEXT,
            nome TEXT,
            created_at TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS arquivos_motor (
            id INTEGER PRIMARY KEY AUTOINCREMENT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS variaveis_motor (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            arquivo_id TEXT,
            bloco_id INTEGER,
            chave TEXT,
            valor TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE VIEW IF NOT EXISTS vw_consulta_motores AS
        SELECT * FROM motores
        """
    )
    conn.commit()


def criar_tabela() -> None:
    _ensure_data_dir()
    with conectar(DB) as conn:
        _ensure_base_tables(conn)


def bootstrap_database(db_path: str = DB) -> None:
    _ensure_data_dir()
    with conectar(db_path) as conn:
        _ensure_base_tables(conn)


def _serialize_value(column: str, value: Any) -> Any:
    if value is None:
        return None
    if column in JSON_COLUMNS:
        if isinstance(value, str):
            return value
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return value


def _deserialize_value(column: str, value: Any) -> Any:
    if column in LIST_JSON_COLUMNS:
        if value in (None, ""):
            return []
        if isinstance(value, list):
            return value
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        except Exception:
            return []
    if column in DICT_JSON_COLUMNS:
        if value in (None, ""):
            return {}
        if isinstance(value, dict):
            return value
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return value


def _normalize_row(table_name: str, row: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key, value in row.items():
        out[key] = _deserialize_value(key, value)
    return out


def _resolve_runtime_table(table_name: str) -> str:
    name = str(table_name or "").strip()
    if name == "vw_consulta_motores":
        return "motores"
    return name


@dataclass
class LocalQueryResult:
    data: List[Dict[str, Any]]


class LocalStorageBucket:
    def __init__(self, bucket_name: str):
        self.bucket_name = bucket_name

    def upload(self, path: str, file: bytes, file_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        target = os.path.join(STORAGE_ROOT, self.bucket_name, path.replace("/", os.sep))
        os.makedirs(os.path.dirname(target), exist_ok=True)
        payload = file if isinstance(file, (bytes, bytearray)) else bytes(file)
        with open(target, "wb") as fh:
            fh.write(payload)
        return {"path": path}

    def get_public_url(self, path: str) -> str:
        return f"local://{self.bucket_name}/{path}"


class LocalStorageClient:
    def from_(self, bucket_name: str) -> LocalStorageBucket:
        return LocalStorageBucket(bucket_name)


class LocalTableQuery:
    def __init__(self, client: "LocalRuntimeClient", table_name: str):
        self.client = client
        self.table_name = _resolve_runtime_table(table_name)
        self.operation = "select"
        self.payload: Any = None
        self.filters: List[Tuple[str, Any]] = []
        self.order_by: Optional[Tuple[str, bool]] = None
        self.limit_n: Optional[int] = None
        self.columns = "*"

    def select(self, columns: str = "*") -> "LocalTableQuery":
        self.operation = "select"
        self.columns = columns or "*"
        return self

    def insert(self, payload: Any) -> "LocalTableQuery":
        self.operation = "insert"
        self.payload = payload
        return self

    def update(self, payload: Dict[str, Any]) -> "LocalTableQuery":
        self.operation = "update"
        self.payload = payload
        return self

    def delete(self) -> "LocalTableQuery":
        self.operation = "delete"
        return self

    def eq(self, column: str, value: Any) -> "LocalTableQuery":
        self.filters.append((column, value))
        return self

    def order(self, column: str, desc: bool = False) -> "LocalTableQuery":
        self.order_by = (column, bool(desc))
        return self

    def limit(self, value: int) -> "LocalTableQuery":
        self.limit_n = int(value)
        return self

    def execute(self) -> LocalQueryResult:
        return self.client.execute_query(self)


class LocalRuntimeClient:
    def __init__(self, mode: str = "DEV", db_path: str = DB):
        self.mode = str(mode or "DEV").upper()
        self.db_path = db_path
        self.storage = LocalStorageClient()
        self.is_local_runtime = True
        self.is_dev_mode = self.mode == "DEV"
        self.is_fallback_mode = self.mode == "FALLBACK"
        bootstrap_database(db_path=self.db_path)

    def table(self, table_name: str) -> LocalTableQuery:
        return LocalTableQuery(self, table_name)

    def _existing_columns(self, table_name: str) -> set[str]:
        with conectar(self.db_path) as conn:
            if not _table_exists(conn, table_name):
                return set()
            return _existing_columns(conn, table_name)

    def execute_query(self, query: LocalTableQuery) -> LocalQueryResult:
        table_name = query.table_name
        with conectar(self.db_path) as conn:
            if not _table_exists(conn, table_name):
                return LocalQueryResult(data=[])

            if query.operation == "select":
                return self._execute_select(conn, query)
            if query.operation == "insert":
                return self._execute_insert(conn, query)
            if query.operation == "update":
                return self._execute_update(conn, query)
            if query.operation == "delete":
                return self._execute_delete(conn, query)
            return LocalQueryResult(data=[])

    def _apply_filters(self, query: LocalTableQuery, existing_cols: set[str]) -> Tuple[str, List[Any]]:
        clauses: List[str] = []
        params: List[Any] = []
        for col, val in query.filters:
            if col in existing_cols:
                clauses.append(f"{col} = ?")
                params.append(val)
        if not clauses:
            return "", params
        return " WHERE " + " AND ".join(clauses), params

    def _execute_select(self, conn: sqlite3.Connection, query: LocalTableQuery) -> LocalQueryResult:
        existing_cols = _existing_columns(conn, query.table_name)
        select_cols = query.columns.strip()
        if select_cols != "*":
            requested = [c.strip() for c in select_cols.split(",") if c.strip()]
            valid_requested = [c for c in requested if c in existing_cols]
            if valid_requested:
                select_cols = ", ".join(valid_requested)
            else:
                select_cols = "*"

        sql = f"SELECT {select_cols} FROM {query.table_name}"
        where_clause, params = self._apply_filters(query, existing_cols)
        sql += where_clause

        if query.order_by:
            col, desc = query.order_by
            if col in existing_cols:
                direction = "DESC" if desc else "ASC"
                sql += f" ORDER BY {col} {direction}"
        if query.limit_n is not None and query.limit_n > 0:
            sql += " LIMIT ?"
            params.append(query.limit_n)

        cur = conn.cursor()
        cur.execute(sql, params)
        rows = [dict(row) for row in cur.fetchall()]
        return LocalQueryResult(data=[_normalize_row(query.table_name, row) for row in rows])

    def _execute_insert(self, conn: sqlite3.Connection, query: LocalTableQuery) -> LocalQueryResult:
        payload = query.payload
        if payload is None:
            return LocalQueryResult(data=[])

        rows_to_insert = payload if isinstance(payload, list) else [payload]
        existing_cols = _existing_columns(conn, query.table_name)
        out_rows: List[Dict[str, Any]] = []
        now = _now_iso()

        cur = conn.cursor()
        for row in rows_to_insert:
            if not isinstance(row, dict):
                continue
            working = dict(row)
            if "created_at" in existing_cols and not working.get("created_at"):
                working["created_at"] = now
            if "updated_at" in existing_cols and not working.get("updated_at"):
                working["updated_at"] = now
            if "dados" in existing_cols and "dados" not in working and working:
                working["dados"] = json.dumps(working, ensure_ascii=False)

            filtered = {k: _serialize_value(k, v) for k, v in working.items() if k in existing_cols}
            if not filtered:
                continue
            cols = ", ".join(filtered.keys())
            placeholders = ", ".join(["?"] * len(filtered))
            values = list(filtered.values())
            cur.execute(
                f"INSERT INTO {query.table_name} ({cols}) VALUES ({placeholders})",
                values,
            )
            out_row = dict(row)
            out_row["id"] = cur.lastrowid
            out_rows.append(out_row)

        conn.commit()
        return LocalQueryResult(data=out_rows)

    def _execute_update(self, conn: sqlite3.Connection, query: LocalTableQuery) -> LocalQueryResult:
        if not isinstance(query.payload, dict):
            return LocalQueryResult(data=[])

        existing_cols = _existing_columns(conn, query.table_name)
        payload = dict(query.payload)
        if "updated_at" in existing_cols:
            payload["updated_at"] = _now_iso()
        filtered_payload = {k: _serialize_value(k, v) for k, v in payload.items() if k in existing_cols}
        if not filtered_payload:
            return LocalQueryResult(data=[])

        set_clause = ", ".join(f"{k} = ?" for k in filtered_payload.keys())
        values = list(filtered_payload.values())
        where_clause, where_values = self._apply_filters(query, existing_cols)
        if not where_clause:
            return LocalQueryResult(data=[])

        sql = f"UPDATE {query.table_name} SET {set_clause}{where_clause}"
        cur = conn.cursor()
        cur.execute(sql, values + where_values)
        conn.commit()
        return LocalQueryResult(data=[{"updated_rows": cur.rowcount}])

    def _execute_delete(self, conn: sqlite3.Connection, query: LocalTableQuery) -> LocalQueryResult:
        existing_cols = _existing_columns(conn, query.table_name)
        where_clause, where_values = self._apply_filters(query, existing_cols)
        if not where_clause:
            return LocalQueryResult(data=[])

        cur = conn.cursor()
        cur.execute(f"DELETE FROM {query.table_name}{where_clause}", where_values)
        conn.commit()
        return LocalQueryResult(data=[{"deleted_rows": cur.rowcount}])


def build_local_runtime_client(mode: str = "DEV", db_path: str = DB) -> LocalRuntimeClient:
    return LocalRuntimeClient(mode=mode, db_path=db_path)


def salvar_motor(motor: Dict[str, Any]) -> None:
    bootstrap_database()
    client = build_local_runtime_client(mode="DEV", db_path=DB)
    client.table("motores").insert(motor).execute()


def listar_motores() -> List[Dict[str, Any]]:
    bootstrap_database()
    client = build_local_runtime_client(mode="DEV", db_path=DB)
    res = client.table("motores").select("*").order("id", desc=True).execute()
    return res.data or []


def excluir_motor(id_motor: Any) -> None:
    bootstrap_database()
    client = build_local_runtime_client(mode="DEV", db_path=DB)
    client.table("motores").delete().eq("id", id_motor).execute()
