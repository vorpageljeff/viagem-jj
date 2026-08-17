from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from sqlalchemy import Boolean, Column, Date, DateTime, Enum as SAEnum, ForeignKey, Numeric, String, Table, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base

class StrEnum(str, Enum):
    pass

class TripStatus(StrEnum):
    PLANNING="PLANNING"; CONFIRMED="CONFIRMED"; IN_PROGRESS="IN_PROGRESS"; FINISHED="FINISHED"; CANCELLED="CANCELLED"
class ParticipantType(StrEnum):
    ADULT="ADULT"; CHILD="CHILD"
class ParticipantStatus(StrEnum):
    INVITED="INVITED"; MAYBE="MAYBE"; CONFIRMED="CONFIRMED"; WITHDREW="WITHDREW"; CANCELLED="CANCELLED"
class Role(StrEnum):
    ADMIN="ADMIN"; ORGANIZER="ORGANIZER"; PARTICIPANT="PARTICIPANT"
class AccommodationStatus(StrEnum):
    CANDIDATE="CANDIDATE"; VOTING="VOTING"; APPROVED="APPROVED"; DISCARDED="DISCARDED"; BOOKED="BOOKED"; CANCELLED="CANCELLED"
class ScenarioStatus(StrEnum):
    DRAFT="DRAFT"; VOTING="VOTING"; APPROVED="APPROVED"; REJECTED="REJECTED"
class Vote(StrEnum):
    YES="YES"; MAYBE="MAYBE"; NO="NO"
class ExpenseCategory(StrEnum):
    ACCOMMODATION="ACCOMMODATION"; FUEL="FUEL"; TOLL="TOLL"; FOOD="FOOD"; DRINKS="DRINKS"; MARKET="MARKET"; TOUR="TOUR"; TRANSPORT="TRANSPORT"; OTHER="OTHER"
class AllocationType(StrEnum):
    ALL="ALL"; SELECTED="SELECTED"; ACCOMMODATION="ACCOMMODATION"; VEHICLE="VEHICLE"; INDIVIDUAL="INDIVIDUAL"; GROUP="GROUP"
class ExpenseStatus(StrEnum):
    DRAFT="DRAFT"; OPEN="OPEN"; CLOSED="CLOSED"; CANCELLED="CANCELLED"
class PaymentMethod(StrEnum):
    PIX="PIX"; CASH="CASH"; CARD="CARD"; TRANSFER="TRANSFER"; OTHER="OTHER"
class PaymentStatus(StrEnum):
    PENDING="PENDING"; CONFIRMED="CONFIRMED"; CANCELLED="CANCELLED"

group_participants = Table("group_participants", Base.metadata,
    Column("group_id", ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True),
    Column("participant_id", ForeignKey("participants.id"), primary_key=True))
accommodation_participants = Table("accommodation_participants", Base.metadata,
    Column("accommodation_id", ForeignKey("accommodations.id", ondelete="CASCADE"), primary_key=True),
    Column("participant_id", ForeignKey("participants.id"), primary_key=True))
scenario_items = Table("accommodation_scenario_items", Base.metadata,
    Column("scenario_id", ForeignKey("accommodation_scenarios.id", ondelete="CASCADE"), primary_key=True),
    Column("accommodation_id", ForeignKey("accommodations.id"), primary_key=True))
vehicle_participants = Table("vehicle_participants", Base.metadata,
    Column("vehicle_id", ForeignKey("vehicles.id", ondelete="CASCADE"), primary_key=True),
    Column("participant_id", ForeignKey("participants.id"), primary_key=True))
room_participants = Table("room_participants", Base.metadata,
    Column("room_id", ForeignKey("rooms.id", ondelete="CASCADE"), primary_key=True),
    Column("participant_id", ForeignKey("participants.id"), primary_key=True))

class User(Base):
    __tablename__="users"
    id: Mapped[int]=mapped_column(primary_key=True)
    name: Mapped[str]=mapped_column(String(120))
    email: Mapped[str]=mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str|None]=mapped_column(String(30))
    auth_id: Mapped[str|None]=mapped_column(String(255), unique=True)
    hashed_password: Mapped[str]=mapped_column(String(255))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Trip(Base):
    __tablename__="trips"
    id: Mapped[int]=mapped_column(primary_key=True)
    name: Mapped[str]=mapped_column(String(160))
    destination: Mapped[str]=mapped_column(String(160))
    start_date: Mapped[date]=mapped_column(Date)
    end_date: Mapped[date]=mapped_column(Date)
    status: Mapped[TripStatus]=mapped_column(SAEnum(TripStatus), default=TripStatus.PLANNING)
    description: Mapped[str|None]=mapped_column(Text)
    created_by: Mapped[int]=mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    members: Mapped[list["TripMember"]]=relationship(cascade="all, delete-orphan")

