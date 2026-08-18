from datetime import date

from fastapi.testclient import TestClient

from app.database.session import get_db
from app.main import app
from app.models import Participant, Trip, User


def client_for(db):
    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    return TestClient(app)


def test_invited_participant_registers_and_joins_trip(db):
    admin = User(name="Admin", email="admin@example.com", hashed_password="unused")
    db.add(admin)
    db.flush()
    trip = Trip(
        name="Viagem teste",
        destination="Recife",
        start_date=date(2027, 1, 10),
        end_date=date(2027, 1, 15),
        created_by=admin.id,
    )
    db.add(trip)
    db.flush()
    participant = Participant(trip_id=trip.id, name="Ana", email="ana@example.com")
    other = Participant(trip_id=trip.id, name="Bruno", email="bruno@example.com")
    db.add_all([participant, other])
    db.commit()

    try:
        with client_for(db) as client:
            response = client.post(
                "/api/auth/register",
                json={"name": "Ana", "email": "ana@example.com", "password": "senha-segura"},
            )
            assert response.status_code == 201
            headers = {"Authorization": f"Bearer {response.json()['access_token']}"}

            membership = client.get(f"/api/trips/{trip.id}/membership", headers=headers)
            assert membership.status_code == 200
            assert membership.json() == {
                "role": "PARTICIPANT",
                "participant_id": participant.id,
                "can_manage": False,
            }

            trips = client.get("/api/trips", headers=headers)
            people = client.get(f"/api/trips/{trip.id}/participants", headers=headers)
            assert trips.status_code == 200
            assert trips.json()[0]["name"] == "Viagem teste"
            assert people.status_code == 200
            assert people.json()[0]["has_account"] is True

            forbidden_expense = client.post(
                f"/api/trips/{trip.id}/expenses",
                headers=headers,
                json={
                    "description": "Despesa indevida",
                    "category": "OTHER",
                    "amount": 10,
                    "expense_date": "2027-01-10",
                    "allocation_type": "INDIVIDUAL",
                    "individual_participant_id": participant.id,
                },
            )
            assert forbidden_expense.status_code == 403

            impersonated_vote = client.put(
                f"/api/trips/{trip.id}/scenarios/999/vote",
                headers=headers,
                json={"participant_id": other.id, "vote": "YES"},
            )
            assert impersonated_vote.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_registration_without_invitation_creates_account(db):
    try:
        with client_for(db) as client:
            response = client.post(
                "/api/auth/register",
                json={"name": "Sem convite", "email": "novo@example.com", "password": "senha-segura"},
            )
            assert response.status_code == 201
            headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
            trips = client.get("/api/trips", headers=headers)
            assert trips.status_code == 200
            assert trips.json() == []
            assert db.query(User).filter_by(email="novo@example.com").first() is not None
    finally:
        app.dependency_overrides.clear()
