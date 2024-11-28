from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from database import engine, SessionLocal
import models
from passlib.context import CryptContext

app = FastAPI()

# Инициализация базы данных
models.Base.metadata.create_all(bind=engine)

# Подключение шаблонов и статических файлов
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Хэширование паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Dependency для работы с БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Главная страница
@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Меню товаров
@app.get("/menu")
def menu(request: Request):
    products = [
        {"name": "Круассан", "price": 120, "id": "croissant", "options": ["Круассан с шоколадом", "Круассан с сыром", "Круассан с джемом"]},
        {"name": "Кусочек торта", "price": 150, "id": "cake", "options": ["Прага", "Киевский", "Наполеон", "Спартак"]},
        {"name": "Булочка", "price": 50, "id": "bun", "options": ["С маком", "С корицей", "С заварным кремом"]},
    ]
    drinks = [
        {"name": "Чай черный", "id": "black_tea"},
        {"name": "Чай зеленый", "id": "green_tea"},
        {"name": "Латте", "id": "latte"},
        {"name": "Эспрессо", "id": "espresso"},
        {"name": "Раф", "id": "raf"},
        {"name": "Капучино", "id": "cappuccino"},
    ]
    return templates.TemplateResponse("menu.html", {"request": request, "products": products, "drinks": drinks})

# Обработка заказа
@app.post("/menu/submit")
async def submit_order(
    request: Request,
    croissant_name: str = Form(...),
    croissant_quantity: int = Form(...),
    croissant_drink: str = Form(...),
    cake_name: str = Form(...),
    cake_quantity: int = Form(...),
    cake_drink: str = Form(...),
    bun_name: str = Form(...),
    bun_quantity: int = Form(...),
    bun_drink: str = Form(...),
):
    # Формируем текст с результатами выбора
    result = {
        "croissant": {"name": croissant_name, "quantity": croissant_quantity, "drink": croissant_drink},
        "cake": {"name": cake_name, "quantity": cake_quantity, "drink": cake_drink},
        "bun": {"name": bun_name, "quantity": bun_quantity, "drink": bun_drink}
    }

    return templates.TemplateResponse("order_summary.html", {"request": request, "result": result})

# Страница регистрации
@app.get("/register")
def register_get(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
def register_post(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    hashed_password = pwd_context.hash(password)
    user = models.User(username=username, hashed_password=hashed_password)
    db.add(user)
    db.commit()
    return RedirectResponse("/", status_code=302)

# Страница входа
@app.get("/login")
def login_get(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login_post(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user or not pwd_context.verify(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Неправильные данные"})
    response = RedirectResponse("/", status_code=302)
    response.set_cookie(key="user_id", value=user.id)
    return response

# Профиль пользователя
@app.get("/profile")
def profile(request: Request, db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=302)
    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    return templates.TemplateResponse("profile.html", {"request": request, "user": user})

@app.post("/profile")
def update_profile(request: Request, name: str = Form(...), gender: str = Form(...), db: Session = Depends(get_db)):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return RedirectResponse("/login", status_code=302)
    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    user.name = name
    user.gender = gender
    db.commit()
    return RedirectResponse("/profile", status_code=302)