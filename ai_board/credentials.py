from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable

from ai_board.role_registry import RoleDefinition


class CredentialResolutionError(RuntimeError):
    """Credential could not be loaded for requested role."""


@dataclass(frozen=True)
class FallbackRequest:
    approved: bool
    reason: str
    primary_failure: str


@dataclass(frozen=True)
class CredentialResolution:
    role: str
    env_var: str
    used_fallback: bool
    fallback_from_env_var: str | None
    reason: str
    api_key: str


def _read_env_var(env_var: str, env_reader: Callable[[str], str | None]) -> str | None:
    value = env_reader(env_var)
    if value is None:
        return None
    value = value.strip()
    return value or None


def resolve_role_credentials(
    role_definition: RoleDefinition,
    *,
    env_reader: Callable[[str], str | None] | None = None,
    fallback_request: FallbackRequest | None = None,
) -> CredentialResolution:
    """
    Resolve role credential without leaking key in logs/errors.

    Missing primary key always raises. Fallback only occurs when explicitly
    approved and only for temporary primary runtime failures.
    """

    reader = env_reader or os.environ.get
    primary_value = _read_env_var(role_definition.env_var, reader)

    if primary_value is None:
        raise CredentialResolutionError(
            f"Missing required credential env var '{role_definition.env_var}' for role '{role_definition.name}'."
        )

    if fallback_request is None:
        return CredentialResolution(
            role=role_definition.name,
            env_var=role_definition.env_var,
            used_fallback=False,
            fallback_from_env_var=None,
            reason="primary",
            api_key=primary_value,
        )

    if not role_definition.fallback.allowed:
        raise CredentialResolutionError(
            f"Fallback denied for role '{role_definition.name}' by registry policy."
        )

    if role_definition.fallback.require_explicit_approval and not fallback_request.approved:
        raise CredentialResolutionError(
            f"Fallback denied for role '{role_definition.name}': explicit approval required."
        )

    if not fallback_request.primary_failure.strip():
        raise CredentialResolutionError(
            f"Fallback denied for role '{role_definition.name}': primary failure reason is required."
        )

    if not role_definition.optional_reserve_env_var:
        raise CredentialResolutionError(
            f"Fallback unavailable for role '{role_definition.name}': reserve env var not configured."
        )

    reserve_value = _read_env_var(role_definition.optional_reserve_env_var, reader)
    if reserve_value is None:
        raise CredentialResolutionError(
            f"Fallback requested for role '{role_definition.name}', but reserve env var "
            f"'{role_definition.optional_reserve_env_var}' is missing."
        )

    return CredentialResolution(
        role=role_definition.name,
        env_var=role_definition.optional_reserve_env_var,
        used_fallback=True,
        fallback_from_env_var=role_definition.env_var,
        reason=fallback_request.reason,
        api_key=reserve_value,
    )
