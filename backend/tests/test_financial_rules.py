from datetime import date
from decimal import Decimal
import pytest
from fastapi import HTTPException
from app.models import (Accommodation, AllocationType, Expense, ExpenseCategory, ExpenseStatus, Participant, ParticipantStatus,
    Payment, PaymentMethod, PaymentStatus, Room, Trip, User, Vehicle)
from app.services.capacity import ensure_capacity
from app.services.finance import participant_balance, recalculate_allocations, split_equally

def trip_data(db):
    user=User(name="Admin",email="admin@test.local",hashed_password="x");db.add(user);db.flush()
    trip=Trip(name="Teste",destination="Garopaba",start_date=date(2026,12,26),end_date=date(2027,1,3),created_by=user.id);db.add(trip);db.flush()
    participants=[Participant(trip_id=trip.id,name=f"Pessoa {i}",status=ParticipantStatus.CONFIRMED) for i in range(1,7)];db.add_all(participants);db.flush();return trip,participants

def expense(trip,allocation_type,amount="600",**kwargs):
    return Expense(trip_id=trip.id,description="Teste",category=ExpenseCategory.OTHER,amount=Decimal(amount),expense_date=date.today(),allocation_type=allocation_type,status=ExpenseStatus.OPEN,**kwargs)

def test_rateio_entre_todos(db):
    trip,people=trip_data(db);e=expense(trip,AllocationType.ALL);db.add(e);recalculate_allocations(db,e)
    assert [a.amount for a in e.allocations]==[Decimal("100.00")]*6

def test_rateio_selecionado(db):
    trip,people=trip_data(db);e=expense(trip,AllocationType.SELECTED);db.add(e);recalculate_allocations(db,e,[p.id for p in people[:3]])
    assert [a.amount for a in e.allocations]==[Decimal("200.00")]*3

def test_rateio_por_carro(db):
    trip,people=trip_data(db);car=Vehicle(trip_id=trip.id,name="Carro",capacity=4,participants=people[:4]);db.add(car);db.flush();e=expense(trip,AllocationType.VEHICLE,vehicle_id=car.id);db.add(e);recalculate_allocations(db,e)
    assert len(e.allocations)==4 and sum(a.amount for a in e.allocations)==Decimal("600")

def test_rateio_por_hospedagem(db):
    trip,people=trip_data(db);house=Accommodation(trip_id=trip.id,name="Casa",city="Garopaba",capacity=5,participants=people[:5]);db.add(house);db.flush();e=expense(trip,AllocationType.ACCOMMODATION,accommodation_id=house.id);db.add(e);recalculate_allocations(db,e)
    assert len(e.allocations)==5 and e.allocations[0].amount==Decimal("120.00")

def test_participante_entrando_no_rateio():
    assert split_equally(Decimal("600"),[1,2,3,4,5,6])[6]==Decimal("100.00")

def test_participante_saindo_antes_do_fechamento():
    result=split_equally(Decimal("600"),[1,2,3,4,5]);assert set(result.values())=={Decimal("120.00")}

def test_ajuste_de_centavos_deterministico():
    result=split_equally(Decimal("10"),[3,1,2]);assert result=={1:Decimal("3.34"),2:Decimal("3.33"),3:Decimal("3.33")}

def test_total_devido(db):
    trip,people=trip_data(db);e=expense(trip,AllocationType.INDIVIDUAL,individual_participant_id=people[0].id,amount="150");db.add(e);recalculate_allocations(db,e);db.commit();assert participant_balance(db,people[0].id)["total_due"]==Decimal("150.00")

def test_total_pago_e_saldo(db):
    trip,people=trip_data(db);e=expense(trip,AllocationType.INDIVIDUAL,individual_participant_id=people[0].id,amount="150");db.add(e);recalculate_allocations(db,e);db.add(Payment(trip_id=trip.id,participant_id=people[0].id,amount=Decimal("50"),payment_date=date.today(),payment_method=PaymentMethod.PIX,status=PaymentStatus.CONFIRMED));db.commit();balance=participant_balance(db,people[0].id);assert balance["total_paid"]==Decimal("50.00") and balance["balance"]==Decimal("100.00")

@pytest.mark.parametrize("resource",["hospedagem","carro","quarto"])
def test_capacidades(resource):
    with pytest.raises(HTTPException) as error:ensure_capacity(5,5,False,resource)
    assert error.value.status_code==409

def test_capacidade_com_confirmacao_explicita():
    ensure_capacity(5,5,True,"hospedagem")

def test_despesa_fechada_nao_recalcula(db):
    trip,_=trip_data(db);e=expense(trip,AllocationType.ALL);db.add(e);db.flush();e.status=ExpenseStatus.CLOSED
    with pytest.raises(HTTPException):recalculate_allocations(db,e)
