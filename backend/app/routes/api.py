from collections import Counter
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.dependencies import current_user, trip_manager, trip_member
from app.core.security import create_access_token, hash_password, verify_password
from app.database.session import get_db
from app.models import (Accommodation, AccommodationScenario, BudgetItem, Expense, ExpenseAllocation, ExpenseStatus, Group,
    Participant, ParticipantStatus, Payment, PaymentStatus, Role, ScenarioVote, Trip, TripMember, User, Vote)
from app.schemas.api import (AccommodationIn, BudgetIn, ExpenseIn, GroupIn, LinkParticipant, Login, MemberIds, ParticipantIn,
    PaymentIn, Register, ScenarioIn, TripIn, VoteIn)
from app.services.capacity import ensure_capacity
from app.services.finance import participant_balance, recalculate_allocations

router = APIRouter(prefix="/api")

def get_or_404(db: Session, model, object_id: int, trip_id: int | None = None):
    obj = db.get(model, object_id)
    if not obj or (trip_id is not None and getattr(obj, "trip_id", None) != trip_id):
        raise HTTPException(404, "Registro não encontrado")
    return obj

def commit(db: Session, obj):
    db.add(obj); db.commit(); db.refresh(obj); return obj

def token_for(user: User):
    return {"access_token": create_access_token(user.id), "token_type": "bearer", "user": {"id": user.id, "name": user.name, "email": user.email}}

@router.post("/auth/register", status_code=201)
def register(data: Register, db: Session = Depends(get_db)):
    if db.query(User).filter(func.lower(User.email) == data.email.lower()).first():
        raise HTTPException(409, "E-mail já cadastrado")
    return token_for(commit(db, User(name=data.name, email=data.email.lower(), phone=data.phone, hashed_password=hash_password(data.password))))

@router.post("/auth/login")
def login(data: Login, db: Session = Depends(get_db)):
    user = db.query(User).filter(func.lower(User.email) == data.email.lower()).first()
    if not user or not verify_password(data.password, user.hashed_password): raise HTTPException(401, "E-mail ou senha inválidos")
    return token_for(user)

@router.post("/auth/token")
def oauth_login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    return login(Login(email=form.username, password=form.password), db)

@router.get("/auth/me")
def me(user: User = Depends(current_user)):
    return {"id": user.id, "name": user.name, "email": user.email, "phone": user.phone}

