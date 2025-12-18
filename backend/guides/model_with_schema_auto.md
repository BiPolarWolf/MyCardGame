# Автоматизация создания Pydantic схем из SQLAlchemy моделей

## Введение

У тебя есть SQLAlchemy модели через `declarative_base`, и ты не хочешь дублировать код, создавая Pydantic схемы вручную? Правильно! Есть несколько способов автоматизировать этот процесс. Разберём все от простого к сложному.

---

## 1. Проблема дублирования кода

### Типичная ситуация (без автоматизации)

```python
# models.py - SQLAlchemy модели
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    age = Column(Integer, nullable=True)

# schemas.py - Pydantic схемы (дублирование!)
from pydantic import BaseModel
from typing import Optional

class UserBase(BaseModel):
    username: str
    email: str
    is_active: bool = True
    age: Optional[int] = None

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    
    class Config:
        from_attributes = True
```

**Проблемы:**
- 😫 Дублирование полей
- 😫 Нужно вручную синхронизировать изменения
- 😫 Легко забыть обновить схему при изменении модели
- 😫 Много рутинной работы

---

## 2. Решение 1: sqlmodel (Рекомендуется!) 🌟

### Что это?

**SQLModel** — это библиотека от создателя FastAPI, которая объединяет SQLAlchemy и Pydantic. Одна модель для БД и для валидации!

### Установка

```bash
pip install sqlmodel
```

### Базовый пример

```python
from typing import Optional
from sqlmodel import Field, SQLModel

# Одна модель = SQLAlchemy + Pydantic!
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(max_length=50, unique=True)
    email: str = Field(max_length=100, unique=True)
    is_active: bool = Field(default=True)
    age: Optional[int] = None

# Используется как SQLAlchemy модель
# И как Pydantic модель одновременно!
```

### Разделение на схемы для разных операций

```python
from typing import Optional
from sqlmodel import Field, SQLModel

# Базовая модель (общие поля)
class UserBase(SQLModel):
    username: str = Field(max_length=50)
    email: str = Field(max_length=100)
    is_active: bool = Field(default=True)
    age: Optional[int] = None

# Для создания (без id)
class UserCreate(UserBase):
    password: str = Field(min_length=8)

# Для обновления (все поля опциональны)
class UserUpdate(SQLModel):
    username: Optional[str] = Field(default=None, max_length=50)
    email: Optional[str] = Field(default=None, max_length=100)
    is_active: Optional[bool] = None
    age: Optional[int] = None

# Таблица в БД (table=True)
class User(UserBase, table=True):
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    password_hash: str = Field()

# Для ответа API (с id, без пароля)
class UserResponse(UserBase):
    id: int

# Использование
user_create = UserCreate(
    username="ivan",
    email="ivan@example.com",
    password="securepass"
)

# Валидация работает автоматически!
print(user_create.model_dump())
```

### Полный пример с FastAPI

```python
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Field, Session, SQLModel, create_engine, select
from typing import Optional

# Модели
class UserBase(SQLModel):
    username: str = Field(max_length=50, unique=True)
    email: str = Field(max_length=100, unique=True)
    is_active: bool = Field(default=True)

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    password_hash: str

class UserCreate(UserBase):
    password: str = Field(min_length=8)

class UserResponse(UserBase):
    id: int

# База данных
DATABASE_URL = "sqlite:///./database.db"
engine = create_engine(DATABASE_URL)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

# FastAPI
app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, session: Session = Depends(get_session)):
    db_user = User(
        username=user.username,
        email=user.email,
        is_active=user.is_active,
        password_hash=hash_password(user.password)  # Замени на реальное хеширование
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

@app.get("/users/{user_id}", response_model=UserResponse)
def read_user(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def hash_password(password: str) -> str:
    return f"hashed_{password}"  # Замени на bcrypt или passlib
```

### Преимущества SQLModel

✅ Одна модель для БД и валидации  
✅ Автоматическая синхронизация  
✅ Встроенная поддержка FastAPI  
✅ Меньше кода  
✅ Меньше ошибок  
✅ От создателя FastAPI  

