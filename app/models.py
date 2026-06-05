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
    
    memberships: list["Membership"] = Relationship(back_populates="user")
    transactions: list["Transaction"] = Relationship(back_populates="user")

class Space(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    invite_code: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    memberships: list["Membership"] = Relationship(back_populates="space")
    transactions: list["Transaction"] = Relationship(back_populates="space")
    goals: list["Goal"] = Relationship(back_populates="space")
    categories: list["Category"] = Relationship(back_populates="space")

class Membership(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    space_id: int = Field(foreign_key="space.id")
    is_primary: bool = Field(default=False)
    joined_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    user: User = Relationship(back_populates="memberships")
    space: Space = Relationship(back_populates="memberships")

class Category(SQLModel, table=True):
    __tablename__ = "category"
    
    id: int | None = Field(default=None, primary_key=True)
    space_id: int = Field(foreign_key="space.id")
    name: str = Field(index=True)
    icon: str = Field(default="💰")
    color: str = Field(default="#556B5B")
    type: TransactionType
    subcategories: str = Field(default="[]")  # JSON-строка: '["Подкат1", "Подкат2"]'
    
    space: Space = Relationship(back_populates="categories")

class Transaction(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    space_id: int = Field(foreign_key="space.id")
    amount: float
    category: str
    subcategory: str | None = None
    type: TransactionType
    description: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    user: User = Relationship(back_populates="transactions")
    space: Space = Relationship(back_populates="transactions")

class Goal(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    space_id: int = Field(foreign_key="space.id")
    name: str
    target_amount: float
    current_amount: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    space: Space = Relationship(back_populates="goals")