@router.get("/trips")
def list_trips(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return db.query(Trip).join(TripMember).filter(TripMember.user_id == user.id).all()

@router.post("/trips", status_code=201)
def create_trip(data: TripIn, user: User = Depends(current_user), db: Session = Depends(get_db)):
    trip = Trip(**data.model_dump(), created_by=user.id); db.add(trip); db.flush(); db.add(TripMember(trip_id=trip.id, user_id=user.id, role=Role.ADMIN)); db.commit(); db.refresh(trip); return trip

@router.get("/trips/{trip_id}")
def get_trip(trip_id: int, _=Depends(trip_member), db: Session = Depends(get_db)):
    return get_or_404(db, Trip, trip_id)

@router.put("/trips/{trip_id}")
def update_trip(trip_id: int, data: TripIn, _=Depends(trip_manager), db: Session = Depends(get_db)):
    trip = get_or_404(db, Trip, trip_id)
    for key, value in data.model_dump().items(): setattr(trip, key, value)
    return commit(db, trip)

@router.get("/trips/{trip_id}/participants")
def list_participants(trip_id: int, _=Depends(trip_member), db: Session = Depends(get_db)):
    result=[]
    for participant in db.query(Participant).filter_by(trip_id=trip_id).order_by(Participant.name).all():
        groups=[g.name for g in db.query(Group).join(Group.participants).filter(Participant.id == participant.id).all()]
        result.append({"id":participant.id,"trip_id":trip_id,"name":participant.name,"email":participant.email,"phone":participant.phone,"participant_type":participant.participant_type,"status":participant.status,"notes":participant.notes,"groups":groups,**participant_balance(db, participant.id)})
    return result

@router.post("/trips/{trip_id}/participants", status_code=201)
def create_participant(trip_id: int, data: ParticipantIn, _=Depends(trip_manager), db: Session = Depends(get_db)):
    return commit(db, Participant(trip_id=trip_id, **data.model_dump()))

@router.put("/trips/{trip_id}/participants/{participant_id}")
def update_participant(trip_id: int, participant_id: int, data: ParticipantIn, _=Depends(trip_manager), db: Session = Depends(get_db)):
    participant=get_or_404(db, Participant, participant_id, trip_id)
    for key,value in data.model_dump().items(): setattr(participant,key,value)
    return commit(db,participant)

@router.get("/trips/{trip_id}/participants/{participant_id}/withdrawal-preview")
def withdrawal_preview(trip_id:int, participant_id:int, _=Depends(trip_manager), db:Session=Depends(get_db)):
    p=get_or_404(db,Participant,participant_id,trip_id); balance=participant_balance(db,p.id)
    accommodations=db.query(Accommodation).join(Accommodation.participants).filter(Participant.id==p.id).all()
    groups=db.query(Group).join(Group.participants).filter(Participant.id==p.id).all()
    return {"participant":p.name,**balance,"allocated_expenses":db.query(ExpenseAllocation).filter_by(participant_id=p.id).count(),"accommodations":[a.name for a in accommodations],"groups":[g.name for g in groups],"warning":"Despesas e pagamentos serão preservados."}

@router.post("/trips/{trip_id}/participants/{participant_id}/withdraw")
def withdraw(trip_id:int, participant_id:int, _=Depends(trip_manager), db:Session=Depends(get_db)):
    p=get_or_404(db,Participant,participant_id,trip_id); p.status=ParticipantStatus.WITHDREW; return commit(db,p)

@router.get("/trips/{trip_id}/groups")
def list_groups(trip_id:int,_=Depends(trip_member),db:Session=Depends(get_db)):
    return [{"id":g.id,"name":g.name,"description":g.description,"participant_ids":[p.id for p in g.participants]} for g in db.query(Group).filter_by(trip_id=trip_id).all()]

@router.post("/trips/{trip_id}/groups",status_code=201)
def create_group(trip_id:int,data:GroupIn,_=Depends(trip_manager),db:Session=Depends(get_db)):
    return commit(db,Group(trip_id=trip_id,**data.model_dump()))

@router.put("/trips/{trip_id}/groups/{group_id}/participants")
def set_group_members(trip_id:int,group_id:int,data:MemberIds,_=Depends(trip_manager),db:Session=Depends(get_db)):
    group=get_or_404(db,Group,group_id,trip_id); members=db.query(Participant).filter(Participant.trip_id==trip_id,Participant.id.in_(data.participant_ids)).all()
    if len(members)!=len(set(data.participant_ids)): raise HTTPException(422,"Participante inválido")
    group.participants=members; commit(db,group); return {"participant_ids":[p.id for p in group.participants]}

def accommodation_json(a:Accommodation):
    return {"id":a.id,"trip_id":a.trip_id,"name":a.name,"city":a.city,"address":a.address,"capacity":a.capacity,"bedrooms":a.bedrooms,"bathrooms":a.bathrooms,"beds":a.beds,"parking_spaces":a.parking_spaces,"nightly_price":a.nightly_price,"total_price":a.total_price,"cleaning_fee":a.cleaning_fee,"deposit":a.deposit,"other_fees":a.other_fees,"distance_to_beach":a.distance_to_beach,"listing_url":a.listing_url,"notes":a.notes,"status":a.status,"occupancy":len(a.participants),"participant_ids":[p.id for p in a.participants]}

@router.get("/trips/{trip_id}/accommodations")
def list_accommodations(trip_id:int,_=Depends(trip_member),db:Session=Depends(get_db)):
    return [accommodation_json(a) for a in db.query(Accommodation).filter_by(trip_id=trip_id).all()]

@router.post("/trips/{trip_id}/accommodations",status_code=201)
def create_accommodation(trip_id:int,data:AccommodationIn,_=Depends(trip_manager),db:Session=Depends(get_db)):
    return accommodation_json(commit(db,Accommodation(trip_id=trip_id,**data.model_dump())))

@router.post("/trips/{trip_id}/accommodations/{accommodation_id}/participants")
def link_accommodation(trip_id:int,accommodation_id:int,data:LinkParticipant,_=Depends(trip_manager),db:Session=Depends(get_db)):
    a=get_or_404(db,Accommodation,accommodation_id,trip_id); p=get_or_404(db,Participant,data.participant_id,trip_id)
    if p not in a.participants: ensure_capacity(len(a.participants),a.capacity,data.allow_over_capacity,"hospedagem"); a.participants.append(p); commit(db,a)
    return accommodation_json(a)

@router.delete("/trips/{trip_id}/accommodations/{accommodation_id}/participants/{participant_id}")
def unlink_accommodation(trip_id:int,accommodation_id:int,participant_id:int,_=Depends(trip_manager),db:Session=Depends(get_db)):
    a=get_or_404(db,Accommodation,accommodation_id,trip_id); p=get_or_404(db,Participant,participant_id,trip_id)
    if p in a.participants:a.participants.remove(p);commit(db,a)
    return accommodation_json(a)

def scenario_json(db:Session,s:AccommodationScenario):
    confirmed=db.query(Participant).filter_by(trip_id=s.trip_id,status=ParticipantStatus.CONFIRMED).count(); total=sum((a.total_price+a.cleaning_fee+a.other_fees for a in s.accommodations),s.extra_costs); votes=Counter(v[0].value for v in db.query(ScenarioVote.vote).filter_by(scenario_id=s.id).all())
    return {"id":s.id,"name":s.name,"description":s.description,"status":s.status,"extra_costs":s.extra_costs,"accommodation_ids":[a.id for a in s.accommodations],"accommodations":[a.name for a in s.accommodations],"capacity":sum(a.capacity for a in s.accommodations),"bedrooms":sum(a.bedrooms for a in s.accommodations),"bathrooms":sum(a.bathrooms for a in s.accommodations),"total_cost":total,"confirmed_participants":confirmed,"cost_per_person":(total/confirmed if confirmed else Decimal(0)),"votes":{"YES":votes["YES"],"MAYBE":votes["MAYBE"],"NO":votes["NO"]}}

@router.get("/trips/{trip_id}/scenarios")
def list_scenarios(trip_id:int,_=Depends(trip_member),db:Session=Depends(get_db)):
    return [scenario_json(db,s) for s in db.query(AccommodationScenario).filter_by(trip_id=trip_id).all()]

@router.post("/trips/{trip_id}/scenarios",status_code=201)
def create_scenario(trip_id:int,data:ScenarioIn,_=Depends(trip_manager),db:Session=Depends(get_db)):
    accommodations=db.query(Accommodation).filter(Accommodation.trip_id==trip_id,Accommodation.id.in_(data.accommodation_ids)).all()
    if len(accommodations)!=len(set(data.accommodation_ids)):raise HTTPException(422,"Hospedagem inválida")
    values=data.model_dump(exclude={"accommodation_ids"});s=AccommodationScenario(trip_id=trip_id,**values,accommodations=accommodations);commit(db,s);return scenario_json(db,s)

@router.put("/trips/{trip_id}/scenarios/{scenario_id}/vote")
def vote_scenario(trip_id:int,scenario_id:int,data:VoteIn,_=Depends(trip_member),db:Session=Depends(get_db)):
    scenario=get_or_404(db,AccommodationScenario,scenario_id,trip_id);get_or_404(db,Participant,data.participant_id,trip_id);record=db.query(ScenarioVote).filter_by(scenario_id=scenario.id,participant_id=data.participant_id).first()
    if record:record.vote=data.vote
    else:record=ScenarioVote(scenario_id=scenario.id,participant_id=data.participant_id,vote=data.vote)
    commit(db,record);return scenario_json(db,scenario)

def expense_json(e:Expense):
    return {"id":e.id,"trip_id":e.trip_id,"description":e.description,"category":e.category,"amount":e.amount,"expense_date":e.expense_date,"allocation_type":e.allocation_type,"paid_by_participant_id":e.paid_by_participant_id,"vehicle_id":e.vehicle_id,"accommodation_id":e.accommodation_id,"group_id":e.group_id,"individual_participant_id":e.individual_participant_id,"notes":e.notes,"status":e.status,"allocations":[{"participant_id":a.participant_id,"amount":a.amount} for a in e.allocations]}

@router.get("/trips/{trip_id}/expenses")
def list_expenses(trip_id:int,_=Depends(trip_member),db:Session=Depends(get_db)):
    return [expense_json(e) for e in db.query(Expense).filter_by(trip_id=trip_id).order_by(Expense.expense_date.desc()).all()]

@router.post("/trips/{trip_id}/expenses",status_code=201)
def create_expense(trip_id:int,data:ExpenseIn,_=Depends(trip_manager),db:Session=Depends(get_db)):
    values=data.model_dump(exclude={"selected_participant_ids"});expense=Expense(trip_id=trip_id,**values);db.add(expense);recalculate_allocations(db,expense,data.selected_participant_ids);db.commit();db.refresh(expense);return expense_json(expense)

@router.get("/trips/{trip_id}/payments")
def list_payments(trip_id:int,_=Depends(trip_member),db:Session=Depends(get_db)):
    return db.query(Payment).filter_by(trip_id=trip_id).order_by(Payment.payment_date.desc()).all()

@router.post("/trips/{trip_id}/payments",status_code=201)
def create_payment(trip_id:int,data:PaymentIn,_=Depends(trip_manager),db:Session=Depends(get_db)):
    get_or_404(db,Participant,data.participant_id,trip_id);return commit(db,Payment(trip_id=trip_id,**data.model_dump()))

@router.get("/trips/{trip_id}/budget")
def list_budget(trip_id:int,_=Depends(trip_member),db:Session=Depends(get_db)):
    return db.query(BudgetItem).filter_by(trip_id=trip_id).all()

@router.post("/trips/{trip_id}/budget",status_code=201)
def create_budget(trip_id:int,data:BudgetIn,_=Depends(trip_manager),db:Session=Depends(get_db)):
    return commit(db,BudgetItem(trip_id=trip_id,**data.model_dump()))

@router.get("/trips/{trip_id}/dashboard")
def dashboard(trip_id:int,_=Depends(trip_member),db:Session=Depends(get_db)):
    participants=db.query(Participant).filter_by(trip_id=trip_id).all(); expenses=db.query(Expense).filter(Expense.trip_id==trip_id,Expense.status!=ExpenseStatus.CANCELLED).all(); payments=db.query(Payment).filter(Payment.trip_id==trip_id,Payment.status==PaymentStatus.CONFIRMED).all(); budget=db.query(BudgetItem).filter_by(trip_id=trip_id).all()
    total_expenses=sum((e.amount for e in expenses),Decimal(0));received=sum((p.amount for p in payments),Decimal(0));estimated=sum((b.estimated_amount for b in budget),Decimal(0));category=Counter()
    for e in expenses:category[e.category.value]+=e.amount
    return {"participants":{"total":len(participants),"confirmed":sum(p.status==ParticipantStatus.CONFIRMED for p in participants),"statuses":dict(Counter(p.status.value for p in participants))},"accommodation_status":"VOTING" if db.query(AccommodationScenario).filter_by(trip_id=trip_id,status="VOTING").count() else "PLANNING","budget":{"estimated":estimated,"actual":total_expenses},"payments":{"received":received,"pending":max(total_expenses-received,Decimal(0))},"expenses_by_category":category,"scenarios":db.query(AccommodationScenario).filter_by(trip_id=trip_id).count()}
