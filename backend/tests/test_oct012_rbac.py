"""OCT-012: RBAC role checks."""
import uuid

import pytest
from fastapi import HTTPException

from app.api.dependencies.auth import CurrentUser
from app.core.permissions.rbac import _check_role
from app.models.user import UserRole


def _user(role: UserRole) -> CurrentUser:
    return CurrentUser(user_id=uuid.uuid4(), role=role, username="test")


class TestRoleCheck:
    def test_admin_passes_all(self):
        u = _user(UserRole.ADMIN)
        _check_role(u, UserRole.ADMIN)
        _check_role(u, UserRole.OPERATOR)
        _check_role(u, UserRole.VIEWER)

    def test_operator_passes_operator_and_viewer(self):
        u = _user(UserRole.OPERATOR)
        _check_role(u, UserRole.OPERATOR)
        _check_role(u, UserRole.VIEWER)

    def test_operator_blocked_from_admin(self):
        u = _user(UserRole.OPERATOR)
        with pytest.raises(HTTPException) as exc:
            _check_role(u, UserRole.ADMIN)
        assert exc.value.status_code == 403

    def test_viewer_passes_viewer(self):
        u = _user(UserRole.VIEWER)
        _check_role(u, UserRole.VIEWER)

    def test_viewer_blocked_from_operator(self):
        u = _user(UserRole.VIEWER)
        with pytest.raises(HTTPException) as exc:
            _check_role(u, UserRole.OPERATOR)
        assert exc.value.status_code == 403

    def test_viewer_blocked_from_admin(self):
        u = _user(UserRole.VIEWER)
        with pytest.raises(HTTPException) as exc:
            _check_role(u, UserRole.ADMIN)
        assert exc.value.status_code == 403


class TestRbacDependencies:
    def test_require_role_returns_callable(self):
        from app.core.permissions.rbac import require_role
        dep = require_role(UserRole.ADMIN)
        assert callable(dep)

    def test_require_admin_importable(self):
        from app.core.permissions.rbac import require_admin
        assert callable(require_admin)

    def test_require_operator_importable(self):
        from app.core.permissions.rbac import require_operator
        assert callable(require_operator)
