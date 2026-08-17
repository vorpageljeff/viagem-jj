from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator
from app.models import AllocationType, AccommodationStatus, ExpenseCategory, ExpenseStatus, ParticipantStatus, ParticipantType, PaymentMethod, PaymentStatus, ScenarioStatus, TripStatus, Vote

class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

class Login(BaseModel):
    email: EmailStr; password: str
class Register(Login):
    name: str = Field(min_length=2, max_length=120); phone: str | None = None
class Token(BaseModel):
    access_token: str; token_type: str = "bearer"; user: dict

class TripIn(BaseModel):
    name: str = Field(min_length=3); destination: str; start_date: date; end_date: date; status: TripStatus = TripStatus.PLANNING; description: str | None = None
    @model_validator(mode="after")
    def dates(self):
        if self.end_date < self.start_date: raise ValueError("A data final deve ser posterior à inicial")
        return self
class TripOut(TripIn, ORMModel):
    id: int; created_by: int; created_at: datetime

class ParticipantIn(BaseModel):
    name: str = Field(min_length=2); email: EmailStr | None = None; phone: str | None = None; participant_type: ParticipantType = ParticipantType.ADULT; status: ParticipantStatus = ParticipantStatus.INVITED; notes: str | None = None
class ParticipantOut(ParticipantIn, ORMModel):
    id: int; trip_id: int; created_at: datetime

class GroupIn(BaseModel):
    name: str; description: str | None = None
class GroupOut(GroupIn, ORMModel):
    id: int; trip_id: int; participant_ids: list[int] = []

class AccommodationIn(BaseModel):
    name: str; city: str = "Garopaba"; address: str | None = None; latitude: Decimal | None = None; longitude: Decimal | None = None; capacity: int = Field(gt=0); bedrooms: int = Field(default=0, ge=0); bathrooms: int = Field(default=0, ge=0); beds: int = Field(default=0, ge=0); parking_spaces: int = Field(default=0, ge=0); nightly_price: Decimal = Field(default=0, ge=0); total_price: Decimal = Field(default=0, ge=0); cleaning_fee: Decimal = Field(default=0, ge=0); deposit: Decimal = Field(default=0, ge=0); other_fees: Decimal = Field(default=0, ge=0); distance_to_beach: str | None = None; listing_url: str | None = None; notes: str | None = None; status: AccommodationStatus = AccommodationStatus.CANDIDATE
class AccommodationOut(AccommodationIn, ORMModel):
    id: int; trip_id: int; occupancy: int = 0

class ScenarioIn(BaseModel):
    name: str; description: str | None = None; status: ScenarioStatus = ScenarioStatus.DRAFT; extra_costs: Decimal = Field(default=0, ge=0); accommodation_ids: list[int] = []
class VoteIn(BaseModel):
    participant_id: int; vote: Vote

class ExpenseIn(BaseModel):
    description: str; category: ExpenseCategory; amount: Decimal = Field(gt=0); expense_date: date; paid_by_participant_id: int | None = None; allocation_type: AllocationType; selected_participant_ids: list[int] = []; vehicle_id: int | None = None; accommodation_id: int | None = None; group_id: int | None = None; individual_participant_id: int | None = None; notes: str | None = None; receipt_url: str | None = None; status: ExpenseStatus = ExpenseStatus.OPEN
class PaymentIn(BaseModel):
    participant_id: int; amount: Decimal = Field(gt=0); payment_date: date; payment_method: PaymentMethod; description: str | None = None; receipt_url: str | None = None; status: PaymentStatus = PaymentStatus.CONFIRMED
class BudgetIn(BaseModel):
    category: ExpenseCategory; description: str; estimated_amount: Decimal = Field(ge=0); actual_amount: Decimal = Field(default=0, ge=0); notes: str | None = None

class MemberIds(BaseModel):
    participant_ids: list[int]
class LinkParticipant(BaseModel):
    participant_id: int; allow_over_capacity: bool = False

