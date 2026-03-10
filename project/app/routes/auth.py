"""
HealthOps Studio — Auth Routes (Full Overhaul)

Endpoints:
  POST /auth/register  — Create account (assigned Viewer role)
  POST /auth/login     — Get access token + refresh cookie
  POST /auth/refresh   — Rotate refresh token (from cookie)
  POST /auth/logout    — Blacklist tokens + clear cookie
  GET  /auth/me        — Get current user info

SECURITY FEATURES:
- Passwords hashed with Argon2id + pepper
- Access tokens: RS256 JWT, 10 min expiry, stored in-memory by frontend
- Refresh tokens: RS256 JWT, 14 day expiry, HttpOnly cookie
- Refresh token rotation: each refresh invalidates the old token
- Reuse detection: if a rotated token is reused, entire family is killed
- Token blacklisting: via the TokenBlacklist table
"""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, Response, Request, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.services.audit import log_audit_event

from app.dependencies import get_db
from app.db_models import User, Role, Tenant, RefreshTokenFamily, TokenBlacklist
from app.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
    set_refresh_cookie, clear_refresh_cookie,
    get_current_user,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


# ── Request/Response Models ──────────────────────────────

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6, max_length=128,
                          description="Minimum 6 characters (will enforce 12 with frontend validation)")

class LoginRequest(BaseModel):
    username: str
    password: str


# ── REGISTER ─────────────────────────────────────────────

@router.post("/register", status_code=201)
def register(request: Request, data: RegisterRequest, db: Session = Depends(get_db)):
    """
    Create a new user with Viewer role.
    Role is NOT selectable — prevents privilege escalation.
    """
    # Check if username exists
    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        log_audit_event(db, request, "user.register", "failure", f"username:{data.username}", tenant_id=None)
        raise HTTPException(status_code=400, detail="Username already taken")

    # Get default role + tenant
    viewer_role = db.query(Role).filter(Role.name == "Viewer").first()
    default_tenant = db.query(Tenant).first()
    if not viewer_role or not default_tenant:
        raise HTTPException(status_code=500, detail="Run seed first (python -m app.seed)")

    user = User(
        username=data.username,
        hashed_password=hash_password(data.password),
        role_id=viewer_role.id,
        tenant_id=default_tenant.id,
    )
    db.add(user)
    db.commit()

    log_audit_event(db, request, "user.register", "success", str(user.id), user_id=str(user.id), tenant_id=str(default_tenant.id))

    return {"message": "User registered successfully"}


# ── LOGIN ────────────────────────────────────────────────

@router.post("/login")
def login(request: Request, data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """
    Authenticate user and return:
    - Access token in response body (frontend stores in memory)
    - Refresh token in HttpOnly cookie (browser manages automatically)
    """
    user = db.query(User).filter(User.username == data.username).first()
    if not user or not verify_password(data.password, user.hashed_password):
        log_audit_event(db, request, "user.login", "failure", f"username:{data.username}", tenant_id=None)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Load role name for JWT claims
    role = db.query(Role).filter(Role.id == user.role_id).first()
    role_name = role.name if role else "Viewer"

    # Create access token
    access_token = create_access_token({
        "sub": user.username,
        "user_id": str(user.id),
        "role": role_name,
        "tenant_id": str(user.tenant_id),
    })

    # Create refresh token + store its family in DB
    refresh_token, jti, family_id = create_refresh_token(str(user.id))

    from datetime import timedelta
    from app.config import get_settings
    s = get_settings()
    family = RefreshTokenFamily(
        family_id=family_id,
        user_id=user.id,
        current_jti=jti,
        expires_at=datetime.now(timezone.utc) + timedelta(days=s.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(family)
    db.commit()

    # Set refresh token as HttpOnly cookie
    set_refresh_cookie(response, refresh_token)

    log_audit_event(db, request, "user.login", "success", str(user.id), user_id=str(user.id), tenant_id=str(user.tenant_id))

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": role_name,
    }


# ── REFRESH ──────────────────────────────────────────────

@router.post("/refresh")
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    """
    Rotate the refresh token:
    1. Read old refresh token from cookie
    2. Verify it's valid and matches the current family jti
    3. Issue a new access + refresh token
    4. Invalidate the old refresh token

    If an ALREADY-ROTATED token is presented (reuse attack):
    → Kill the entire token family → force re-login
    """
    raw_token = request.cookies.get("refresh_token")
    if not raw_token:
        raise HTTPException(status_code=401, detail="No refresh token")

    payload = decode_token(raw_token)

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    family_id = payload.get("family_id")
    jti = payload.get("jti")
    user_id = payload.get("sub")

    # Look up the token family
    family = db.query(RefreshTokenFamily).filter(
        RefreshTokenFamily.family_id == family_id,
        RefreshTokenFamily.is_revoked == False,
    ).first()

    if not family:
        # Family doesn't exist or was invalidated → possible reuse attack
        raise HTTPException(status_code=401, detail="Token family invalidated. Please log in again.")

    # Check if this is the CURRENT token for this family
    if family.current_jti != jti:
        # REUSE DETECTED — someone is using an old, rotated token!
        # Kill the entire family to protect the user.
        family.is_revoked = True
        db.commit()
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=401,
            detail="Token reuse detected. All sessions invalidated. Please log in again."
        )

    # Load user info for new tokens
    user = db.query(User).filter(User.id == family.user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    role = db.query(Role).filter(Role.id == user.role_id).first()
    role_name = role.name if role else "Viewer"

    # Issue new access token
    new_access = create_access_token({
        "sub": user.username,
        "user_id": str(user.id),
        "role": role_name,
        "tenant_id": str(user.tenant_id),
    })

    # Issue new refresh token (same family, new jti)
    new_refresh, new_jti, _ = create_refresh_token(str(user.id), family_id=family_id)

    # Rotate: update the family's current jti
    family.current_jti = new_jti
    db.commit()

    set_refresh_cookie(response, new_refresh)

    return {
        "access_token": new_access,
        "token_type": "bearer",
        "role": role_name,
    }


# ── LOGOUT ───────────────────────────────────────────────

@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    """
    Invalidate refresh token family + blacklist the access token.
    """
    # Invalidate refresh token family if present
    raw_token = request.cookies.get("refresh_token")
    if raw_token:
        try:
            payload = decode_token(raw_token)
            family_id = payload.get("family_id")
            if family_id:
                family = db.query(RefreshTokenFamily).filter(
                    RefreshTokenFamily.family_id == family_id
                ).first()
                if family:
                    family.is_valid = False
                    db.commit()
        except Exception:
            pass  # Token might already be expired
        clear_refresh_cookie(response)

    # Blacklist the access token if provided
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        access_token = auth_header[7:]
        try:
            payload = decode_token(access_token)
            blacklist_entry = TokenBlacklist(
                jti=payload["jti"],
                expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            )
            db.add(blacklist_entry)
            db.commit()
        except Exception:
            pass

    return {"message": "Logged out successfully"}


# ── GET CURRENT USER ─────────────────────────────────────

@router.get("/me")
def get_me(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    """Return profile info for the authenticated user."""
    user = db.query(User).filter(User.username == current_user["sub"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    role = db.query(Role).filter(Role.id == user.role_id).first()

    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "role": role.name if role else "Viewer",
        "tenant_id": str(user.tenant_id),
    }
