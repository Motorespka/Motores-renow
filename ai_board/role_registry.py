from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Literal

RoleName = Literal[
    "founder",
    "cto",
    "security",
    "qa",
    "performance",
    "product",
    "devops",
    "data_guardian",
    "ux",
    "risk",
    "advisor",
]

BASE_DIR = Path(__file__).resolve().parent
ROLE_DIR = BASE_DIR / "roles"


@dataclass(frozen=True)
class RolePermission:
    approval_required: bool
    allow_prod_write: bool
    security_review_required: bool


@dataclass(frozen=True)
class FallbackPolicy:
    allowed: bool
    require_explicit_approval: bool


@dataclass(frozen=True)
class RoleDefinition:
    name: RoleName
    env_var: str
    role_file: Path
    permissions: RolePermission
    fallback: FallbackPolicy
    criticality: int
    optional_reserve_env_var: str | None = None


ROLE_REGISTRY: Dict[RoleName, RoleDefinition] = {
    "founder": RoleDefinition(
        name="founder",
        env_var="AI_KEY_FOUNDER",
        role_file=ROLE_DIR / "founder.md",
        permissions=RolePermission(True, False, True),
        fallback=FallbackPolicy(allowed=False, require_explicit_approval=True),
        criticality=1,
        optional_reserve_env_var="AI_KEY_FOUNDER_RESERVE",
    ),
    "cto": RoleDefinition(
        name="cto",
        env_var="AI_KEY_CTO",
        role_file=ROLE_DIR / "cto.md",
        permissions=RolePermission(True, False, True),
        fallback=FallbackPolicy(allowed=True, require_explicit_approval=True),
        criticality=2,
        optional_reserve_env_var="AI_KEY_CTO_RESERVE",
    ),
    "security": RoleDefinition(
        name="security",
        env_var="AI_KEY_SECURITY",
        role_file=ROLE_DIR / "security.md",
        permissions=RolePermission(True, False, True),
        fallback=FallbackPolicy(allowed=False, require_explicit_approval=True),
        criticality=1,
        optional_reserve_env_var="AI_KEY_SECURITY_RESERVE",
    ),
    "qa": RoleDefinition(
        name="qa",
        env_var="AI_KEY_QA",
        role_file=ROLE_DIR / "qa.md",
        permissions=RolePermission(False, False, False),
        fallback=FallbackPolicy(allowed=True, require_explicit_approval=True),
        criticality=4,
        optional_reserve_env_var="AI_KEY_QA_RESERVE",
    ),
    "performance": RoleDefinition(
        name="performance",
        env_var="AI_KEY_PERFORMANCE",
        role_file=ROLE_DIR / "performance.md",
        permissions=RolePermission(False, False, False),
        fallback=FallbackPolicy(allowed=True, require_explicit_approval=True),
        criticality=4,
        optional_reserve_env_var="AI_KEY_PERFORMANCE_RESERVE",
    ),
    "product": RoleDefinition(
        name="product",
        env_var="AI_KEY_PRODUCT",
        role_file=ROLE_DIR / "product.md",
        permissions=RolePermission(False, False, False),
        fallback=FallbackPolicy(allowed=True, require_explicit_approval=True),
        criticality=5,
        optional_reserve_env_var="AI_KEY_PRODUCT_RESERVE",
    ),
    "devops": RoleDefinition(
        name="devops",
        env_var="AI_KEY_DEVOPS",
        role_file=ROLE_DIR / "devops.md",
        permissions=RolePermission(True, False, True),
        fallback=FallbackPolicy(allowed=False, require_explicit_approval=True),
        criticality=2,
        optional_reserve_env_var="AI_KEY_DEVOPS_RESERVE",
    ),
    "data_guardian": RoleDefinition(
        name="data_guardian",
        env_var="AI_KEY_DATA_GUARDIAN",
        role_file=ROLE_DIR / "data_guardian.md",
        permissions=RolePermission(True, False, True),
        fallback=FallbackPolicy(allowed=False, require_explicit_approval=True),
        criticality=2,
        optional_reserve_env_var="AI_KEY_DATA_GUARDIAN_RESERVE",
    ),
    "ux": RoleDefinition(
        name="ux",
        env_var="AI_KEY_UX",
        role_file=ROLE_DIR / "ux.md",
        permissions=RolePermission(False, False, False),
        fallback=FallbackPolicy(allowed=True, require_explicit_approval=True),
        criticality=5,
        optional_reserve_env_var="AI_KEY_UX_RESERVE",
    ),
    "risk": RoleDefinition(
        name="risk",
        env_var="AI_KEY_RISK",
        role_file=ROLE_DIR / "risk.md",
        permissions=RolePermission(True, False, True),
        fallback=FallbackPolicy(allowed=False, require_explicit_approval=True),
        criticality=1,
        optional_reserve_env_var="AI_KEY_RISK_RESERVE",
    ),
    "advisor": RoleDefinition(
        name="advisor",
        env_var="AI_KEY_ADVISOR",
        role_file=ROLE_DIR / "advisor.md",
        permissions=RolePermission(False, False, False),
        fallback=FallbackPolicy(allowed=True, require_explicit_approval=True),
        criticality=5,
        optional_reserve_env_var="AI_KEY_ADVISOR_RESERVE",
    ),
}


def get_role_definition(role: str) -> RoleDefinition:
    normalized = str(role or "").strip().lower()
    if normalized not in ROLE_REGISTRY:
        available = ", ".join(sorted(ROLE_REGISTRY))
        raise ValueError(f"Unknown role '{role}'. Available roles: {available}")
    return ROLE_REGISTRY[normalized]  # type: ignore[index]
