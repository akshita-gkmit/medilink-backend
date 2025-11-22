import pytest


@pytest.mark.asyncio
async def test_create_slot(client):
    data = {
        "doctor_id": 1,
        "date": "2025-01-01",
        "start_time": "10:00",
        "end_time": "12:00"
    }

    response = await client.post("/doctor/slot/create", json=data)
    assert response.status_code == 201
    assert response.json()["doctor_id"] == 1


@pytest.mark.asyncio
async def test_create_slot_invalid_doctor(client):
    data = {
        "doctor_id": 9999,
        "date": "2025-01-01",
        "start_time": "10:00",
        "end_time": "12:00"
    }

    response = await client.post("/doctor/slot/create", json=data)
    assert response.status_code == 404
