from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from .database import get_session
from .models import Category, Membership, TransactionType
from .dependencies import get_current_user
import json
from fastapi import Form

router = APIRouter(prefix="/categories", tags=["categories"])

class CategoryCreate:
    def __init__(self, name: str, icon: str, color: str, type: str, subcategories: List[str]):
        self.name = name
        self.icon = icon
        self.color = color
        self.type = TransactionType(type)
        self.subcategories = subcategories

@router.get("/space/{space_id}")
def get_space_categories(
    space_id: int,
    current_user = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Получить все категории пространства"""
    # Проверка доступа
    membership = session.exec(
        select(Membership).where(
            Membership.user_id == current_user.id,
            Membership.space_id == space_id
        )
    ).first()
    
    if not membership:
        raise HTTPException(status_code=403, detail="Access denied")
    
    categories = session.exec(
        select(Category).where(Category.space_id == space_id)
    ).all()
    
    # Преобразуем JSON-строку подкатегорий в массив
    result = []
    for cat in categories:
        result.append({
            "id": cat.id,
            "name": cat.name,
            "icon": cat.icon,
            "color": cat.color,
            "type": cat.type.value,
            "subcategories": json.loads(cat.subcategories)
        })
    
    return result

from fastapi import Form  

@router.post("/space/{space_id}")
async def create_category(
    space_id: int,
    name: str = Form(...),          
    icon: str = Form("💰"),
    color: str = Form("#556B5B"),
    type: str = Form("expense"),
    subcategories: str = Form("[]"), # Принимаем как строку, парсим ниже
    current_user = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Создать новую категорию"""
    # Проверка доступа
    membership = session.exec(
        select(Membership).where(
            Membership.user_id == current_user.id,
            Membership.space_id == space_id
        )
    ).first()
    
    if not membership:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Парсим подкатегории из строки JSON
    import json
    try:
        subs_list = json.loads(subcategories) if isinstance(subcategories, str) else []
    except json.JSONDecodeError:
        subs_list = []
    
    category = Category(
        space_id=space_id,
        name=name,
        icon=icon,
        color=color,
        type=TransactionType(type),
        subcategories=json.dumps(subs_list)
    )
    
    session.add(category)
    session.commit()
    session.refresh(category)
    
    return {
        "id": category.id,
        "name": category.name,
        "icon": category.icon,
        "color": category.color,
        "type": category.type.value,
        "subcategories": subs_list
    }

@router.delete("/{category_id}")
def delete_category(
    category_id: int,
    current_user = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Удалить категорию"""
    category = session.get(Category, category_id)
    
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Проверка доступа
    membership = session.exec(
        select(Membership).where(
            Membership.user_id == current_user.id,
            Membership.space_id == category.space_id
        )
    ).first()
    
    if not membership:
        raise HTTPException(status_code=403, detail="Access denied")
    
    session.delete(category)
    session.commit()
    
    return {"message": "Category deleted"}