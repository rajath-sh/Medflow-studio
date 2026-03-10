import pytest
import os
from fastapi.testclient import TestClient

# Must set the isolated database URL BEFORE importing app.main
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

from app.main import app
from app.database import Base, engine

# Ensure we have a fresh, isolated database schema for the tests
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

client = TestClient(app)

def test_health_check_endpoint():
    # Tests that the application boots up and routes are registered
    response = client.get("/ai/ping")
    assert response.status_code == 200
    assert "status" in response.json()
    assert response.json()["status"] == "ok"

def test_protected_routes_require_auth():
    # Security Test: Accessing protected patient endpoint without a token should fail
    response = client.get("/patients/")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

def test_protected_workflow_require_auth():
    # Security Test: Accessing AI generation endpoint without a token should fail
    response = client.post("/ai/generate", json={"prompt": "test"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

def test_login_invalid_credentials():
    # Security Test: Logging in with wrong credentials
    response = client.post(
        "/auth/login",
        json={"username": "not_real_user@test.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credentials"
