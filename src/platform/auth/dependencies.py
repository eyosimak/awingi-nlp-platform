"""
Awingi NLP Platform — Authentication Dependencies & RBAC
"""

from typing import List, Optional
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from src.platform.database import get_db
from src.platform.models import User
from src.platform.auth.security import decode_access_token, get_password_hash


def get_token_from_request(request: Request) -> Optional[str]:
    """
    Extract JWT token from either HTTP-only cookie or Authorization: Bearer header.
    """
    # 1. Check HTTP-only cookie
    token = request.cookies.get("access_token")
    if token:
        # Strip optional "Bearer " prefix if stored in cookie
        if token.startswith("Bearer "):
            token = token[7:]
        return token

    # 2. Check Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:]

    return None


def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db),
) -> Optional[User]:
    """
    Extract and return authenticated User, or None if guest/unauthenticated.
    """
    token = get_token_from_request(request)
    if not token:
        return None

    payload = decode_access_token(token)
    if not payload:
        return None

    username: Optional[str] = payload.get("sub")
    if not username:
        return None

    user = db.query(User).filter(User.username == username, User.is_active == True).first()
    return user


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """
    FastAPI dependency requiring an authenticated user.
    Raises HTTP 401 if token is missing or invalid.
    """
    user = get_current_user_optional(request, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided or have expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_role(allowed_roles: List[str]):
    """
    Role-based authorization dependency factory.
    Admins automatically satisfy all role requirements.
    """
    def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role == "admin" or user.role in allowed_roles:
            return user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Operation requires one of the following roles: {', '.join(allowed_roles)}",
        )
    return role_checker


def bootstrap_default_admin(db: Session) -> User:
    """
    Ensure an initial administrator exists for immediate local testing and review.
    Default credentials: admin / admin123
    """
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        admin = User(
            username="admin",
            email="admin@awingi.edu.et",
            password_hash=get_password_hash("admin123"),
            role="admin",
            is_active=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
    return admin
