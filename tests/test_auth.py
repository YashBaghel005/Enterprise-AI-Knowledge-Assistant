from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.app import app
from app.db.base import Base
from app.db.models.user import User
from app.db.sessions import SessionLocal, engine


@pytest.fixture(scope="module", autouse=True)
def ensure_tables_exist():
    Base.metadata.create_all(bind=engine)


@pytest.fixture()
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def registered_user(db_session):
    email = f"test-{uuid4().hex}@example.com"
    password = "supersecret123"

    client = TestClient(app)
    client.post(
        "/auth/register",
        json={"name": "Test User", "email": email, "password": password},
    )

    yield {"email": email, "password": password}

    db_session.query(User).filter(User.email == email).delete(
        synchronize_session=False,
    )
    db_session.commit()


def test_register_creates_user():
    client = TestClient(app)
    email = f"test-{uuid4().hex}@example.com"

    response = client.post(
        "/auth/register",
        json={"name": "New User", "email": email, "password": "supersecret123"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["email"] == email
    assert payload["is_active"] is True
    assert "password" not in payload
    assert "password_hash" not in payload

    db = SessionLocal()
    db.query(User).filter(User.email == email).delete(synchronize_session=False)
    db.commit()
    db.close()


def test_register_rejects_duplicate_email(registered_user):
    client = TestClient(app)
    response = client.post(
        "/auth/register",
        json={
            "name": "Duplicate User",
            "email": registered_user["email"],
            "password": "anotherpassword",
        },
    )

    assert response.status_code == 409


def test_login_with_correct_credentials_returns_token(registered_user):
    client = TestClient(app)
    response = client.post(
        "/auth/login",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert len(payload["access_token"]) > 0


def test_login_with_wrong_password_fails(registered_user):
    client = TestClient(app)
    response = client.post(
        "/auth/login",
        json={"email": registered_user["email"], "password": "wrongpassword"},
    )

    assert response.status_code == 401


def test_me_with_valid_token_returns_user(registered_user):
    client = TestClient(app)
    login_response = client.post(
        "/auth/login",
        json={
            "email": registered_user["email"],
            "password": registered_user["password"],
        },
    )
    token = login_response.json()["access_token"]

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == registered_user["email"]


def test_me_without_token_fails():
    client = TestClient(app)
    response = client.get("/auth/me")

    assert response.status_code == 401
