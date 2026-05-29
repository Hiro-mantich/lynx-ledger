from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from .database import get_session
from .models import User
from .schemas import UserCreate, UserResponse, Token
from .utils import hash_password, verify_password, create_access_token
from .dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, session: Session = Depends(get_session)):
    """Регистрация нового пользователя"""
    # Проверяем, существует ли пользователь
    statement = select(User).where(User.username == user_data.username)
    existing_user = session.exec(statement).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Создаем нового пользователя
    new_user = User(
        username=user_data.username,
        password_hash=hash_password(user_data.password)
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    return new_user

@router.post("/login", response_model=Token)
def login(user_data: UserCreate, session: Session = Depends(get_session)):
    """Вход и получение JWT токена"""
    # Ищем пользователя
    statement = select(User).where(User.username == user_data.username)
    user = session.exec(statement).first()
    
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Создаем токен
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Получить информацию о текущем пользователе"""
    return current_user