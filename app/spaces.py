from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from .database import get_session
from .models import User, Space, Membership
from .schemas import SpaceCreate, SpaceResponse, JoinSpace
from .dependencies import get_current_user
from .utils import generate_invite_code

router = APIRouter(prefix="/spaces", tags=["spaces"])

@router.post("/create", response_model=SpaceResponse)
def create_space(
    space_data: SpaceCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Создать новое пространство"""
    # Генерируем уникальный код
    invite_code = generate_invite_code()
    
    # Проверяем уникальность кода
    while session.exec(select(Space).where(Space.invite_code == invite_code)).first():
        invite_code = generate_invite_code()
    
    # Создаем пространство
    space = Space(
        name=space_data.name,
        invite_code=invite_code
    )
    session.add(space)
    session.commit()
    session.refresh(space)
    
    # Автоматически добавляем создателя в пространство
    membership = Membership(
        user_id=current_user.id,
        space_id=space.id
    )
    session.add(membership)
    session.commit()
    
    return space

@router.post("/join")
def join_space(
    join_data: JoinSpace,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Присоединиться к пространству по коду"""
    # Ищем пространство по коду
    statement = select(Space).where(Space.invite_code == join_data.invite_code.upper())
    space = session.exec(statement).first()
    
    if not space:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Space not found"
        )
    
    # Проверяем, не состоит ли уже
    statement = select(Membership).where(
        Membership.user_id == current_user.id,
        Membership.space_id == space.id
    )
    existing = session.exec(statement).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already a member of this space"
        )
    
    # Добавляем пользователя
    membership = Membership(
        user_id=current_user.id,
        space_id=space.id
    )
    session.add(membership)
    session.commit()
    
    return {"message": f"Successfully joined {space.name}"}

@router.get("/my", response_model=List[SpaceResponse])
def get_my_spaces(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Получить список пространств текущего пользователя"""
    statement = select(Space).join(Membership).where(
        Membership.user_id == current_user.id
    )
    spaces = session.exec(statement).all()
    return spaces