"""
HealthOps Studio -- Authorization Module (RBAC)

This module provides reusable FastAPI dependencies for:
1. Permission-based route protection: require_permission("create:workflow")
2. Tenant-scoped database queries: ensures users only see their own data
3. Object-level ownership checks

HOW IT WORKS:
- The JWT access token contains: sub (username), role, user_id, tenant_id
- get_current_user() (from security.py) extracts these claims
- require_permission() checks if the user's role has the needed permission
- The permission check hits the DB once and caches per-request

USAGE IN ROUTES:
    @router.post("/workflows")
    def create_workflow(
        user: dict = Depends(require_permission("create:workflow")),
        db: Session = Depends(get_db),
    ):
        # user is the JWT payload — guaranteed to have the permission
        ...
"""

from functools import lru_cache
from typing import Callable

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.db_models import Role, Permission
from app.security import get_current_user


# -- Permission Cache (per role) ------------------------------------------
# We cache (role_name -> set of permissions) so we don't query the DB
# on every single request. Cache is cleared on server restart.
_permission_cache: dict[str, set[str]] = {}


def _get_permissions_for_role(role_name: str, db: Session) -> set[str]:
    """
    Load all permissions for a role. Results are cached in memory.
    Returns a set like {"create:workflow", "read:patient", ...}
    """
    if role_name in _permission_cache:
        return _permission_cache[role_name]

    role = db.query(Role).filter(Role.name == role_name).first()
    if not role:
        _permission_cache[role_name] = set()
        return set()

    perms = db.query(Permission).filter(Permission.role_id == role.id).all()
    perm_set = {f"{p.action}:{p.resource}" for p in perms}

    _permission_cache[role_name] = perm_set
    return perm_set


# -- require_permission() -------------------------------------------------

def require_permission(permission: str) -> Callable:
    """
    FastAPI dependency factory.

    Usage:
        @router.get("/patients")
        def list_patients(user = Depends(require_permission("read:patient"))):
            ...

    If the user's role doesn't have the required permission,
    returns 403 Forbidden with a clear error message.
    """

    def _check_permission(
        current_user: dict = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> dict:
        role_name = current_user.get("role", "")

        # SuperAdmin bypasses all permission checks
        if role_name == "SuperAdmin":
            return current_user

        allowed = _get_permissions_for_role(role_name, db)

        if permission not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: '{permission}' required. Your role '{role_name}' does not have it.",
            )

        return current_user

    return _check_permission


# -- Tenant Scoping Helper ------------------------------------------------

def get_tenant_id(current_user: dict = Depends(get_current_user)) -> str:
    """
    Extract tenant_id from the JWT.
    Use this to filter all DB queries so users only see their own org's data.

    Usage:
        @router.get("/workflows")
        def list_workflows(
            tenant_id: str = Depends(get_tenant_id),
            db: Session = Depends(get_db),
        ):
            return db.query(Workflow).filter(Workflow.tenant_id == tenant_id).all()
    """
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tenant context. Contact admin.",
        )
    return tenant_id


# -- Convenience: get both user + tenant -----------------------------------

def get_auth_context(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Returns a dict with user_id, username, role, and tenant_id.
    A convenience wrapper for routes that need all auth context.
    """
    return {
        "user_id": current_user.get("user_id"),
        "username": current_user.get("sub"),
        "role": current_user.get("role"),
        "tenant_id": current_user.get("tenant_id"),
    }
