"""
Unit & Integration Tests for Authentication System (Login, Register, Logout, RBAC)
"""

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.orm import Session
from src.platform.app import app
from src.platform.database import SessionLocal
from src.platform.models import User
from src.platform.auth.security import verify_password


@pytest.fixture
def db():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_auth_pages_render(client: AsyncClient):
    """Ensure login and register pages render properly."""
    login_resp = await client.get("/auth/login")
    assert login_resp.status_code == 200
    assert "Sign in to Awingi NLP" in login_resp.text

    reg_resp = await client.get("/auth/register")
    assert reg_resp.status_code == 200
    assert "Create Reviewer Account" in reg_resp.text


@pytest.mark.asyncio
async def test_user_registration_and_login_flow(client: AsyncClient, db: Session):
    """Test full registration, cookie issuance, logout, and subsequent login."""
    import uuid
    suffix = uuid.uuid4().hex[:8]
    username = f"test_linguist_{suffix}"
    email = f"linguist_{suffix}@injibara.edu.et"
    password = "secure_password_123"

    # 1. Register new user
    reg_resp = await client.post(
        "/auth/register",
        data={"username": username, "email": email, "password": password},
        follow_redirects=False,
    )
    assert reg_resp.status_code == 303
    assert "access_token" in reg_resp.cookies

    # 2. Check DB record
    user = db.query(User).filter(User.username == username).first()
    assert user is not None
    assert verify_password(password, user.password_hash)

    # 3. Logout
    logout_resp = await client.get("/auth/logout", follow_redirects=False)
    assert logout_resp.status_code == 303

    # 4. Successful login
    login_resp = await client.post(
        "/auth/login",
        data={"username": username, "password": password, "next": "/"},
        follow_redirects=False,
    )
    assert login_resp.status_code == 303
    assert "access_token" in login_resp.cookies

    # 5. Failed login with invalid password
    bad_login = await client.post(
        "/auth/login",
        data={"username": username, "password": "wrong_password", "next": "/"},
        follow_redirects=False,
    )
    assert bad_login.status_code == 400
    assert "Invalid username or password" in bad_login.text


@pytest.mark.asyncio
async def test_duplicate_registration_rejected(client: AsyncClient):
    """Ensure duplicate username registration is rejected."""
    import uuid
    dup_name = f"dup_{uuid.uuid4().hex[:8]}"
    data = {
        "username": dup_name,
        "email": f"{dup_name}@injibara.edu.et",
        "password": "password123",
    }
    # First registration
    resp1 = await client.post("/auth/register", data=data, follow_redirects=False)
    assert resp1.status_code == 303

    # Second registration with same username
    resp2 = await client.post("/auth/register", data=data, follow_redirects=False)
    assert resp2.status_code == 400
    assert "already registered" in resp2.text
