import pytest


@pytest.mark.asyncio
async def test_register_success(client):
    data = {
        "name": "Akshita",
        "email": "akshita@test.com",
        "password": "Test@123",
        "role": "USER"
    }

    response = await client.post("/auth/register", json=data)
    assert response.status_code == 201
    assert response.json()["email"] == "akshita@test.com"


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    # Same email again → should fail
    data = {
        "name": "Akshita",
        "email": "akshita@test.com",
        "password": "Test@123",
        "role": "USER"
    }

    response = await client.post("/auth/register", json=data)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login_success(client):
    data = {
        "email": "akshita@test.com",
        "password": "Test@123"
    }

    response = await client.post("/auth/login", json=data)
    assert response.status_code == 200
    assert "token" in response.json()


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    data = {
        "email": "akshita@test.com",
        "password": "WrongPassword"
    }

    response = await client.post("/auth/login", json=data)
    assert response.status_code == 401
