import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_register_user():
    payload = {
        "name": "John Tester",
        "email": "testuser@example.com",
        "password": "Test@123",
        "gender": "male",
        "dob": "1995-05-10",
        "blood_group": "O+"
    }

    response = client.post("/auth/register", json=payload)
    
    assert response.status_code in [200, 400]  # 400 if user already exists
    data = response.json()

    print("Register Response:", data)

    if response.status_code == 200:
        assert data["email"] == payload["email"]


def test_login_user():
    payload = {
        "email": "doctor1@medilink.com",
        "password": "Password@123"
    }

    response = client.post("/auth/login", json=payload)
    
    assert response.status_code == 200

    data = response.json()
    print("Login Response:", data)

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["role"] in ["admin", "doctor", "patient"]


def test_login_invalid_credentials():
    payload = {
        "email": "wrong@example.com",
        "password": "InvalidPass"
    }

    response = client.post("/auth/login", json=payload)
    assert response.status_code == 401 or response.status_code == 400

    print("Invalid Login Response:", response.json())
