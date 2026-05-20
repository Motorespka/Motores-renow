from __future__ import annotations

import importlib.util
import sys
import types
from dataclasses import asdict
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[3]


def _import_repo_module(module_name: str, rel_path: str):
    if module_name in sys.modules:
        return sys.modules[module_name]
    path = _REPO_ROOT / rel_path
    spec = importlib.util.spec_from_file_location(
        module_name,
        path,
        submodule_search_locations=[str(path.parent)],
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Nao foi possivel carregar {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


_search_lib = _import_repo_module("mrw_search_lib", "app/search_lib.py")
_app_pkg = types.ModuleType("app")
_app_pkg.search_lib = _search_lib  # type: ignore[attr-defined]
sys.modules.setdefault("app", _app_pkg)
sys.modules["app.search_lib"] = _search_lib
_oficial_engine = _import_repo_module("mrw_oficial_engine", "app/oficial_engine.py")

DEFAULT_DB = _oficial_engine.DEFAULT_DB
load_catalog = _oficial_engine.load_catalog
save_official_calculation = _oficial_engine.save_official_calculation
suggest_calculation = _oficial_engine.suggest_calculation
filter_file = _oficial_engine.filter_file
parse_scalar = _search_lib.parse_scalar


class OficialCalculoService:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or DEFAULT_DB

    def stats(self) -> dict[str, Any]:
        motors, meta = load_catalog(self.db_path)
        file_n = sum(1 for m in motors if getattr(m, "is_file", 0))
        if not file_n:
            file_n = len(filter_file(motors))
        return {
            "oficial_total": len(motors),
            "file_complete": file_n,
            "with_geometry": int(meta.get("with_geometry", 0) or 0),
            "index_generated_at": meta.get("generated_at", ""),
        }

    def suggest(self, payload: dict[str, Any]) -> dict[str, Any]:
        motors, _ = load_catalog(self.db_path)
        ranh = payload.get("ranhuras")
        pol = payload.get("polos")
        sug = suggest_calculation(
            motors,
            diametro_mm=float(payload["diametro_mm"]),
            pacote_mm=float(payload["pacote_mm"]),
            carcaca=str(payload.get("carcaca", "")),
            passo=str(payload.get("passo", "")),
            tipo_bobinagem=str(payload.get("tipo_bobinagem", "")),
            ligacao=str(payload.get("ligacao", "")),
            fio_engenheiro=str(payload.get("fio_engenheiro", "")),
            espiras_engenheiro=str(payload.get("espiras_engenheiro", "")),
            ranhuras=int(ranh) if ranh is not None and str(ranh).strip() else None,
            polos=int(pol) if pol is not None and str(pol).strip() else None,
            top_k=5,
            use_gemini=True,
        )

        out = asdict(sug)
        out["modo_processamento"] = sug.modo_processamento
        out["validation_status"] = sug.validation_status or "REVISAR"
        out["validation_message"] = sug.validation_message or sug.alerta_risco or ""
        out["lei_ranhura_logs"] = sug.lei_ranhura_logs
        out["media_historica_espiras"] = sug.media_historica_espiras
        out["slot_fill_limit"] = sug.slot_fill_limit
        out["slot_fill_actual"] = sug.slot_fill_actual

        eng_esp = parse_scalar(str(payload.get("espiras_engenheiro", "")))
        if eng_esp and sug.sugestao_espira and out["validation_status"] == "APROVADO":
            tol = max(sug.sugestao_espira * 0.15, 2.0)
            if abs(eng_esp - sug.sugestao_espira) > tol:
                out["validation_status"] = "ATENCAO"
                out["validation_message"] = (
                    f"Sua espira ({eng_esp}) diverge da sugestao ({sug.sugestao_espira})."
                )
        return out

    def save_oficial(self, payload: dict[str, Any]) -> dict[str, Any]:
        return save_official_calculation(payload, db_path=self.db_path)
