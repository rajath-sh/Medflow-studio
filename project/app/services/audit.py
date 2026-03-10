"""
HealthOps Studio — Audit Logging Service

Writes sensitive actions to the audit_logs table.
Used for compliance (HIPAA, SOC2) and security monitoring.
"""

from sqlalchemy.orm import Session
from fastapi import Request
import uuid
from app.db_models import AuditLog
from app.logging_config import get_logger

logger = get_logger("healthops.audit")

def log_audit_event(
    db: Session,
    request: Request,
    action: str,
    status: str,
    resource: str = None,
    user_id: str = None,
    tenant_id: str = None
):
    """
    Log an audit event to the database and structured logger.
    """
    try:
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")

        # Fallback to request state if not explicitly provided
        if not user_id and hasattr(request.state, "user_id"):
            user_id = request.state.user_id
            
        if hasattr(request.state, "user") and isinstance(request.state.user, dict):
            if not user_id:
                user_id = request.state.user.get("user_id")
            if not tenant_id:
                tenant_id = request.state.user.get("tenant_id")
                
        # Parse UUIDs safely
        safe_tenant_id = uuid.UUID(tenant_id) if tenant_id and isinstance(tenant_id, str) else tenant_id
        safe_user_id = uuid.UUID(user_id) if user_id and isinstance(user_id, str) else user_id

        audit_log = AuditLog(
            tenant_id=safe_tenant_id,
            user_id=safe_user_id,
            action=action,
            resource=resource,
            status=status,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.add(audit_log)
        db.commit()

        # Also emit to structured log for SIEM ingesting
        logger.info(
            f"Audit event: {action} ({status})",
            extra={
                "audit_action": action,
                "audit_status": status,
                "audit_resource": resource,
                "user_id": str(user_id) if user_id else None,
                "tenant_id": str(tenant_id) if tenant_id else None,
                "client_ip": ip_address
            }
        )
    except Exception as e:
        # Never fail a request just because audit logging failed, but do log the error
        logger.error(f"Failed to write audit log: {str(e)}")
