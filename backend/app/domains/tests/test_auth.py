import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings

TEST_DB_URL = settings.DATABASE_TEST_URL or "sqlite:///./test.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False} if "sqlite" in TEST_DB_URL else {})
TestingSession = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    def override_db():
        yield db
    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# --- Register ---

def test_register_success(client):
    res = client.post("/auth/register", json={"email": "user@test.com", "password": "Secure123"})
    assert res.status_code == 201
    assert res.json()["email"] == "user@test.com"


def test_register_duplicate_email(client):
    payload = {"email": "user@test.com", "password": "Secure123"}
    client.post("/auth/register", json=payload)
    res = client.post("/auth/register", json=payload)
    assert res.status_code == 409


def test_register_weak_password(client):
    res = client.post("/auth/register", json={"email": "user@test.com", "password": "weak"})
    assert res.status_code == 422


# --- Login ---

def test_login_success(client):
    client.post("/auth/register", json={"email": "user@test.com", "password": "Secure123"})
    res = client.login("/auth/login", json={"email": "user@test.com", "password": "Secure123"})
    # Use post
    res = client.post("/auth/login", json={"email": "user@test.com", "password": "Secure123"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_login_wrong_password(client):
    client.post("/auth/register", json={"email": "user@test.com", "password": "Secure123"})
    res = client.post("/auth/login", json={"email": "user@test.com", "password": "WrongPass1"})
    assert res.status_code == 401


# --- Me ---

def test_me(client):
    client.post("/auth/register", json={"email": "user@test.com", "password": "Secure123"})
    login = client.post("/auth/login", json={"email": "user@test.com", "password": "Secure123"})
    token = login.json()["access_token"]
    res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["email"] == "user@test.com"


# --- Refresh ---

def test_refresh_token(client):
    client.post("/auth/register", json={"email": "user@test.com", "password": "Secure123"})
    login = client.post("/auth/login", json={"email": "user@test.com", "password": "Secure123"})
    refresh = login.json()["refresh_token"]
    res = client.post("/auth/refresh", json={"refresh_token": refresh})
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_refresh_reuse_rejected(client):
    client.post("/auth/register", json={"email": "user@test.com", "password": "Secure123"})
    login = client.post("/auth/login", json={"email": "user@test.com", "password": "Secure123"})
    refresh = login.json()["refresh_token"]
    client.post("/auth/refresh", json={"refresh_token": refresh})
    res = client.post("/auth/refresh", json={"refresh_token": refresh})
    assert res.status_code == 401