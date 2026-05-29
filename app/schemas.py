from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from .models import TransactionType

# ===== Auth Schemas =====
class UserCreate(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str

class Token(BaseModel):
    access_token: str
    token_type: str

# ===== Space Schemas =====
class SpaceCreate(BaseModel):
    name: str

class SpaceResponse(BaseModel):
    id: int
    name: str
    invite_code: str
    created_at: datetime

class JoinSpace(BaseModel):
    invite_code: str


# ===== Transaction Schemas =====
class TransactionCreate(BaseModel):
    amount: float
    category: str
    type: TransactionType
    description: Optional[str] = None
    space_id: int

class TransactionResponse(BaseModel):
    id: int
    user_id: int
    username: str
    amount: float
    category: str
    type: TransactionType
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# ===== Stats Schemas =====
class SpaceStats(BaseModel):
    total_income: float
    total_expense: float
    balance: float
    transactions: list[TransactionResponse]
    user_breakdown: dict