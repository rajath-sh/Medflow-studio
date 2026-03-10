"""
HealthOps Studio — Database Models (Full Schema)

TABLE MAP:
┌─────────────────────────────────────────────────────────────────┐
│  tenants ──┬── users ──┬── workflows ──┬── workflow_nodes      │
│            │           │               └── workflow_edges       │
│            │           └── jobs ──── job_logs                   │
│            │                                                    │
│            └── roles ── permissions                             │
│                                                                 │
│  audit_logs    ai_usage_logs    token_blacklist                 │
└─────────────────────────────────────────────────────────────────┘

KEY DESIGN DECISIONS:
1. UUIDs as primary keys — globally unique, non-guessable, safe for APIs
2. tenant_id on all data tables — enables multi-tenant isolation
3. created_at / updated_at / deleted_at — full audit trail + soft delete
4. Proper foreign keys — database enforces referential integrity
5. Enum types for constrained values (job status, node types, etc.)
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Float, Text, Boolean,
    ForeignKey, DateTime, Enum as SAEnum, JSON, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
import enum


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ENUMS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class JobStatus(str, enum.Enum):
    """Workflow execution job states."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class NodeType(str, enum.Enum):
    """Types of blocks a user can place on the workflow canvas."""
    DATA_SOURCE = "data_source"
    TRANSFORM = "transform"
    DESTINATION = "destination"
    API_ENDPOINT = "api_endpoint"
    TRIGGER = "trigger"


class AuditAction(str, enum.Enum):
    """What happened — used in audit logs."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    ROLE_CHANGE = "role_change"
    WORKFLOW_EXECUTE = "workflow_execute"
    AI_GENERATE = "ai_generate"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TIMESTAMP MIXIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TimestampMixin:
    """
    Every table gets these three columns:
    - created_at: set once at row creation
    - updated_at: auto-updated on every change
    - deleted_at: soft delete — row still exists but is "deleted"
    """
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TENANT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class Tenant(TimestampMixin, Base):
    """
    Multi-tenant isolation root.
    Every organization using the platform is a tenant.
    All user data is scoped to a tenant.
    """
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)

    # Relationships
    users = relationship("User", back_populates="tenant")
    workflows = relationship("Workflow", back_populates="tenant")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ROLE & PERMISSION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class Role(TimestampMixin, Base):
    """
    RBAC roles: SuperAdmin, Admin, Manager, Editor, Viewer, Guest.
    Roles are seeded at startup, not user-created.
    """
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255), nullable=True)

    # Relationships
    permissions = relationship("Permission", back_populates="role", cascade="all, delete-orphan")
    users = relationship("User", back_populates="role")


class Permission(Base):
    """
    Fine-grained permissions linked to roles.
    Format is verb:resource — e.g. "create:workflow", "read:patient", "execute:workflow".

    WHY verb:resource?
    Code checks `require_permission("create:workflow")` instead of role names.
    If you later restructure roles, you change the role↔permission mapping
    without touching any route code.
    """
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    resource = Column(String(100), nullable=False)  # e.g. "workflow", "patient"
    action = Column(String(100), nullable=False)        # e.g., "user.login", "create:patient"
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    role = relationship("Role", back_populates="permissions")

    # Unique constraint: a role can't have duplicate resource:action pairs
    __table_args__ = (
        Index("ix_permission_role_resource_action", "role_id", "resource", "action", unique=True),
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  USER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class User(TimestampMixin, Base):
    """
    Platform users. Key security decisions:
    - UUID primary key (non-guessable)
    - role_id FK instead of free-text role string
    - tenant_id for multi-tenant isolation
    - token_version: incremented on password change to invalidate all tokens
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=True, index=True)
    hashed_password = Column(String(255), nullable=False)

    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    # Token version — increment to invalidate all existing tokens for this user.
    # If the version in the JWT doesn't match the DB, the token is rejected.
    token_version = Column(Integer, default=1, nullable=False)

    # Relationships
    role = relationship("Role", back_populates="users")
    tenant = relationship("Tenant", back_populates="users")
    workflows = relationship("Workflow", back_populates="created_by_user")
    jobs = relationship("Job", back_populates="created_by_user")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  WORKFLOW + NODES + EDGES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class Workflow(TimestampMixin, Base):
    """
    A workflow designed in the visual editor.
    The full definition is stored as JSON (for flexibility),
    AND individual nodes/edges are stored in separate tables
    (for querying, validation, and future features).
    """
    __tablename__ = "workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    definition = Column(JSON, nullable=True)  # Full workflow JSON snapshot
    version = Column(String(20), default="1.0", nullable=False)

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    # Relationships
    created_by_user = relationship("User", back_populates="workflows")
    tenant = relationship("Tenant", back_populates="workflows")
    nodes = relationship("WorkflowNode", back_populates="workflow", cascade="all, delete-orphan")
    edges = relationship("WorkflowEdge", back_populates="workflow", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="workflow")

    # Index for common query: "list my workflows" sorted by date
    __table_args__ = (
        Index("ix_workflow_tenant_created", "tenant_id", "created_at"),
    )


