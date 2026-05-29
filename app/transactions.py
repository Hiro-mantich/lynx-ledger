from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, col
from typing import List
from .database import get_session
from .models import User, Space, Membership, Transaction, TransactionType
from .schemas import TransactionCreate, TransactionResponse, SpaceStats
from .dependencies import get_current_user

router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.post("/add", response_model=TransactionResponse)
def add_transaction(
    tx_data: TransactionCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Добавить новую транзакцию"""
    
    # 1. Проверяем, состоит ли пользователь в этом пространстве
    statement = select(Membership).where(
        Membership.user_id == current_user.id,
        Membership.space_id == tx_data.space_id
    )
    membership = session.exec(statement).first()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this space"
        )
    
    # 2. Создаем транзакцию
    new_tx = Transaction(
        user_id=current_user.id,
        space_id=tx_data.space_id,
        amount=tx_data.amount,
        category=tx_data.category,
        type=tx_data.type,
        description=tx_data.description
    )
    session.add(new_tx)
    session.commit()
    session.refresh(new_tx)
    
    # 3. Формируем ответ с именем пользователя
    return TransactionResponse(
        id=new_tx.id,
        user_id=new_tx.user_id,
        username=current_user.username,
        amount=new_tx.amount,
        category=new_tx.category,
        type=new_tx.type,
        description=new_tx.description,
        created_at=new_tx.created_at
    )

@router.get("/space/{space_id}", response_model=SpaceStats)
def get_space_stats(
    space_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Получить статистику и историю транзакций пространства"""
    
    # Проверка доступа
    statement = select(Membership).where(
        Membership.user_id == current_user.id,
        Membership.space_id == space_id
    )
    if not session.exec(statement).first():
        raise HTTPException(status_code=403, detail="Access denied")

    # 1. Получаем все транзакции
    statement = select(Transaction).where(Transaction.space_id == space_id).order_by(col(Transaction.created_at).desc())
    transactions = session.exec(statement).all()
    
    # 2. Считаем суммы
    total_income = sum(t.amount for t in transactions if t.type == TransactionType.INCOME)
    total_expense = sum(t.amount for t in transactions if t.type == TransactionType.EXPENSE)
    
    # 3. Считаем вклад каждого пользователя
    user_breakdown = {}
    for t in transactions:
        user = session.get(User, t.user_id)
        uname = user.username if user else "Unknown"
        
        if uname not in user_breakdown:
            user_breakdown[uname] = {"income": 0, "expense": 0}
        
        if t.type == TransactionType.INCOME:
            user_breakdown[uname]["income"] += t.amount
        else:
            user_breakdown[uname]["expense"] += t.amount

    # 4. Формируем список ответов
    tx_responses = []
    for t in transactions:
        user = session.get(User, t.user_id)
        tx_responses.append(TransactionResponse(
            id=t.id,
            user_id=t.user_id,
            username=user.username if user else "Unknown",
            amount=t.amount,
            category=t.category,
            type=t.type,
            description=t.description,
            created_at=t.created_at
        ))

    return SpaceStats(
        total_income=total_income,
        total_expense=total_expense,
        balance=total_income - total_expense,
        transactions=tx_responses,
        user_breakdown=user_breakdown
    )