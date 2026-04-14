from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from ai_board.credentials import (
    CredentialResolution,
    CredentialResolutionError,
    FallbackRequest,
    resolve_role_credentials,
)
from ai_board.role_registry import RoleDefinition, get_role_definition

logger = logging.getLogger(__name__)


class GovernanceViolation(RuntimeError):
    """Raised when governance gates reject role runtime initialization."""


@dataclass(frozen=True)
class RoleRuntime:
    role: str
    role_file: Path
    role_prompt: str
    env_var_used: str
    api_key: str
    permissions: dict[str, Any]
    criticality: int
    audit: dict[str, Any]


ApprovalGate = Callable[[RoleDefinition], bool]
PolicyEngine = Callable[[RoleDefinition], bool]
KillSwitch = Callable[[], bool]


@dataclass(frozen=True)
class RuntimeFallback:
    approved: bool
    reason: str
    primary_failure: str


def _default_approval_gate(_role_def: RoleDefinition) -> bool:
    return True


def _default_policy_engine(_role_def: RoleDefinition) -> bool:
    return True


def _default_kill_switch() -> bool:
    return False


def _load_role_prompt(role_file: Path) -> str:
    if not role_file.exists():
        raise FileNotFoundError(f"Role prompt file not found: {role_file}")
    return role_file.read_text(encoding="utf-8")


def _audit_log(event: str, payload: dict[str, Any]) -> None:
    safe_payload = {
        "event": event,
        "role": payload.get("role"),
        "env_var": payload.get("env_var"),
        "used_fallback": payload.get("used_fallback"),
        "fallback_from_env_var": payload.get("fallback_from_env_var"),
        "reason": payload.get("reason"),
        "status": payload.get("status"),
    }
    logger.info("ai_role_runtime", extra={"audit": safe_payload})


def resolve_role_credentials_by_name(
    role: str,
    *,
    fallback: RuntimeFallback | None = None,
) -> CredentialResolution:
    role_def = get_role_definition(role)
    fallback_request = None
    if fallback is not None:
        fallback_request = FallbackRequest(
            approved=fallback.approved,
            reason=fallback.reason,
            primary_failure=fallback.primary_failure,
        )
    return resolve_role_credentials(role_def, fallback_request=fallback_request)


def get_role_runtime(
    role: str,
    *,
    fallback: RuntimeFallback | None = None,
    approval_gate: ApprovalGate | None = None,
    policy_engine: PolicyEngine | None = None,
    kill_switch: KillSwitch | None = None,
) -> RoleRuntime:
    role_def = get_role_definition(role)

    gate = approval_gate or _default_approval_gate
    policy = policy_engine or _default_policy_engine
    kill = kill_switch or _default_kill_switch

    if kill():
        raise GovernanceViolation("AI execution blocked by kill switch.")
    if not policy(role_def):
        raise GovernanceViolation(f"Policy engine rejected role '{role_def.name}'.")
    if role_def.permissions.approval_required and not gate(role_def):
        raise GovernanceViolation(f"Approval gate rejected role '{role_def.name}'.")

    prompt = _load_role_prompt(role_def.role_file)

    fallback_request = None
    if fallback is not None:
        fallback_request = FallbackRequest(
            approved=fallback.approved,
            reason=fallback.reason,
            primary_failure=fallback.primary_failure,
        )

    try:
        credential: CredentialResolution = resolve_role_credentials(
            role_def,
            fallback_request=fallback_request,
        )
        status = "ok"
    except CredentialResolutionError:
        _audit_log(
            "credential_resolution_failed",
            {
                "role": role_def.name,
                "env_var": role_def.env_var,
                "used_fallback": fallback is not None,
                "fallback_from_env_var": role_def.env_var if fallback is not None else None,
                "reason": fallback.reason if fallback is not None else "missing_or_invalid_credential",
                "status": "error",
            },
        )
        raise

    audit = {
        "role": role_def.name,
        "env_var": credential.env_var,
        "used_fallback": credential.used_fallback,
        "fallback_from_env_var": credential.fallback_from_env_var,
        "reason": credential.reason,
        "status": status,
    }
    _audit_log("credential_resolution", audit)

    return RoleRuntime(
        role=role_def.name,
        role_file=role_def.role_file,
        role_prompt=prompt,
        env_var_used=credential.env_var,
        api_key=credential.api_key,
        permissions={
            "approval_required": role_def.permissions.approval_required,
            "allow_prod_write": role_def.permissions.allow_prod_write,
            "security_review_required": role_def.permissions.security_review_required,
            "allow_fallback": role_def.fallback.allowed,
            "fallback_requires_approval": role_def.fallback.require_explicit_approval,
        },
        criticality=role_def.criticality,
        audit=audit,
    )
