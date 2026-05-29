from sqlmodel import SQLModel, create_engine, Session
from pathlib import Path

# Путь к файлу БД
DATABASE_URL = "sqlite:///./finance.db"

# Создаем engine
engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    """Создает все таблицы в БД"""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Зависимость для получения сессии БД"""
    with Session(engine) as session:
        yield session