---

## 3. Решение 2: Pydantic v2 + from_attributes (Классический способ)

### Если ты не можешь использовать SQLModel

```python
# models.py - SQLAlchemy модели
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    age = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

```python
# schemas.py - Pydantic схемы
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: str
    is_active: bool = True
    age: Optional[int] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None
    age: Optional[int] = None

class UserResponse(UserBase):
    id: int
    created_at: datetime
    
    # ВАЖНО! Позволяет создавать из SQLAlchemy объектов
    model_config = ConfigDict(from_attributes=True)

# Использование
from models import User as UserModel
from schemas import UserResponse

# SQLAlchemy объект из БД
db_user = session.query(UserModel).first()

# Автоматическое преобразование в Pydantic
pydantic_user = UserResponse.model_validate(db_user)
print(pydantic_user.model_dump())
```

### Как работает from_attributes?

```python
# БЕЗ from_attributes - нужен dict
user_dict = {
    "id": 1,
    "username": "ivan",
    "email": "ivan@example.com",
    "is_active": True,
    "age": 25,
    "created_at": datetime.now()
}
pydantic_user = UserResponse(**user_dict)

# С from_attributes - можно напрямую из объекта!
db_user = session.query(User).first()
pydantic_user = UserResponse.model_validate(db_user)
# Pydantic автоматически читает атрибуты: db_user.id, db_user.username и т.д.
```

---

## 4. Решение 3: Автоматическая генерация схем (Advanced) 🔥

### Создаём функцию-генератор

```python
# schema_generator.py
from pydantic import BaseModel, ConfigDict, create_model
from typing import Optional, Type, get_type_hints
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import DeclarativeMeta

def sqlalchemy_to_pydantic(
    db_model: Type[DeclarativeMeta],
    *,
    exclude: set = None,
    optional: set = None,
    config: ConfigDict = None
) -> Type[BaseModel]:
    """
    Автоматически создаёт Pydantic модель из SQLAlchemy модели
    
    Args:
        db_model: SQLAlchemy модель
        exclude: Поля для исключения
        optional: Поля, которые сделать Optional
        config: Pydantic ConfigDict
    
    Returns:
        Pydantic модель
    """
    exclude = exclude or set()
    optional = optional or set()
    
    mapper = inspect(db_model)
    fields = {}
    
    for column in mapper.columns:
        if column.name in exclude:
            continue
        
        # Определяем тип Python
        python_type = column.type.python_type
        
        # Делаем поле Optional если нужно
        if column.nullable or column.name in optional:
            python_type = Optional[python_type]
            default = None
        elif column.default is not None:
            default = column.default.arg if callable(column.default.arg) else column.default.arg
        else:
            default = ...  # Обязательное поле
        
        fields[column.name] = (python_type, default)
    
    # Создаём Pydantic модель динамически
    pydantic_model = create_model(
        f"{db_model.__name__}Schema",
        **fields,
        __config__=config or ConfigDict(from_attributes=True)
    )
    
    return pydantic_model
```

### Использование генератора

```python
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from schema_generator import sqlalchemy_to_pydantic

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    age = Column(Integer, nullable=True)

# Автоматическая генерация схем!

# 1. Схема для создания (без id и password_hash)
UserCreate = sqlalchemy_to_pydantic(
    User,
    exclude={"id", "password_hash"}
)

# 2. Схема для ответа (без password_hash)
UserResponse = sqlalchemy_to_pydantic(
    User,
    exclude={"password_hash"}
)

# 3. Схема для обновления (все поля Optional)
UserUpdate = sqlalchemy_to_pydantic(
    User,
    exclude={"id"},
    optional={"username", "email", "is_active", "age", "password_hash"}
)

# Использование
user_data = {
    "username": "ivan",
    "email": "ivan@example.com",
    "is_active": True,
    "age": 25
}

user_create = UserCreate(**user_data)
print(user_create.model_dump())
```

---

## 5. Решение 4: Готовая библиотека - sqlalchemy-to-pydantic

### Установка

```bash
pip install sqlalchemy-to-pydantic
```

### Использование

```python
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_to_pydantic import sqlalchemy_to_pydantic

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False)
    email = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)

