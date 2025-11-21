import sys
import os
import uuid

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_register_user():
    unique_email = f"test_{uuid.uuid4().hex[:6]}@example.com"

    payload = {
        "name": "John Tester",
        "email": unique_email,
        "password": "Test@123",
        "gender": "male",
        "dob": "1995-05-10",
        "blood_group": "O+"
    }

    response = client.post("/auth/register", json=payload)
    data = response.json()

    print("\nRegister Response:", data)

    assert response.status_code in [200, 400]

    if response.status_code == 200:
        assert data["email"] == payload["email"]
        assert data["role"] in ["patient", "doctor", "admin", None]


def test_login_user():
    payload = {
        "email": "doctor1@medilink.com",
        "password": "Password@123"
    }

    response = client.post("/auth/login", json=payload)
    data = response.json()

    print("\nLogin Response:", data)

    assert response.status_code == 200
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["role"] in ["admin", "doctor", "patient"]

def test_login_invalid_credentials():
    payload = {
        "email": "wrong@example.com",
        "password": "InvalidPass"
    }

    response = client.post("/auth/login", json=payload)
    data = response.json()

    print("\nInvalid Login Response:", data)

    assert response.status_code in [400, 401]
    assert "detail" in data
    assert "invalid" in data["detail"].lower() or "not" in data["detail"].lower()
