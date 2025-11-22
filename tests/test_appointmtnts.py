import pytest


@pytest.mark.asyncio
async def test_book_appointment(client):
    data = {
        "user_id": 1,
        "doctor_id": 1,
        "slot_id": 1,
        "reason": "Fever"
    }

    response = await client.post("/appointment/book", json=data)
    assert response.status_code == 201
    assert response.json()["reason"] == "Fever"


@pytest.mark.asyncio
async def test_book_appointment_invalid_slot(client):
    data = {
        "user_id": 1,
        "doctor_id": 1,
        "slot_id": 9999,
        "reason": "Fever"
    }

    response = await client.post("/appointment/book", json=data)
    assert response.status_code == 404
