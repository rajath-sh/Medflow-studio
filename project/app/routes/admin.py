"""
Admin routes -- SuperAdmin/Admin only.
Provides role management, user listing, and system audit logs.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.dependencies import get_db
from app.db_models import User, Role, Permission, AuditLog
from app.authorization import require_permission

router = APIRouter(prefix="/admin", tags=["Admin"])


# ── LIST USERS ────────────────────────────────────────────

@router.get("/users")
def list_users(
    user: dict = Depends(require_permission("read:user")),
    db: Session = Depends(get_db),
):
    users = db.query(User).filter(User.deleted_at.is_(None)).all()
    result = []
    for u in users:
        role = db.query(Role).filter(Role.id == u.role_id).first()
        result.append({
            "id": str(u.id),
            "username": u.username,
            "email": u.email,
            "role": role.name if role else "Unknown",
            "created_at": str(u.created_at),
        })
    return result


# ── ASSIGN ROLE ───────────────────────────────────────────

class RoleAssignRequest(BaseModel):
    user_id: str
    role_name: str


@router.post("/assign-role")
def assign_role(
    data: RoleAssignRequest,
    admin: dict = Depends(require_permission("assign:role")),
    db: Session = Depends(get_db),
):
    """Only users with assign:role permission (Admin, SuperAdmin) can change roles."""
    target_user = db.query(User).filter(User.id == data.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    new_role = db.query(Role).filter(Role.name == data.role_name).first()
    if not new_role:
        raise HTTPException(status_code=400, detail=f"Role '{data.role_name}' not found")

    # Prevent non-SuperAdmins from assigning SuperAdmin
    if data.role_name == "SuperAdmin" and admin.get("role") != "SuperAdmin":
        raise HTTPException(status_code=403, detail="Only SuperAdmin can assign SuperAdmin role")

    target_user.role_id = new_role.id
    db.commit()

    return {"message": f"User '{target_user.username}' assigned role '{data.role_name}'"}


# ── LIST ROLES ────────────────────────────────────────────

@router.get("/roles")
def list_roles(
    user: dict = Depends(require_permission("read:user")),
    db: Session = Depends(get_db),
):
    roles = db.query(Role).all()
    result = []
    for role in roles:
        perms = db.query(Permission).filter(Permission.role_id == role.id).all()
        result.append({
            "id": role.id,
            "name": role.name,
            "description": role.description,
            "permissions": [f"{p.action}:{p.resource}" for p in perms],
        })
    return result


# ── AUDIT LOGS ────────────────────────────────────────────

@router.get("/audit-logs")
def get_audit_logs(
    user: dict = Depends(require_permission("read:audit")),
    db: Session = Depends(get_db),
    limit: int = 50,
):
    logs = db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).all()
    return [
        {
            "id": str(log.id),
            "user_id": str(log.user_id) if log.user_id else None,
            "action": log.action,
            "resource": log.resource,
            "resource_id": log.resource_id,
            "details": log.details,
            "ip_address": log.ip_address,
            "created_at": str(log.created_at),
        }
        for log in logs
    ]