# Автоматическая конвертация!
UserSchema = sqlalchemy_to_pydantic(User)

# Использование
user = UserSchema(
    id=1,
    username="ivan",
    email="ivan@example.com",
    is_active=True
)
```

---

## 6. Лучшие практики и паттерны

### Паттерн 1: Базовая схема + варианты

```python
from typing import Optional
from sqlmodel import Field, SQLModel

# Базовая схема с общими полями
class UserBase(SQLModel):
    username: str = Field(max_length=50)
    email: str = Field(max_length=100)
    full_name: Optional[str] = None

# Для создания (добавляем пароль)
class UserCreate(UserBase):
    password: str = Field(min_length=8)

# Для обновления (все опционально)
class UserUpdate(SQLModel):
    username: Optional[str] = Field(default=None, max_length=50)
    email: Optional[str] = Field(default=None, max_length=100)
    full_name: Optional[str] = None
    password: Optional[str] = Field(default=None, min_length=8)

# Таблица БД
class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    password_hash: str
    is_active: bool = Field(default=True)

# Для ответа (публичные данные)
class UserResponse(UserBase):
    id: int
    is_active: bool
```

### Паттерн 2: Вложенные модели с relationships

```python
from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel

# Базовые схемы
class PostBase(SQLModel):
    title: str = Field(max_length=200)
    content: str
    published: bool = Field(default=False)

class UserBase(SQLModel):
    username: str = Field(max_length=50)
    email: str = Field(max_length=100)

# Таблицы БД
class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    password_hash: str
    posts: List["Post"] = Relationship(back_populates="author")

