from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime, timezone
import enum

class TransactionType(str, enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    password_hash: str
    
    # Связи
    memberships: list["Membership"] = Relationship(back_populates="user")
    transactions: list["Transaction"] = Relationship(back_populates="user")

class Space(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    invite_code: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Связи
    memberships: list["Membership"] = Relationship(back_populates="space")
    transactions: list["Transaction"] = Relationship(back_populates="space")
    goals: list["Goal"] = Relationship(back_populates="space")

class Membership(SQLModel, table=True):
    """Связь многие-ко-многим между User и Space"""
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    space_id: int = Field(foreign_key="space.id")
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Связи
    user: User = Relationship(back_populates="memberships")
    space: Space = Relationship(back_populates="memberships")

class Transaction(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    space_id: int = Field(foreign_key="space.id")
    amount: float
    category: str  # "Еда", "Транспорт", "Зарплата" и т.д.
    type: TransactionType
    description: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Связи
    user: User = Relationship(back_populates="transactions")
    space: Space = Relationship(back_populates="transactions")

class Goal(SQLModel, table=True):
    """Общая цель (копилка)"""
    id: int | None = Field(default=None, primary_key=True)
    space_id: int = Field(foreign_key="space.id")
    name: str
    target_amount: float
    current_amount: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Связи
    space: Space = Relationship(back_populates="goals")