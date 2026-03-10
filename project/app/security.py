"""
HealthOps Studio — Security Module (Argon2id + RS256 JWT)

WHAT CHANGED FROM THE ORIGINAL:
1. Password hashing: bcrypt -> Argon2id (OWASP-recommended, memory-hard)
2. JWT algorithm: HS256 (shared secret) -> RS256 (asymmetric key pair)
3. Added: refresh tokens, token blacklisting, token families for reuse detection
4. Removed: hardcoded SECRET_KEY

WHY RS256?
- Private key signs tokens (only the auth server needs it)
- Public key verifies tokens (any service can verify without the secret)
- If you scale to microservices, they only need the public key.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.config import get_settings
from app.dependencies import get_db

settings = get_settings()

# ── Password Hashing (Argon2id) ─────────────────────────
# Argon2id is the winner of the Password Hashing Competition.
# It's memory-hard, meaning attackers can't just throw GPUs at it.
# The default parameters (time_cost=3, memory_cost=65536, parallelism=4)
# are tuned for a good balance of security vs login speed.
ph = PasswordHasher()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def hash_password(password: str) -> str:
    """
    Hash a password with Argon2id + optional pepper.
    The pepper is mixed in before hashing so even if the database leaks,
    the attacker also needs the pepper (stored as an env var) to crack passwords.
    """
    peppered = password + settings.PASSWORD_PEPPER
    return ph.hash(peppered)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    Handles BOTH Argon2id (new) and bcrypt (legacy) hashes for
    backward compatibility during the migration period.
    """
    # Legacy bcrypt hash (from before the Argon2id switch)
    if hashed_password.startswith("$2b$") or hashed_password.startswith("$2a$"):
        from passlib.context import CryptContext
        legacy_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
        # Old users had no pepper — try without first, then with
        if legacy_ctx.verify(plain_password, hashed_password):
            return True
        return legacy_ctx.verify(plain_password + settings.PASSWORD_PEPPER, hashed_password)

    # Argon2id hash (current)
    peppered = plain_password + settings.PASSWORD_PEPPER
    try:
        return ph.verify(hashed_password, peppered)
    except (VerifyMismatchError, Exception):
        return False


# ── JWT Token Creation (RS256) ───────────────────────────

def _load_private_key() -> str:
    """Load the RSA private key, handling \\n escapes from .env files."""
    key = settings.JWT_PRIVATE_KEY
    if not key:
        raise RuntimeError("JWT_PRIVATE_KEY not set. Generate keys first (see .env.template).")
    return key.replace("\\n", "\n")


def _load_public_key() -> str:
    """Load the RSA public key, handling \\n escapes from .env files."""
    key = settings.JWT_PUBLIC_KEY
    if not key:
        raise RuntimeError("JWT_PUBLIC_KEY not set. Generate keys first (see .env.template).")
    return key.replace("\\n", "\n")


def create_access_token(data: dict) -> str:
    """
    Create a short-lived access token (10 min).

    Claims included:
    - sub: username (subject)
    - role: user's role name
    - jti: unique token ID (for blacklisting)
    - exp: expiry timestamp
    - type: "access"
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    to_encode.update({
        "jti": str(uuid.uuid4()),
        "exp": now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": now,
        "type": "access",
    })
    return jwt.encode(to_encode, _load_private_key(), algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str, family_id: Optional[str] = None) -> tuple[str, str, str]:
    """
    Create a long-lived refresh token (14 days).

    Returns: (token_string, jti, family_id)

    HOW REFRESH TOKEN FAMILIES WORK:
    1. On first login, a new family_id is created.
    2. On each refresh, a new token is created with the SAME family_id
       but a NEW jti.
    3. The DB stores which jti is currently valid for each family.
    4. If an OLD jti is presented (already rotated), it means theft:
       → Invalidate the entire family → force re-login.
    """
    jti = str(uuid.uuid4())
    fam_id = family_id or str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    payload = {
        "sub": user_id,
        "jti": jti,
        "family_id": fam_id,
        "exp": now + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        "iat": now,
        "type": "refresh",
    }
    token = jwt.encode(payload, _load_private_key(), algorithm=settings.JWT_ALGORITHM)
    return token, jti, fam_id


def decode_token(token: str) -> dict:
    """Decode and verify any JWT (access or refresh)."""
    try:
        return jwt.decode(token, _load_public_key(), algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


# ── Auth Dependencies ────────────────────────────────────

def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> dict:
    """
    FastAPI dependency: extracts and validates the access token.
    Supports both Authorization header (default) and 'token' query parameter.
    """
    actual_token = token
    
    # Fallback: Check query params if header didn't provide a valid one
    # Note: OAuth2PasswordBearer might have already raised 401 if it's strictly required
    # and the header is missing. We use request.query_params to override.
    if not actual_token or actual_token == "":
         query_token = request.query_params.get("token")
         if query_token:
             actual_token = query_token

    if not actual_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    payload = decode_token(actual_token)
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )
    return payload


# ── Cookie Helpers ───────────────────────────────────────

def set_refresh_cookie(response: Response, token: str) -> None:
    """
    Set the refresh token as an HttpOnly cookie.

    WHY HttpOnly?
    - JavaScript can't read it → immune to XSS attacks
    - SameSite=Lax → prevents CSRF on non-GET requests
    - Secure is commented out for local dev (no HTTPS)
    """
    response.set_cookie(
        key="refresh_token",
        value=token,
        httponly=True,
        samesite="lax",
        # secure=True,  # Enable in production (HTTPS only)
        max_age=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/auth",  # Only sent to /auth/* endpoints
    )


def clear_refresh_cookie(response: Response) -> None:
    """Remove the refresh token cookie."""
    response.delete_cookie(key="refresh_token", path="/auth")
