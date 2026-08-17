from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.security import hash_password
from app.database.base import Base
from app.database.session import get_db
from app.main import app
from app.models import Participant, ParticipantStatus, Role, Trip, TripMember, User

def test_login_and_dashboard_are_connected():
    engine=create_engine("sqlite://",connect_args={"check_same_thread":False},poolclass=StaticPool)
    Base.metadata.create_all(engine);Session=sessionmaker(bind=engine,expire_on_commit=False);db=Session()
    user=User(name="Admin",email="admin@example.com",hashed_password=hash_password("secret123"));db.add(user);db.flush()
    trip=Trip(name="Viagem teste",destination="Garopaba",start_date=date(2026,12,26),end_date=date(2027,1,3),created_by=user.id);db.add(trip);db.flush();db.add(TripMember(trip_id=trip.id,user_id=user.id,role=Role.ADMIN));db.add(Participant(trip_id=trip.id,name="Admin",status=ParticipantStatus.CONFIRMED));db.commit()
    def override_db():
        try:yield db
        finally:pass
    app.dependency_overrides[get_db]=override_db
    try:
        with TestClient(app) as client:
            login=client.post("/api/auth/login",json={"email":"admin@example.com","password":"secret123"})
            assert login.status_code==200
            headers={"Authorization":f"Bearer {login.json()['access_token']}"}
            trips=client.get("/api/trips",headers=headers)
            dashboard=client.get(f"/api/trips/{trip.id}/dashboard",headers=headers)
            assert trips.status_code==200 and trips.json()[0]["name"]=="Viagem teste"
            assert dashboard.status_code==200 and dashboard.json()["participants"]["confirmed"]==1
    finally:
        app.dependency_overrides.clear();db.close();Base.metadata.drop_all(engine)
