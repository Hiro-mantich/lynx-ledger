from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from .database import get_session
from .models import User, Space, Membership
from .schemas import SpaceCreate, SpaceResponse, JoinSpace
from .dependencies import get_current_user
from .utils import generate_invite_code
from sqlmodel import Session, select, func
from .models import User, Space, Membership, Transaction, TransactionType
from sqlmodel import Session, select, func, col
from .models import User, Space, Membership, Transaction, TransactionType, Category

router = APIRouter(prefix="/spaces", tags=["spaces"])

@router.get("/overview")
def get_overview(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Глобальная сводка по всем пространствам пользователя"""
    memberships = session.exec(select(Membership).where(Membership.user_id == current_user.id)).all()
    space_ids = [m.space_id for m in memberships]
    
    primary_map = {m.space_id: m.is_primary for m in memberships}

    if not space_ids:
        return {"global_balance": 0, "global_income": 0, "global_expense": 0, "spaces": []}

    spaces_data = []
    g_income, g_expense = 0.0, 0.0

    for sid in space_ids:
        space = session.get(Space, sid)
        txs = session.exec(select(Transaction).where(Transaction.space_id == sid)).all()
        inc = sum(t.amount for t in txs if t.type == TransactionType.INCOME)
        exp = sum(t.amount for t in txs if t.type == TransactionType.EXPENSE)
        g_income += inc
        g_expense += exp
        
        members_count = session.exec(
            select(func.count(Membership.id)).where(Membership.space_id == sid)
        ).one()

        spaces_data.append({
            "id": space.id,
            "name": space.name,
            "balance": inc - exp,
            "income": inc,
            "expense": exp,
            "invite_code": space.invite_code,
            "members_count": members_count,
            "is_primary": primary_map.get(sid, False) # Отмечаем, что это основное пространство
        })

    primary_stats = None
    primary_sid = primary_map.get(True)  # Ищем space_id, где is_primary == True
    
    # Если primary_map хранит {space_id: bool}, то ищем иначе:
    primary_sid = next((m.space_id for m in memberships if m.is_primary), None)

    if primary_sid:
        # Получаем транзакции для основного пространства
        txs_primary = session.exec(
            select(Transaction).where(Transaction.space_id == primary_sid).order_by(col(Transaction.created_at).desc())
        ).all()
        
        # Считаем итоги
        p_income = sum(t.amount for t in txs_primary if t.type == TransactionType.INCOME)
        p_expense = sum(t.amount for t in txs_primary if t.type == TransactionType.EXPENSE)
        
        # Собираем данные для графика (по пользователям)
        user_breakdown = {}
        tx_responses = []
        for t in txs_primary:
            user = session.get(User, t.user_id)
            uname = user.username if user else "Unknown"
            
            if uname not in user_breakdown:
                user_breakdown[uname] = {"income": 0, "expense": 0}
            if t.type == TransactionType.INCOME:
                user_breakdown[uname]["income"] += t.amount
            else:
                user_breakdown[uname]["expense"] += t.amount
                
            tx_responses.append({
                "id": t.id, "user_id": t.user_id, "username": uname,
                "amount": t.amount, "category": t.category, 
                "subcategory": t.subcategory, "type": t.type,
                "description": t.description, "created_at": t.created_at
            })

        primary_stats = {
            "space_id": primary_sid,
            "balance": p_income - p_expense,
            "total_income": p_income,
            "total_expense": p_expense,
            "user_breakdown": user_breakdown,
            "transactions": tx_responses
        }

    return {
        "global_balance": g_income - g_expense,
        "global_income": g_income,
        "global_expense": g_expense,
        "spaces": spaces_data,
        "primary_stats": primary_stats  
    }

@router.post("/create", response_model=SpaceResponse)
def create_space(
    space_data: SpaceCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    # 1. Генерация кода
    invite_code = generate_invite_code()
    while session.exec(select(Space).where(Space.invite_code == invite_code)).first():
        invite_code = generate_invite_code()
    
    # 2. Проверка на первое пространство
    existing_memberships = session.exec(
        select(Membership).where(Membership.user_id == current_user.id)
    ).all()
    is_first_space = len(existing_memberships) == 0
    
    # 3. Создание пространства и получение ID
    space = Space(name=space_data.name, invite_code=invite_code)
    session.add(space)
    session.flush()  # КРИТИЧНО: Присваивает space.id без коммита
    
    print(f"🔥 DEBUG: Создаем пространство ID={space.id}, начинаем генерацию категорий...")
    
    # 4. Генерация категорий
    default_categories = [
        Category(space_id=space.id, name="Еда", icon="🍕", color="#8C5A5A", type=TransactionType.EXPENSE, subcategories='["Продукты", "Рестораны", "Доставка"]'),
        Category(space_id=space.id, name="Дом", icon="🏠", color="#6B5B73", type=TransactionType.EXPENSE, subcategories='["Аренда", "ЖКХ", "Ремонт"]'),
        Category(space_id=space.id, name="Транспорт", icon="🚗", color="#A89F91", type=TransactionType.EXPENSE, subcategories='["Бензин", "Такси"]'),
        Category(space_id=space.id, name="Развлечения", icon="🎬", color="#46594B", type=TransactionType.EXPENSE, subcategories='[]'),
        Category(space_id=space.id, name="Зарплата", icon="💵", color="#556B5B", type=TransactionType.INCOME, subcategories='["Аванс", "Основная"]'),
        Category(space_id=space.id, name="Бизнес", icon="💼", color="#6B5B73", type=TransactionType.INCOME, subcategories='["Выручка"]'),
    ]
    
    session.add_all(default_categories)
    print(f"✅ DEBUG: В сессию добавлено {len(default_categories)} категорий.")
    
    # 5. Добавление пользователя
    membership = Membership(user_id=current_user.id, space_id=space.id, is_primary=is_first_space)
    session.add(membership)
    
    # 6. ФИНАЛЬНЫЙ КОММИТ
    session.commit()
    session.refresh(space)
    
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

@router.post("/set-primary/{space_id}")
def set_primary_space(
    space_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Делает указанное пространство основным для текущего пользователя"""
    
    # 1. Получаем ВСЕ связи (участия) текущего пользователя
    statement = select(Membership).where(Membership.user_id == current_user.id)
    memberships = session.exec(statement).all()
    
    target_membership = None
    
    # 2. Проходим циклом: у всех сбрасываем флаг, у нужного - поднимаем
    for m in memberships:
        m.is_primary = False  # Сбрасываем у всех
        if m.space_id == space_id:
            target_membership = m
            
    # 3. Проверка: а состоит ли юзер вообще в этом пространстве?
    if not target_membership:
        raise HTTPException(status_code=404, detail="Вы не состоите в этом пространстве")
        
    # 4. Делаем целевое основным
    target_membership.is_primary = True
    
    # 5. Сохраняем изменения в БД
    session.add_all(memberships)
    session.commit()
    
    return {"message": "Основное пространство обновлено"}

# Конфигурация категорий по умолчанию
DEFAULT_CATEGORIES = {
    "expense": {
        "Еда": ["Продукты", "Рестораны", "Доставка"],
        "Дом": ["Аренда", "ЖКХ", "Ремонт", "Бытовая химия"],
        "Транспорт": ["Бензин", "Общественный", "Такси"],
        "Развлечения": [],
        "Здоровье": []
    },
    "income": {
        "Зарплата": ["Аванс", "Основная", "Бонус"],
        "Бизнес": ["Выручка", "Инвестиции"],
        "Подарки": [],
        "Кэшбэк": []
    }
}

@router.get("/categories")
def get_categories():
    """Возвращает дерево категорий и подкатегорий"""
    return DEFAULT_CATEGORIES