"""
HealthOps Studio — Pydantic Schemas (Request/Response Models)

WHY SEPARATE FROM DB MODELS?
- DB models define what's stored (SQLAlchemy ↔ PostgreSQL)
- Schemas define what's sent/received via HTTP (Pydantic ↔ JSON)

This separation lets you:
1. Hide sensitive fields (hashed_password never in responses)
2. Validate input more strictly than the DB requires
3. Version your API independently from the DB schema
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  AUTH
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class RegisterRequest(BaseModel):
    """
    Registration input.
    NOTE: No role field — users are assigned "Viewer" by default.
    Only admins can promote users. This prevents privilege escalation.
    """
    username: str = Field(..., min_length=3, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    password: str = Field(..., min_length=12, max_length=128,
                          description="Minimum 12 characters for security")


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    """Returned on login/refresh. Refresh token is set as HttpOnly cookie, not in body."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until access token expiry


class UserResponse(BaseModel):
    """Public user profile — never includes password or internal IDs."""
    id: UUID
    username: str
    email: Optional[str] = None
    role: str  # role name, e.g. "Admin"
    tenant_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PATIENTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class PatientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    age: Optional[int] = Field(None, ge=0, le=200)
    gender: Optional[str] = Field(None, max_length=20)
    height_cm: Optional[float] = Field(None, ge=0, le=300)


class PatientResponse(BaseModel):
    id: UUID
    patient_id: str
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  WORKFLOWS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class WorkflowNodeSchema(BaseModel):
    """A single block on the canvas."""
    id: str
    type: str
    label: Optional[str] = None
    config: Optional[dict] = None
    position: Optional[dict] = None  # {x, y}


class WorkflowEdgeSchema(BaseModel):
    """A connection between two nodes."""
    source: str  # node id
    target: str  # node id


class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    nodes: list[WorkflowNodeSchema] = []
    edges: list[WorkflowEdgeSchema] = []


class WorkflowResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str] = None
    version: str
    nodes: list[WorkflowNodeSchema] = []
    edges: list[WorkflowEdgeSchema] = []
    created_by: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkflowListItem(BaseModel):
    """Lightweight response for listing workflows (no nodes/edges)."""
    id: UUID
    name: str
    description: Optional[str] = None
    version: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  JOBS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class JobResponse(BaseModel):
    id: UUID
    workflow_id: UUID
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    retry_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobLogResponse(BaseModel):
    level: str
    message: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  ADMIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class RoleAssignRequest(BaseModel):
    """Assign a role to a user (admin only)."""
    user_id: UUID
    role_name: str


class RoleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    permissions: list[str] = []  # ["create:workflow", "read:patient", ...]

    model_config = ConfigDict(from_attributes=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  AUDIT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class AuditLogResponse(BaseModel):
    id: UUID
    user_id: Optional[UUID] = None
    action: str
    resource: Optional[str] = None
    resource_id: Optional[str] = None
    details: Optional[dict] = None
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  AI USAGE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class AIUsageResponse(BaseModel):
    model: str
    input_tokens: int
    output_tokens: int
    estimated_cost: Optional[float] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
