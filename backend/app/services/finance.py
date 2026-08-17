from collections.abc import Sequence
from decimal import Decimal, ROUND_DOWN
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.models import (AllocationType, Expense, ExpenseAllocation, ExpenseStatus, Participant, ParticipantStatus,
    Payment, PaymentStatus, accommodation_participants, group_participants, vehicle_participants)

CENT = Decimal("0.01")

def split_equally(total: Decimal, participant_ids: Sequence[int]) -> dict[int, Decimal]:
    ids = sorted(set(participant_ids))
    if not ids:
        raise ValueError("O rateio precisa de ao menos um participante")
    total = Decimal(total).quantize(CENT)
    base = (total / len(ids)).quantize(CENT, rounding=ROUND_DOWN)
    cents_left = int((total - base * len(ids)) / CENT)
    return {participant_id: base + (CENT if index < cents_left else Decimal("0")) for index, participant_id in enumerate(ids)}

def resolve_participants(db: Session, expense: Expense, selected_ids: list[int] | None = None) -> list[int]:
    if expense.allocation_type == AllocationType.SELECTED:
        ids = selected_ids or []
    elif expense.allocation_type == AllocationType.ALL:
        ids = [row[0] for row in db.query(Participant.id).filter(Participant.trip_id == expense.trip_id, Participant.status.in_([ParticipantStatus.CONFIRMED, ParticipantStatus.MAYBE])).all()]
    elif expense.allocation_type == AllocationType.ACCOMMODATION and expense.accommodation_id:
        ids = [row[0] for row in db.query(accommodation_participants.c.participant_id).where(accommodation_participants.c.accommodation_id == expense.accommodation_id).all()]
    elif expense.allocation_type == AllocationType.VEHICLE and expense.vehicle_id:
        ids = [row[0] for row in db.query(vehicle_participants.c.participant_id).where(vehicle_participants.c.vehicle_id == expense.vehicle_id).all()]
    elif expense.allocation_type == AllocationType.GROUP and expense.group_id:
        ids = [row[0] for row in db.query(group_participants.c.participant_id).where(group_participants.c.group_id == expense.group_id).all()]
    elif expense.allocation_type == AllocationType.INDIVIDUAL and expense.individual_participant_id:
        ids = [expense.individual_participant_id]
    else:
        raise HTTPException(422, "Informe o vínculo exigido pelo tipo de rateio")
    valid = {row[0] for row in db.query(Participant.id).filter(Participant.trip_id == expense.trip_id, Participant.id.in_(ids)).all()}
    if valid != set(ids):
        raise HTTPException(422, "Há participantes inválidos para esta viagem")
    return ids

def recalculate_allocations(db: Session, expense: Expense, selected_ids: list[int] | None = None) -> None:
    if expense.status == ExpenseStatus.CLOSED and expense.id:
        raise HTTPException(409, "Uma despesa fechada não pode ter o rateio alterado")
    ids = resolve_participants(db, expense, selected_ids)
    allocations = split_equally(expense.amount, ids)
    expense.allocations.clear()
    for participant_id, amount in allocations.items():
        expense.allocations.append(ExpenseAllocation(participant_id=participant_id, amount=amount))

def participant_balance(db: Session, participant_id: int) -> dict[str, Decimal]:
    due = db.query(func.coalesce(func.sum(ExpenseAllocation.amount), 0)).join(Expense).filter(ExpenseAllocation.participant_id == participant_id, Expense.status != ExpenseStatus.CANCELLED).scalar()
    paid = db.query(func.coalesce(func.sum(Payment.amount), 0)).filter(Payment.participant_id == participant_id, Payment.status == PaymentStatus.CONFIRMED).scalar()
    due, paid = Decimal(due), Decimal(paid)
    return {"total_due": due, "total_paid": paid, "balance": due - paid}