class WorkflowNode(TimestampMixin, Base):
    """
    A single block on the workflow canvas.
    Config is JSON because different node types have different config shapes.
    Position is stored so we can restore the canvas layout on load.
    """
    __tablename__ = "workflow_nodes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    node_type = Column(SAEnum(NodeType), nullable=False)
    label = Column(String(255), nullable=True)
    config = Column(JSON, nullable=True)
    position = Column(JSON, nullable=True)  # {x: number, y: number}

    # Relationships
    workflow = relationship("Workflow", back_populates="nodes")


class WorkflowEdge(Base):
    """
    A connection between two nodes (Source → Target).
    Edges define the execution order of the pipeline.
    """
    __tablename__ = "workflow_edges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False)
    source_node_id = Column(UUID(as_uuid=True), ForeignKey("workflow_nodes.id", ondelete="CASCADE"), nullable=False)
    target_node_id = Column(UUID(as_uuid=True), ForeignKey("workflow_nodes.id", ondelete="CASCADE"), nullable=False)

    # Relationships
    workflow = relationship("Workflow", back_populates="edges")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  JOB EXECUTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class Job(TimestampMixin, Base):
    """
    A single execution of a workflow.
    Managed by Celery workers in Phase 2.
    """
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False)
    status = Column(SAEnum(JobStatus), default=JobStatus.PENDING, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0, nullable=False)
    idempotency_key = Column(String(255), unique=True, nullable=True)

    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    # Relationships
    workflow = relationship("Workflow", back_populates="jobs")
    created_by_user = relationship("User", back_populates="jobs")
    logs = relationship("JobLog", back_populates="job", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_job_tenant_status", "tenant_id", "status"),
    )


class JobLog(Base):
    """
    Execution logs for a job.
    Each step of the workflow produces log entries.
    """
    __tablename__ = "job_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False)
    level = Column(String(20), nullable=False)  # INFO, WARN, ERROR
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    job = relationship("Job", back_populates="logs")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TOKEN BLACKLIST
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class TokenBlacklist(Base):
    """
    Revoked JWT tokens tracked by their unique jti (JWT ID) claim.

    WHY NOT JUST SHORT EXPIRY?
    Short access tokens (10 min) limit blast radius, but for logout
    and password-change scenarios, we need to immediately invalidate
    tokens that are still within their expiry window.
    """
    __tablename__ = "token_blacklist"

    id = Column(Integer, primary_key=True, autoincrement=True)
    jti = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  REFRESH TOKEN FAMILY (for reuse detection)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class RefreshTokenFamily(Base):
    """
    Tracks refresh token rotation.

    HOW REUSE DETECTION WORKS:
    1. On login, a new token family is created with a family_id.
    2. Each refresh rotates: new refresh token with same family_id.
    3. We store the current valid jti in this table.
    4. If someone presents an OLD jti (already rotated), it means
       an attacker stole a token → we invalidate the ENTIRE family
       and force re-login.
    """
    __tablename__ = "refresh_token_families"

    id = Column(Integer, primary_key=True, autoincrement=True)
    family_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    current_jti = Column(String(255), nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  AUDIT LOG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class AuditLog(Base):
    """
    Immutable record of every significant action in the system.
    No update, no delete — append only.
    Audit logs are tamper-proof for compliance (HIPAA, SOC 2).
    """
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True) # Optional FK for system events
    tenant_id = Column(UUID(as_uuid=True), nullable=True) # Optional FK for global events
    action = Column(String(100), nullable=False)        # e.g., "user.login", "patient.read"
    resource = Column(String(100), nullable=True)       # e.g., "workflow", "patients/123"
    resource_id = Column(String(255), nullable=True)    # UUID or identifier of affected record
    status = Column(String(50), nullable=False)         # "success", "failure"
    details = Column(JSON, nullable=True)               # Extra context (diffs, etc)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_audit_tenant_action", "tenant_id", "action"),
        Index("ix_audit_user_created", "user_id", "created_at"),
        {'extend_existing': True}
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  AI USAGE LOG
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class AiUsageLog(Base):
    """
    Records LLM API token consumption for billing and monitoring.
    """
    __tablename__ = "ai_usage_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), index=True, nullable=False)
    request_id = Column(String(255), nullable=True)
    model = Column(String(100), nullable=False)
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    estimated_cost = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_ai_usage_user", "user_id"),
        Index("ix_ai_usage_created_at", "created_at"),
        {'extend_existing': True}
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PATIENT RECORD (domain-specific)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class PatientRecord(TimestampMixin, Base):
    """
    Sample healthcare domain table.
    """
    __tablename__ = "patients"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)
    height_cm = Column(Float, nullable=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)

    __table_args__ = (
        Index("ix_patient_tenant", "tenant_id"),
        {'extend_existing': True}
    )

