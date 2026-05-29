"""RBAC — role-based access control dependencies.

Roles (ascending privilege): viewer < operator < admin.
Viewers can only read. Operators can read+write. Admins have full access.
"""
from __future__ import annotations

from fastapi import Depends, HTTPException, status

from app.api.dependencies.auth import CurrentUser, get_current_user
from app.models.user import UserRole

# Privilege ordering
_ROLE_RANK: dict[UserRole, int] = {
    UserRole.VIEWER: 0,
    UserRole.OPERATOR: 1,
    UserRole.ADMIN: 2,
}


def _check_role(user: CurrentUser, minimum_role: UserRole) -> None:
    if _ROLE_RANK[user.role] < _ROLE_RANK[minimum_role]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Requires role '{minimum_role.value}' or higher",
        )


def require_role(minimum_role: UserRole):
    """Return a FastAPI dependency that enforces a minimum role."""
    async def _dep(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        _check_role(user, minimum_role)
        return user
    return _dep


def require_admin(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    _check_role(user, UserRole.ADMIN)
    return user


def require_operator(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    _check_role(user, UserRole.OPERATOR)
    return user


def tenant_filter(company_id_param: str | None = None) -> None:
    """
    Placeholder dependency for tenant isolation.
    Routes that return company/program data must filter by tenant.
    Used as a reminder at the route level; actual filtering is in repositories.
    """
