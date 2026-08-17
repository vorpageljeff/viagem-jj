from datetime import date
from decimal import Decimal
from app.core.security import hash_password
from app.database.session import SessionLocal
from app.models import (Accommodation, AccommodationScenario, AllocationType, BudgetItem, Expense, ExpenseCategory, Group,
    Participant, ParticipantStatus, ParticipantType, Payment, PaymentMethod, PaymentStatus, Role, ScenarioStatus, ScenarioVote,
    Trip, TripMember, TripStatus, User, Vehicle, Vote)
from app.services.finance import recalculate_allocations

NAMES = ["Jefferson Santos","Ana Santos","Bruno Lima","Carla Lima","Diego Alves","Elisa Alves","Felipe Rocha","Gabriela Rocha","Henrique Melo","Isabela Melo","João Costa","Karen Costa","Lucas Martins","Marina Martins","Nicolas Souza","Olívia Souza","Paulo Nunes","Renata Nunes","Samuel Reis","Talita Reis"]

def run_seed():
    db=SessionLocal()
    try:
        user=db.query(User).filter_by(email="admin@viagem.com").first()
        if not user:
            user=User(name="Jefferson Santos",email="admin@viagem.com",phone="(48) 99999-0000",hashed_password=hash_password("viagem2026"));db.add(user);db.flush()
        trip=db.query(Trip).filter_by(name="Garopaba Réveillon 2026/2027").first()
        if trip:return
        trip=Trip(name="Garopaba Réveillon 2026/2027",destination="Garopaba - SC",start_date=date(2026,12,26),end_date=date(2027,1,3),status=TripStatus.PLANNING,description="Oito dias para começar 2027 perto do mar.",created_by=user.id);db.add(trip);db.flush();member=TripMember(trip_id=trip.id,user_id=user.id,role=Role.ADMIN);db.add(member)
        participants=[]
        for index,name in enumerate(NAMES):
            p=Participant(trip_id=trip.id,name=name,email=f"pessoa{index+1}@example.com",participant_type=ParticipantType.CHILD if index in (7,13,18) else ParticipantType.ADULT,status=ParticipantStatus.CONFIRMED if index<18 else ParticipantStatus.MAYBE);db.add(p);participants.append(p)
        db.flush();member.participant_id=participants[0].id
        groups=[Group(trip_id=trip.id,name="Família Jefferson",description="Organizadores",participants=participants[:7]),Group(trip_id=trip.id,name="Amigos",participants=participants[7:14]),Group(trip_id=trip.id,name="Família João",participants=participants[14:])];db.add_all(groups)
        accommodations=[
            Accommodation(trip_id=trip.id,name="Casa da Ferrugem",city="Garopaba",capacity=10,bedrooms=4,bathrooms=3,beds=8,total_price=Decimal("11800"),cleaning_fee=Decimal("450"),distance_to_beach="350 m",status="VOTING"),
            Accommodation(trip_id=trip.id,name="Vila do Silveira",city="Garopaba",capacity=12,bedrooms=5,bathrooms=4,beds=10,total_price=Decimal("14200"),cleaning_fee=Decimal("600"),distance_to_beach="600 m",status="VOTING"),
            Accommodation(trip_id=trip.id,name="Refúgio da Gamboa",city="Garopaba",capacity=8,bedrooms=3,bathrooms=2,beds=7,total_price=Decimal("8900"),cleaning_fee=Decimal("350"),distance_to_beach="200 m"),
            Accommodation(trip_id=trip.id,name="Casa Centro Histórico",city="Garopaba",capacity=14,bedrooms=6,bathrooms=4,beds=12,total_price=Decimal("16900"),cleaning_fee=Decimal("650"),distance_to_beach="900 m")]
        db.add_all(accommodations);db.flush()
        scenarios=[AccommodationScenario(trip_id=trip.id,name="Duas casas perto da praia",description="Mais privacidade e acesso fácil ao mar",status=ScenarioStatus.VOTING,extra_costs=Decimal("500"),accommodations=[accommodations[0],accommodations[2]]),AccommodationScenario(trip_id=trip.id,name="Casa única",description="Todo mundo junto no centro",status=ScenarioStatus.VOTING,accommodations=[accommodations[3]]),AccommodationScenario(trip_id=trip.id,name="Vila + Gamboa",description="Maior capacidade e conforto",status=ScenarioStatus.DRAFT,accommodations=[accommodations[1],accommodations[2]])]
        db.add_all(scenarios);db.flush()
        for index,p in enumerate(participants[:16]):db.add(ScenarioVote(scenario_id=scenarios[0].id,participant_id=p.id,vote=Vote.YES if index<12 else Vote.MAYBE))
        vehicles=[Vehicle(trip_id=trip.id,name="SUV Jefferson",model="Compass",driver_participant_id=participants[0].id,capacity=5,average_consumption_km_l=Decimal("10.5"),fuel_price=Decimal("6.20"),estimated_distance_km=Decimal("520"),estimated_tolls=Decimal("85"),participants=participants[:5]),Vehicle(trip_id=trip.id,name="Carro João",model="Corolla",driver_participant_id=participants[10].id,capacity=5,average_consumption_km_l=Decimal("12"),fuel_price=Decimal("6.20"),estimated_distance_km=Decimal("600"),estimated_tolls=Decimal("90"),participants=participants[5:10]),Vehicle(trip_id=trip.id,name="Van Amigos",model="Sprinter",driver_participant_id=participants[14].id,capacity=12,average_consumption_km_l=Decimal("8"),fuel_price=Decimal("6.20"),estimated_distance_km=Decimal("550"),estimated_tolls=Decimal("120"),participants=participants[10:])];db.add_all(vehicles);db.flush()
        expenses=[
            Expense(trip_id=trip.id,description="Sinal da hospedagem",category=ExpenseCategory.ACCOMMODATION,amount=Decimal("6000"),expense_date=date(2026,8,10),paid_by_participant_id=participants[0].id,allocation_type=AllocationType.ALL),
            Expense(trip_id=trip.id,description="Primeira compra de mercado",category=ExpenseCategory.MARKET,amount=Decimal("840"),expense_date=date(2026,12,26),paid_by_participant_id=participants[2].id,allocation_type=AllocationType.SELECTED),
            Expense(trip_id=trip.id,description="Combustível SUV",category=ExpenseCategory.FUEL,amount=Decimal("390"),expense_date=date(2026,12,26),paid_by_participant_id=participants[0].id,allocation_type=AllocationType.VEHICLE,vehicle_id=vehicles[0].id),
            Expense(trip_id=trip.id,description="Churrasco de réveillon",category=ExpenseCategory.FOOD,amount=Decimal("1200"),expense_date=date(2026,12,31),paid_by_participant_id=participants[5].id,allocation_type=AllocationType.ALL),
            Expense(trip_id=trip.id,description="Passeio de barco",category=ExpenseCategory.TOUR,amount=Decimal("900"),expense_date=date(2026,12,29),paid_by_participant_id=participants[10].id,allocation_type=AllocationType.SELECTED)]
        for i,e in enumerate(expenses):db.add(e);recalculate_allocations(db,e,participants_ids(participants[:12] if i in (1,4) else []))
        payments=[Payment(trip_id=trip.id,participant_id=p.id,amount=Decimal("400") if i<8 else Decimal("250"),payment_date=date(2026,8,15),payment_method=PaymentMethod.PIX,description="Entrada",status=PaymentStatus.CONFIRMED) for i,p in enumerate(participants[:12])];db.add_all(payments)
        db.add_all([BudgetItem(trip_id=trip.id,category=ExpenseCategory.ACCOMMODATION,description="Hospedagem",estimated_amount=Decimal("18000"),actual_amount=Decimal("6000")),BudgetItem(trip_id=trip.id,category=ExpenseCategory.MARKET,description="Mercado e bebidas",estimated_amount=Decimal("4500"),actual_amount=Decimal("840")),BudgetItem(trip_id=trip.id,category=ExpenseCategory.TRANSPORT,description="Combustível e pedágios",estimated_amount=Decimal("2800"),actual_amount=Decimal("390"))])
        db.commit()
    finally:db.close()

def participants_ids(items):return [p.id for p in items]

if __name__ == "__main__":run_seed()
