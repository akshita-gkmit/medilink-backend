import pytest


@pytest.mark.asyncio
async def test_create_doctor(client):
    data = {
        "name": "Dr. Strange",
        "email": "doctor@test.com",
        "specialization": "Cardiology"
    }

    response = await client.post("/admin/doctor/add", json=data)
    assert response.status_code == 201
    assert response.json()["name"] == "Dr. Strange"


@pytest.mark.asyncio
async def test_get_doctors(client):
    response = await client.get("/admin/doctor/all")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_delete_doctor_invalid_id(client):
    response = await client.delete("/admin/doctor/delete/9999")
    assert response.status_code == 404