class Post(PostBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    author_id: int = Field(foreign_key="user.id")
    author: Optional[User] = Relationship(back_populates="posts")

# Схемы для API
class PostResponse(PostBase):
    id: int
    author_id: int

class UserResponse(UserBase):
    id: int
    posts: List[PostResponse] = []

class PostWithAuthor(PostBase):
    id: int
    author: UserResponse
```

### Паттерн 3: Фабрика схем

```python
from typing import Optional, Type, TypeVar, Generic
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.declarative import DeclarativeMeta

T = TypeVar('T')

class SchemaFactory:
    """Фабрика для создания стандартных схем"""
    
    @staticmethod
    def create_base_schema(
        model: Type[DeclarativeMeta],
        exclude: set = None
    ) -> Type[BaseModel]:
        """Создаёт базовую схему"""
        # Здесь логика генерации
        pass
    
    @staticmethod
    def create_create_schema(
        model: Type[DeclarativeMeta],
        exclude: set = None
    ) -> Type[BaseModel]:
        """Создаёт схему для создания (без id)"""
        exclude = exclude or set()
        exclude.add('id')
        # Логика генерации
        pass
    
    @staticmethod
    def create_response_schema(
        model: Type[DeclarativeMeta],
        exclude: set = None
    ) -> Type[BaseModel]:
        """Создаёт схему для ответа (с id)"""
        # Логика генерации
        pass
    
    @staticmethod
    def create_update_schema(
        model: Type[DeclarativeMeta],
        exclude: set = None
    ) -> Type[BaseModel]:
        """Создаёт схему для обновления (все Optional)"""
        exclude = exclude or set()
        exclude.add('id')
        # Все поля Optional
        pass

# Использование
from models import User

UserCreate = SchemaFactory.create_create_schema(User, exclude={'password_hash'})
UserResponse = SchemaFactory.create_response_schema(User, exclude={'password_hash'})
UserUpdate = SchemaFactory.create_update_schema(User, exclude={'password_hash'})
```

---

## 7. Сравнительная таблица решений

| Решение | Сложность | Гибкость | Поддержка | Рекомендация |
|---------|-----------|----------|-----------|--------------|
| **SQLModel** | ⭐ Очень просто | ⭐⭐⭐ Высокая | ⭐⭐⭐ Активная | 🏆 **Лучший выбор для новых проектов** |
| **from_attributes** | ⭐⭐ Просто | ⭐⭐⭐ Высокая | ⭐⭐⭐ Стандарт | ✅ Для существующих проектов |
| **Кастомный генератор** | ⭐⭐⭐ Средне | ⭐⭐⭐ Очень высокая | ⭐ Нужна поддержка | 🔧 Для специфичных кейсов |
| **sqlalchemy-to-pydantic** | ⭐⭐ Просто | ⭐⭐ Средняя | ⭐⭐ Есть | ⚠️ Проверь актуальность |

---

## 8. Полный пример проекта со SQLModel

```
project/
├── main.py           # FastAPI приложение
├── models.py         # SQLModel модели (таблицы + схемы)
├── database.py       # Настройка БД
└── requirements.txt
```

### database.py

```python
from sqlmodel import create_engine, Session

DATABASE_URL = "sqlite:///./app.db"
engine = create_engine(DATABASE_URL, echo=True)

def get_session():
    with Session(engine) as session:
        yield session
```

### models.py

```python
from typing import Optional, List
from sqlmodel import Field, Relationship, SQLModel
from datetime import datetime

# ============ USER ============

class UserBase(SQLModel):
    username: str = Field(max_length=50, unique=True, index=True)
    email: str = Field(max_length=100, unique=True, index=True)
    full_name: Optional[str] = Field(default=None, max_length=100)
    is_active: bool = Field(default=True)

class UserCreate(UserBase):
    password: str = Field(min_length=8)

class UserUpdate(SQLModel):
    username: Optional[str] = Field(default=None, max_length=50)
    email: Optional[str] = Field(default=None, max_length=100)
    full_name: Optional[str] = None
    is_active: Optional[bool] = None

class User(UserBase, table=True):
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    password_hash: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    posts: List["Post"] = Relationship(back_populates="author")

class UserResponse(UserBase):
    id: int
    created_at: datetime

class UserWithPosts(UserResponse):
    posts: List["PostResponse"] = []

# ============ POST ============

class PostBase(SQLModel):
    title: str = Field(max_length=200)
    content: str
    published: bool = Field(default=False)

class PostCreate(PostBase):
    pass

class PostUpdate(SQLModel):
    title: Optional[str] = Field(default=None, max_length=200)
    content: Optional[str] = None
    published: Optional[bool] = None

class Post(PostBase, table=True):
    __tablename__ = "posts"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    author_id: int = Field(foreign_key="users.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    author: Optional[User] = Relationship(back_populates="posts")

class PostResponse(PostBase):
    id: int
    author_id: int
    created_at: datetime

class PostWithAuthor(PostResponse):
    author: UserResponse
```

### main.py

```python
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from database import engine, get_session
from models import (
    User, UserCreate, UserResponse, UserUpdate, UserWithPosts,
    Post, PostCreate, PostResponse, PostUpdate, PostWithAuthor,
    SQLModel
)
import bcrypt

app = FastAPI(title="Blog API")

# Создание таблиц
@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

# ============ USER ENDPOINTS ============

@app.post("/users", response_model=UserResponse)
def create_user(user: UserCreate, session: Session = Depends(get_session)):
    # Проверка существования
    existing = session.exec(
        select(User).where(User.username == user.username)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Хеширование пароля
    password_hash = bcrypt.hashpw(
        user.password.encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')
    
    # Создание пользователя
    db_user = User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        password_hash=password_hash
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

@app.get("/users", response_model=List[UserResponse])
def read_users(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session)
):
    users = session.exec(select(User).offset(skip).limit(limit)).all()
    return users

@app.get("/users/{user_id}", response_model=UserWithPosts)
def read_user(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.patch("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    user_update: UserUpdate,
    session: Session = Depends(get_session)
):
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Обновление только переданных полей
    update_data = user_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)
    
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

@app.delete("/users/{user_id}")
def delete_user(user_id: int, session: Session = Depends(get_session)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    session.delete(user)
    session.commit()
    return {"message": "User deleted"}

# ============ POST ENDPOINTS ============

@app.post("/posts", response_model=PostResponse)
def create_post(
    post: PostCreate,
    author_id: int,
    session: Session = Depends(get_session)
):
    # Проверка автора
    author = session.get(User, author_id)
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    
    db_post = Post(**post.model_dump(), author_id=author_id)
    session.add(db_post)
    session.commit()
    session.refresh(db_post)
    return db_post

@app.get("/posts", response_model=List[PostWithAuthor])
def read_posts(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session)
):
    posts = session.exec(select(Post).offset(skip).limit(limit)).all()
    return posts

@app.get("/posts/{post_id}", response_model=PostWithAuthor)
def read_post(post_id: int, session: Session = Depends(get_session)):
    post = session.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post
```

---

## 9. Чеклист миграции на автоматизацию

### Если начинаешь новый проект:

- [ ] Установи SQLModel: `pip install sqlmodel`
- [ ] Создай модели через SQLModel с `table=True`
- [ ] Создай схемы для Create, Update, Response
- [ ] Наслаждайся отсутствием дублирования! 🎉

### Если у тебя существующий проект:

**Вариант А: Постепенная миграция на SQLModel**
- [ ] Установи SQLModel
- [ ] Создай новые модели через SQLModel
- [ ] Постепенно мигрируй старые модели
- [ ] Обнови эндпоинты

**Вариант Б: Добавь from_attributes**
- [ ] Обнови Pydantic до v2
- [ ] Добавь `model_config = ConfigDict(from_attributes=True)`
- [ ] Используй `.model_validate()` для конвертации
- [ ] Постепенно сокращай дублирование

**Вариант В: Используй генератор**
- [ ] Создай функцию `sqlalchemy_to_pydantic`
- [ ] Автоматизируй создание схем
- [ ] Оставь SQLAlchemy модели как есть

---

## 10. Типичные ошибки и решения

### Ошибка 1: Забыл from_attributes

```python
# ❌ НЕ РАБОТАЕТ
class UserResponse(BaseModel):
    id: int
    username: str

db_user = session.query(User).first()
response = UserResponse(**db_user)  # TypeError!

# ✅ РАБОТАЕТ
class UserResponse(BaseModel):
    id: int
    username: str
    
    model_config = ConfigDict(from_attributes=True)

db_user = session.query(User).first()
response = UserResponse.model_validate(db_user)  # OK!
```

### Ошибка 2: Circular imports с relationships

```python
# ❌ ПРОБЛЕМА: циклические импорты
# models.py
from schemas import PostResponse

class User(Base):
    posts: List[PostResponse]  # Импорт из schemas

# schemas.py
from models import User

class PostResponse(BaseModel):
    author: User  # Импорт из models

# ✅ РЕШЕНИЕ 1: Forward references
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from schemas import PostResponse

class User(Base):
    posts: List["PostResponse"]

# ✅ РЕШЕНИЕ 2: SQLModel (всё в одном файле)
class User(UserBase, table=True):
    posts: List["Post"] = Relationship(back_populates="author")
```

### Ошибка 3: Не учёл nullable поля

```python
# SQLAlchemy модель
class User(Base):
    age = Column(Integer, nullable=True)  # Может быть NULL

# ❌ НЕПРАВИЛЬНАЯ Pydantic схема
class UserResponse(BaseModel):
    age: int  # Всегда требует значение!

# ✅ ПРАВИЛЬНАЯ схема
from typing import Optional

class UserResponse(BaseModel):
    age: Optional[int] = None
```

---

## Заключение

### Рекомендации по выбору

1. **Новый проект?** → Используй **SQLModel** 🏆
2. **Существующий проект на SQLAlchemy?** → Добавь **from_attributes** ✅
3. **Нужна гибкость?** → Создай **кастомный генератор** 🔧
4. **Ленивый?** → Попробуй **sqlalchemy-to-pydantic** 😎

### Главные преимущества автоматизации

✅ Меньше кода  
✅ Нет дублирования  
✅ Автоматическая синхронизация  
✅ Меньше багов  
✅ Быстрая разработка  
✅ Легче поддержка  

Теперь ты знаешь все способы автоматизации создания Pydantic схем! 🚀
