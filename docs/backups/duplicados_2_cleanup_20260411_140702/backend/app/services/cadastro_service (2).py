from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Tuple

from app.core.config import Settings
from app.integrations.supabase_rest import SupabaseRestClient, SupabaseRestError
from app.services.access_service import AccessContext
from app.services.technical_history_service import TechnicalHistoryService
from app.services.technical_parser import parse_technical_bobinagem

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "heic", "heif", "avif", "jfif"}
ALLOWED_MIME_PREFIX = "image/"


@dataclass
class UploadedImage:
    file_name: str
    mime_type: str
    data: bytes


class CadastroValidationError(ValueError):
    pass


class CadastroService:
    def __init__(self, settings: Settings, gateway: SupabaseRestClient):
        self.settings = settings
        self.gateway = gateway

    def validate_uploads(self, files: List[UploadedImage]) -> None:
        if not files:
            raise CadastroValidationError("Envie pelo menos 1 imagem.")
        if len(files) > max(1, int(self.settings.cadastro_max_files)):
            raise CadastroValidationError(
                f"Limite de arquivos excedido. Maximo: {self.settings.cadastro_max_files}."
            )

        max_file_bytes = int(self.settings.cadastro_max_file_size_mb) * 1024 * 1024
        max_total_bytes = int(self.settings.cadastro_max_total_size_mb) * 1024 * 1024

        total = 0
        for item in files:
            name = str(item.file_name or "").strip()
            mime = str(item.mime_type or "").strip().lower()
            data = item.data or b""

            total += len(data)
            if not name:
                raise CadastroValidationError("Arquivo sem nome nao e permitido.")
            if len(data) == 0:
                raise CadastroValidationError(f"Arquivo vazio: {name}")
            if len(data) > max_file_bytes:
                raise CadastroValidationError(
                    f"Arquivo '{name}' excede {self.settings.cadastro_max_file_size_mb}MB."
                )
            if not self._is_allowed_image(name=name, mime=mime):
                raise CadastroValidationError(
                    f"Tipo de arquivo nao permitido: {name} ({mime or 'mime-desconhecido'})."
                )

        if total > max_total_bytes:
            raise CadastroValidationError(
                f"Tamanho total excede {self.settings.cadastro_max_total_size_mb}MB."
            )

    async def analyze(
        self,
        *,
        access: AccessContext,
        files: List[UploadedImage],
    ) -> Dict[str, Any]:
        if not access.cadastro_allowed:
            raise PermissionError("Sem permissao de cadastro.")
        self.validate_uploads(files)

        extract_fn, normalize_fn = self._load_legacy_extractors()
        if self.settings.gemini_api_key:
            os.environ.setdefault("GEMINI_API_KEY", self.settings.gemini_api_key)
        if self.settings.gemini_model:
            os.environ.setdefault("GEMINI_MODEL", self.settings.gemini_model)

        file_payload = [
            {"name": f.file_name, "bytes": f.data, "mime_type": f.mime_type}
            for f in files
        ]
        extracted = extract_fn(file_payload)
        normalized = normalize_fn(extracted)
        normalized = self._apply_technical_layers(normalized)
        warnings: List[str] = []
        image_urls = await self._try_upload_images(access=access, files=files, warnings=warnings)

        return {
            "ok": True,
            "message": "Analise concluida.",
            "file_count": len(files),
            "file_names": [f.file_name for f in files],
            "image_urls": image_urls,
            "normalized_data": normalized,
            "warnings": warnings,
        }

    async def save(
        self,
        *,
        access: AccessContext,
        normalized_data: Dict[str, Any],
        file_names: List[str],
        image_urls: List[str],
    ) -> Dict[str, Any]:
        if not access.cadastro_allowed:
            raise PermissionError("Sem permissao de cadastro.")

        normalize_fn, to_legacy_payload, to_schema_payload, enrich_fn = self._load_legacy_savers()
        normalized = normalize_fn(normalized_data or {})
        normalized = enrich_fn(normalized, evento="cadastro")
        normalized = self._with_creator_metadata(normalized, access=access)
        normalized = self._apply_technical_layers(normalized)

        safe_file_names = [self._safe_file_name(name) for name in (file_names or []) if str(name or "").strip()]
        safe_urls = [str(url or "").strip() for url in (image_urls or []) if str(url or "").strip()]
        legacy_payload = to_legacy_payload(normalized, image_paths=safe_urls, image_names=safe_file_names)
        schema_payload = to_schema_payload(normalized, image_paths=safe_urls, image_names=safe_file_names)

        creator = access.display_name or access.email or access.user_id
        legacy_payload["observacoes"] = self._append_creator_note(legacy_payload.get("observacoes"), creator)

        strategies: List[Tuple[str, Dict[str, Any]]] = [
            ("legacy_token", legacy_payload),
            ("schema_token", schema_payload),
            (
                "fallback_token",
                {
                    "marca": legacy_payload.get("marca", ""),
                    "modelo": legacy_payload.get("modelo", ""),
                    "potencia": legacy_payload.get("potencia", ""),
                    "rpm": legacy_payload.get("rpm", ""),
                    "tensao": legacy_payload.get("tensao", ""),
                    "corrente": legacy_payload.get("corrente", ""),
                    "observacoes": legacy_payload.get("observacoes", ""),
                },
            ),
        ]

        warnings: List[str] = []
        row, strategy = await self._insert_with_strategies(
            token=access.token,
            strategies=strategies,
            warnings=warnings,
            use_service_role=False,
        )
        if not row and self.settings.supabase_service_role_key:
            row, strategy = await self._insert_with_strategies(
                token=None,
                strategies=[
                    ("legacy_service_role", legacy_payload),
                    ("schema_service_role", schema_payload),
                    ("fallback_service_role", strategies[-1][1]),
                ],
                warnings=warnings,
                use_service_role=True,
            )

        if not row:
            raise RuntimeError("Nao foi possivel salvar motor em nenhum formato compativel.")

        return {
            "ok": True,
            "message": "Motor salvo com sucesso.",
            "strategy": strategy,
            "inserted_id": row.get("id"),
            "warnings": warnings,
        }

    def _apply_technical_layers(self, normalized: Dict[str, Any]) -> Dict[str, Any]:
        try:
            out = json.loads(json.dumps(normalized or {}))
        except Exception:
            out = dict(normalized or {})

        oficina = out.get("oficina")
        if not isinstance(oficina, dict):
            oficina = {}

        try:
            parser_tecnico = parse_technical_bobinagem(out)
        except Exception as exc:
            parser_tecnico = {
                "espiras_bruto": [],
                "passo_bruto": [],
                "espiras_normalizado": [],
                "passo_normalizado": [],
                "confianca_dados": "baixa",
                "ligacao_tipo_eletrico": "",
                "ligacao_estrutura": "",
                "ligacao_observacao": "",
                "candidate_alternatives": [],
                "parse_note": f"falha no parser tecnico: {self._short_error(str(exc), max_len=120)}",
                "ambiguous": True,
                "needs_review": True,
                "status_revisao": "revisar",
            }

        office_status = "revisar" if parser_tecnico.get("needs_review") else "ok"
        oficina["parser_tecnico"] = parser_tecnico
        oficina["status_revisao"] = office_status

        # Nao ativar sugestao real no V20: manter candidates vazio.
        candidates: List[Dict[str, Any]] = []
        history_service = TechnicalHistoryService()
        oficina["sugestao_historica"] = history_service.build_suggestion(
            parser_tecnico=parser_tecnico,
            candidates=candidates,
        )

        out["oficina"] = oficina
        return out

    async def _insert_with_strategies(
        self,
        *,
        token: str | None,
        strategies: List[Tuple[str, Dict[str, Any]]],
        warnings: List[str],
        use_service_role: bool,
    ) -> Tuple[Dict[str, Any] | None, str]:
        for strategy, payload in strategies:
            try:
                rows = await self.gateway.insert(
                    "motores",
                    token=token,
                    use_service_role=use_service_role,
                    payload=payload,
                )
                if rows:
                    return rows[0], strategy
            except SupabaseRestError as exc:
                warnings.append(f"{strategy}: {self._short_error(exc.detail)}")
            except Exception as exc:
                warnings.append(f"{strategy}: {self._short_error(str(exc))}")
        return None, ""

    async def _try_upload_images(
        self,
        *,
        access: AccessContext,
        files: List[UploadedImage],
        warnings: List[str],
    ) -> List[str]:
        urls: List[str] = []
        bucket = str(self.settings.supabase_motores_bucket or "motores-imagens").strip()
        if not bucket:
            return urls

        for item in files:
            safe = self._safe_file_name(item.file_name)
            stamp = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            path = f"cadastro/{access.user_id}/{stamp}_{safe}"
            try:
                public_url = await self.gateway.upload_storage_object(
                    bucket=bucket,
                    path=path,
                    data=item.data,
                    content_type=item.mime_type or "application/octet-stream",
                    token=access.token,
                    use_service_role=bool(self.settings.supabase_service_role_key),
                )
                urls.append(public_url)
            except Exception as exc:
                warnings.append(f"upload:{safe} -> {self._short_error(str(exc))}")
        return urls

    @staticmethod
    def _append_creator_note(current: Any, creator: str) -> str:
        text = str(current or "").strip()
        suffix = f"Feito por: {creator}"
        if suffix.lower() in text.lower():
            return text
        if not text:
            return suffix
        return f"{text} | {suffix}"

    @staticmethod
    def _safe_file_name(file_name: str) -> str:
        base = str(file_name or "").replace("\\", "/").split("/")[-1].strip()
        safe = re.sub(r"[^a-zA-Z0-9._-]+", "_", base).strip("._")
        return safe or "upload.bin"

    @classmethod
    def _is_allowed_image(cls, *, name: str, mime: str) -> bool:
        extension = name.lower().rsplit(".", 1)[-1] if "." in name else ""
        by_ext = extension in ALLOWED_EXTENSIONS
        by_mime = mime.startswith(ALLOWED_MIME_PREFIX) if mime else False
        return by_ext or by_mime

    @staticmethod
    def _with_creator_metadata(payload: Dict[str, Any], *, access: AccessContext) -> Dict[str, Any]:
        try:
            enriched = json.loads(json.dumps(payload or {}))
        except Exception:
            enriched = dict(payload or {})

        meta = enriched.get("meta")
        if not isinstance(meta, dict):
            meta = {}
        meta.update(
            {
                "cadastrado_por_id": access.user_id,
                "cadastrado_por_email": access.email,
                "cadastrado_por_username": access.username,
                "cadastrado_por_nome": access.nome,
                "cadastrado_por_display": access.display_name,
                "cadastrado_em": datetime.now(tz=timezone.utc).isoformat(),
            }
        )
        enriched["meta"] = meta

        oficina = enriched.get("oficina")
        if not isinstance(oficina, dict):
            oficina = {}
        servico = oficina.get("servico_executado")
        if not isinstance(servico, dict):
            servico = {}
        if not str(servico.get("responsavel") or "").strip():
            servico["responsavel"] = access.display_name
        oficina["servico_executado"] = servico
        enriched["oficina"] = oficina
        return enriched

    @staticmethod
    def _short_error(message: str, max_len: int = 220) -> str:
        text = str(message or "").replace("\n", " ").strip()
        return text[:max_len] + ("..." if len(text) > max_len else "")

    @staticmethod
    def _load_legacy_extractors():
        root = Path(__file__).resolve().parents[3]
        root_str = str(root)
        if root_str not in sys.path:
            sys.path.insert(0, root_str)

        from services.gemini_oficina import extract_motor_data_with_gemini
        from services.oficina_parser import normalize_extracted_data

        return extract_motor_data_with_gemini, normalize_extracted_data

    @staticmethod
    def _load_legacy_savers():
        root = Path(__file__).resolve().parents[3]
        root_str = str(root)
        if root_str not in sys.path:
            sys.path.insert(0, root_str)

        from services.oficina_parser import (
            normalize_extracted_data,
            to_motores_schema_payload,
            to_supabase_payload,
        )
        from services.oficina_runtime import enriquecer_motor_oficina

        return (
            normalize_extracted_data,
            to_supabase_payload,
            to_motores_schema_payload,
            enriquecer_motor_oficina,
        )