class TripMember(Base):
    __tablename__="trip_members"; __table_args__=(UniqueConstraint("trip_id","user_id"),)
    id: Mapped[int]=mapped_column(primary_key=True)
    trip_id: Mapped[int]=mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int]=mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[Role]=mapped_column(SAEnum(Role), default=Role.PARTICIPANT)
    participant_id: Mapped[int|None]=mapped_column(ForeignKey("participants.id"))

class Participant(Base):
    __tablename__="participants"
    id: Mapped[int]=mapped_column(primary_key=True)
    trip_id: Mapped[int]=mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), index=True)
    name: Mapped[str]=mapped_column(String(120))
    email: Mapped[str|None]=mapped_column(String(255))
    phone: Mapped[str|None]=mapped_column(String(30))
    participant_type: Mapped[ParticipantType]=mapped_column(SAEnum(ParticipantType), default=ParticipantType.ADULT)
    status: Mapped[ParticipantStatus]=mapped_column(SAEnum(ParticipantStatus), default=ParticipantStatus.INVITED)
    notes: Mapped[str|None]=mapped_column(Text)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Group(Base):
    __tablename__="groups"
    id: Mapped[int]=mapped_column(primary_key=True)
    trip_id: Mapped[int]=mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), index=True)
    name: Mapped[str]=mapped_column(String(120)); description: Mapped[str|None]=mapped_column(Text)
    participants: Mapped[list[Participant]]=relationship(secondary=group_participants)

class Accommodation(Base):
    __tablename__="accommodations"
    id: Mapped[int]=mapped_column(primary_key=True); trip_id: Mapped[int]=mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), index=True)
    name: Mapped[str]=mapped_column(String(160)); city: Mapped[str]=mapped_column(String(100)); address: Mapped[str|None]=mapped_column(String(255))
    latitude: Mapped[Decimal|None]=mapped_column(Numeric(10,7)); longitude: Mapped[Decimal|None]=mapped_column(Numeric(10,7))
    capacity: Mapped[int]=mapped_column(); bedrooms: Mapped[int]=mapped_column(default=0); bathrooms: Mapped[int]=mapped_column(default=0); beds: Mapped[int]=mapped_column(default=0); parking_spaces: Mapped[int]=mapped_column(default=0)
    nightly_price: Mapped[Decimal]=mapped_column(Numeric(12,2), default=0); total_price: Mapped[Decimal]=mapped_column(Numeric(12,2), default=0); cleaning_fee: Mapped[Decimal]=mapped_column(Numeric(12,2), default=0); deposit: Mapped[Decimal]=mapped_column(Numeric(12,2), default=0); other_fees: Mapped[Decimal]=mapped_column(Numeric(12,2), default=0)
    distance_to_beach: Mapped[str|None]=mapped_column(String(80)); listing_url: Mapped[str|None]=mapped_column(String(500)); notes: Mapped[str|None]=mapped_column(Text)
    status: Mapped[AccommodationStatus]=mapped_column(SAEnum(AccommodationStatus), default=AccommodationStatus.CANDIDATE)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), server_default=func.now()); updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    participants: Mapped[list[Participant]]=relationship(secondary=accommodation_participants)

class Room(Base):
    __tablename__="rooms"
    id: Mapped[int]=mapped_column(primary_key=True); accommodation_id: Mapped[int]=mapped_column(ForeignKey("accommodations.id", ondelete="CASCADE")); name: Mapped[str]=mapped_column(String(100)); capacity: Mapped[int]=mapped_column(); room_type: Mapped[str|None]=mapped_column(String(80)); notes: Mapped[str|None]=mapped_column(Text)
    participants: Mapped[list[Participant]]=relationship(secondary=room_participants)

class AccommodationScenario(Base):
    __tablename__="accommodation_scenarios"
    id: Mapped[int]=mapped_column(primary_key=True); trip_id: Mapped[int]=mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), index=True); name: Mapped[str]=mapped_column(String(120)); description: Mapped[str|None]=mapped_column(Text); status: Mapped[ScenarioStatus]=mapped_column(SAEnum(ScenarioStatus), default=ScenarioStatus.DRAFT); extra_costs: Mapped[Decimal]=mapped_column(Numeric(12,2), default=0); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), server_default=func.now())
    accommodations: Mapped[list[Accommodation]]=relationship(secondary=scenario_items)

