from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = "dev"
    app_debug: bool = True
    app_name: str = "Uniao Motor API"
    api_prefix: str = "/api"

    backend_cors_origins: str = "http://localhost:3000"

    # Allow backend to boot without Supabase in local dev.
    # When missing, auth/protected endpoints will return 503 with clear message.
    supabase_url: str = Field(default="", alias="SUPABASE_URL")
    supabase_anon_key: str = Field(default="", alias="SUPABASE_ANON_KEY")
    supabase_service_role_key: str | None = Field(default=None, alias="SUPABASE_SERVICE_ROLE_KEY")

    default_paid_plans: str = "paid,pro,premium,enterprise,business"
    supabase_motores_bucket: str = "motores-imagens"

    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")

    cadastro_max_files: int = 5
    cadastro_max_file_size_mb: int = 12
    cadastro_max_total_size_mb: int = 40

    @property
    def cors_origins(self) -> List[str]:
        raw = self.backend_cors_origins or ""
        return [part.strip() for part in raw.replace(";", ",").split(",") if part.strip()]

    @property
    def paid_plans(self) -> set[str]:
        raw = self.default_paid_plans or ""
        return {part.strip().lower() for part in raw.replace(";", ",").split(",") if part.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()
