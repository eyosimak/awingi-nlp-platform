"""
Awingi NLP Platform — Authentication Web & API Routes
"""

from typing import Optional
from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from src.platform.database import get_db
from src.platform.models import User
from src.platform.templates import templates
from src.platform.auth.security import create_access_token, get_password_hash, verify_password
from src.platform.auth.dependencies import get_current_user_optional

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    next: str = "/",
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Render login form. If already authenticated, redirect to next."""
    if current_user:
        return RedirectResponse(url=next, status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "next": next,
            "error": None,
            "user": None,
        },
    )


@router.post("/login")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    next: str = Form("/"),
    db: Session = Depends(get_db),
):
    """Validate credentials and set HTTP-only cookie."""
    user = db.query(User).filter(User.username == username.strip()).first()
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "next": next,
                "error": "Invalid username or password.",
                "user": None,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if not user.is_active:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "next": next,
                "error": "Account is inactive. Please contact an administrator.",
                "user": None,
            },
            status_code=status.HTTP_403_FORBIDDEN,
        )

    # Issue JWT token
    token = create_access_token(data={"sub": user.username, "role": user.role})
    response = RedirectResponse(url=next, status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=60 * 60 * 24,  # 24 hours
        samesite="lax",
    )
    return response


@router.get("/register", response_class=HTMLResponse)
async def register_page(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Render registration form."""
    if current_user:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={
            "error": None,
            "user": None,
        },
    )


@router.post("/register")
async def register_submit(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """Create new reviewer/contributor account."""
    clean_username = username.strip()
    clean_email = email.strip().lower()

    if len(clean_username) < 3:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"error": "Username must be at least 3 characters long.", "user": None},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    if len(password) < 6:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"error": "Password must be at least 6 characters long.", "user": None},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    existing = db.query(User).filter((User.username == clean_username) | (User.email == clean_email)).first()
    if existing:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={"error": "Username or email is already registered.", "user": None},
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # First registered user defaults to admin if none exists; otherwise reviewer
    user_count = db.query(User).count()
    assigned_role = "admin" if user_count == 0 else "reviewer"

    new_user = User(
        username=clean_username,
        email=clean_email,
        password_hash=get_password_hash(password),
        role=assigned_role,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token(data={"sub": new_user.username, "role": new_user.role})
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        max_age=60 * 60 * 24,
        samesite="lax",
    )
    return response


@router.get("/logout")
@router.post("/logout")
async def logout():
    """Clear session cookie and redirect to login."""
    response = RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="access_token")
    return response