class ScenarioVote(Base):
    __tablename__="scenario_votes"; __table_args__=(UniqueConstraint("scenario_id","participant_id"),)
    id: Mapped[int]=mapped_column(primary_key=True); scenario_id: Mapped[int]=mapped_column(ForeignKey("accommodation_scenarios.id", ondelete="CASCADE"), index=True); participant_id: Mapped[int]=mapped_column(ForeignKey("participants.id")); vote: Mapped[Vote]=mapped_column(SAEnum(Vote)); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), server_default=func.now())

class Vehicle(Base):
    __tablename__="vehicles"
    id: Mapped[int]=mapped_column(primary_key=True); trip_id: Mapped[int]=mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), index=True); name: Mapped[str]=mapped_column(String(100)); model: Mapped[str|None]=mapped_column(String(100)); driver_participant_id: Mapped[int|None]=mapped_column(ForeignKey("participants.id")); capacity: Mapped[int]=mapped_column(); average_consumption_km_l: Mapped[Decimal]=mapped_column(Numeric(8,2), default=0); fuel_price: Mapped[Decimal]=mapped_column(Numeric(8,2), default=0); estimated_distance_km: Mapped[Decimal]=mapped_column(Numeric(10,2), default=0); estimated_tolls: Mapped[Decimal]=mapped_column(Numeric(12,2), default=0); notes: Mapped[str|None]=mapped_column(Text); driver_in_split: Mapped[bool]=mapped_column(Boolean, default=True)
    participants: Mapped[list[Participant]]=relationship(secondary=vehicle_participants)

class Expense(Base):
    __tablename__="expenses"
    id: Mapped[int]=mapped_column(primary_key=True); trip_id: Mapped[int]=mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), index=True); description: Mapped[str]=mapped_column(String(180)); category: Mapped[ExpenseCategory]=mapped_column(SAEnum(ExpenseCategory)); amount: Mapped[Decimal]=mapped_column(Numeric(12,2)); expense_date: Mapped[date]=mapped_column(Date); paid_by_participant_id: Mapped[int|None]=mapped_column(ForeignKey("participants.id")); allocation_type: Mapped[AllocationType]=mapped_column(SAEnum(AllocationType)); vehicle_id: Mapped[int|None]=mapped_column(ForeignKey("vehicles.id")); accommodation_id: Mapped[int|None]=mapped_column(ForeignKey("accommodations.id")); group_id: Mapped[int|None]=mapped_column(ForeignKey("groups.id")); individual_participant_id: Mapped[int|None]=mapped_column(ForeignKey("participants.id")); notes: Mapped[str|None]=mapped_column(Text); receipt_url: Mapped[str|None]=mapped_column(String(500)); status: Mapped[ExpenseStatus]=mapped_column(SAEnum(ExpenseStatus), default=ExpenseStatus.OPEN); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), server_default=func.now()); updated_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    allocations: Mapped[list["ExpenseAllocation"]]=relationship(cascade="all, delete-orphan")

class ExpenseAllocation(Base):
    __tablename__="expense_allocations"; __table_args__=(UniqueConstraint("expense_id","participant_id"),)
    id: Mapped[int]=mapped_column(primary_key=True); expense_id: Mapped[int]=mapped_column(ForeignKey("expenses.id", ondelete="CASCADE"), index=True); participant_id: Mapped[int]=mapped_column(ForeignKey("participants.id")); amount: Mapped[Decimal]=mapped_column(Numeric(12,2))

class Payment(Base):
    __tablename__="payments"
    id: Mapped[int]=mapped_column(primary_key=True); trip_id: Mapped[int]=mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), index=True); participant_id: Mapped[int]=mapped_column(ForeignKey("participants.id")); amount: Mapped[Decimal]=mapped_column(Numeric(12,2)); payment_date: Mapped[date]=mapped_column(Date); payment_method: Mapped[PaymentMethod]=mapped_column(SAEnum(PaymentMethod)); description: Mapped[str|None]=mapped_column(String(180)); receipt_url: Mapped[str|None]=mapped_column(String(500)); status: Mapped[PaymentStatus]=mapped_column(SAEnum(PaymentStatus), default=PaymentStatus.PENDING); created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True), server_default=func.now())

class BudgetItem(Base):
    __tablename__="budget_items"
    id: Mapped[int]=mapped_column(primary_key=True); trip_id: Mapped[int]=mapped_column(ForeignKey("trips.id", ondelete="CASCADE"), index=True); category: Mapped[ExpenseCategory]=mapped_column(SAEnum(ExpenseCategory)); description: Mapped[str]=mapped_column(String(180)); estimated_amount: Mapped[Decimal]=mapped_column(Numeric(12,2)); actual_amount: Mapped[Decimal]=mapped_column(Numeric(12,2), default=0); notes: Mapped[str|None]=mapped_column(Text)
