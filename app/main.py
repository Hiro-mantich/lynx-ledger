from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from .database import create_db_and_tables
# Импортируем модели, чтобы SQLModel увидел их при создании таблиц
from .models import User, Space, Membership, Transaction, Goal 
from .auth import router as auth_router
from .spaces import router as spaces_router
from .transactions import router as transactions_router
from .categories import router as categories_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(title="Finance Tracker", lifespan=lifespan)

# Инициализация шаблонов 
templates = Jinja2Templates(directory="templates")

# API Роуты 
app.include_router(auth_router)
app.include_router(spaces_router)
app.include_router(transactions_router)
app.include_router(categories_router)

# HTML Роуты 
@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/join", response_class=HTMLResponse)
async def join_page(request: Request):
    return templates.TemplateResponse("join_space.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})