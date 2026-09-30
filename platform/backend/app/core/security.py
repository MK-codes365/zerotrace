"""
ZEROTrace — Security Module
JWT authentication, password hashing, and RBAC.
"""

import os
import hashlib
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional

try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.core.config import settings


# ── Password Hashing ─────────────────────────────────────

def hash_password(password: str) -> str:
    """Hash password using bcrypt (max 72 bytes) or salted SHA-256 fallback."""
    pw_bytes = password.encode("utf-8")[:72]
    if HAS_BCRYPT:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(pw_bytes, salt).decode("utf-8")
    else:
        salt = os.urandom(16).hex()
        digest = hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()
        return f"sha256${salt}${digest}"


def verify_password(plain: str, hashed: str) -> bool:
    """Verify plain password against hashed value."""
    if not hashed:
        return False
    pw_bytes = plain.encode("utf-8")[:72]
    if hashed.startswith("sha256$"):
        parts = hashed.split("$")
        if len(parts) == 3:
            _, salt, expected = parts
            computed = hashlib.sha256(f"{salt}:{plain}".encode("utf-8")).hexdigest()
            return computed == expected
    if HAS_BCRYPT:
        try:
            return bcrypt.checkpw(pw_bytes, hashed.encode("utf-8"))
        except Exception:
            return False
    return False


# ── Roles ─────────────────────────────────────────────────

class Role(str, Enum):
    ADMIN = "ADMIN"
    INVESTIGATOR = "INVESTIGATOR"
    ANALYST = "ANALYST"
    AUDITOR = "AUDITOR"


ROLE_HIERARCHY = {
    Role.ADMIN: {Role.ADMIN, Role.INVESTIGATOR, Role.ANALYST, Role.AUDITOR},
    Role.INVESTIGATOR: {Role.INVESTIGATOR, Role.ANALYST},
    Role.ANALYST: {Role.ANALYST},
    Role.AUDITOR: {Role.AUDITOR},
}


# ── JWT ───────────────────────────────────────────────────

security_scheme = HTTPBearer(auto_error=False)


def create_access_token(
    user_id: str,
    username: str,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
    )
    payload = {
        "sub": user_id,
        "username": username,
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {e}",
        )


# ── Dependencies ──────────────────────────────────────────

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> dict:
    """Extract and validate the current user from the JWT bearer token."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return decode_token(credentials.credentials)


def require_role(*allowed_roles: Role):
    """Factory: returns a dependency that enforces role-based access."""

    async def _check(user: dict = Depends(get_current_user)) -> dict:
        user_role = user.get("role", "")
        if user_role not in {r.value for r in allowed_roles}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user_role}' not permitted. Required: {[r.value for r in allowed_roles]}",
            )
        return user

    return _check
