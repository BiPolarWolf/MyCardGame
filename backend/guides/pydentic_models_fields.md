# Полный гайд по Pydantic: BaseModel, Field и управление полями

## Введение

Pydantic — это мощная библиотека для валидации данных и управления настройками в Python. Она используется в FastAPI и многих других проектах. Давай разберём все основные концепции!

---

## 1. BaseModel - Основа всего

### Что это такое?

`BaseModel` — это базовый класс Pydantic, от которого наследуются все модели данных. Он автоматически валидирует данные при создании объекта.

### Простой пример

```python
from pydantic import BaseModel

class User(BaseModel):
    name: str
    age: int
    email: str

# Создание объекта
user = User(name="Иван", age=25, email="ivan@example.com")
print(user.name)  # Иван
print(user.model_dump())  # {'name': 'Иван', 'age': 25, 'email': 'ivan@example.com'}
```

### Автоматическая валидация

```python
# ❌ Это вызовет ошибку!
user = User(name="Иван", age="не число", email="ivan@example.com")
# ValidationError: age должно быть int
```

---

## 2. Обязательные поля

### Что такое обязательное поле?

**Обязательное поле** — это поле, которое **ДОЛЖНО** быть передано при создании объекта.

### Способы создания обязательных полей

#### Способ 1: Просто указать тип

```python
from pydantic import BaseModel

class User(BaseModel):
    name: str      # ✅ Обязательное
    age: int       # ✅ Обязательное
    email: str     # ✅ Обязательное

# ❌ Ошибка! Не хватает полей
user = User(name="Иван")
# ValidationError: age и email обязательны
```

#### Способ 2: Использовать `Field(...)`

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    name: str = Field(...)      # ✅ Обязательное
    age: int = Field(...)       # ✅ Обязательное
    email: str = Field(...)     # ✅ Обязательное

# Результат тот же — все поля обязательны
```

#### Способ 3: С описанием через Field

```python
class User(BaseModel):
    name: str = Field(..., description="Имя пользователя", min_length=1)
    age: int = Field(..., description="Возраст", ge=0, le=150)
    email: str = Field(..., description="Email адрес")
```

---

## 3. Необязательные (опциональные) поля

### Способы создания необязательных полей

#### Способ 1: Значение по умолчанию

```python
from pydantic import BaseModel

class User(BaseModel):
    name: str                    # ✅ Обязательное
    age: int                     # ✅ Обязательное
    nickname: str = "Аноним"     # ⭐ Необязательное (есть default)
    bio: str = ""                # ⭐ Необязательное (пустая строка)

# ✅ Работает!
user = User(name="Иван", age=25)
print(user.nickname)  # "Аноним"
print(user.bio)       # ""
```

#### Способ 2: Optional с None

```python
from typing import Optional
from pydantic import BaseModel

class User(BaseModel):
    name: str                    # ✅ Обязательное
    age: int                     # ✅ Обязательное
    nickname: Optional[str] = None  # ⭐ Может быть None

# ✅ Работает!
user = User(name="Иван", age=25)
print(user.nickname)  # None

user2 = User(name="Пётр", age=30, nickname="Петруша")
print(user2.nickname)  # "Петруша"
```

#### Способ 3: Field с default

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    name: str = Field(...)
    age: int = Field(...)
    nickname: str = Field(default="Аноним")
    is_active: bool = Field(default=True)
```

#### Способ 4: Field с default_factory

```python
from pydantic import BaseModel, Field
from typing import List

class User(BaseModel):
    name: str = Field(...)
    tags: List[str] = Field(default_factory=list)  # Создаёт новый список каждый раз
    
user = User(name="Иван")
print(user.tags)  # []
```

---

## 4. Многоточие `...` (Ellipsis) - Что это?

### Что означает `...`?

`...` (троеточие) в Python называется **Ellipsis**. В Pydantic оно означает: **"это поле ОБЯЗАТЕЛЬНО, и у него НЕТ значения по умолчанию"**.

### Примеры использования

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    # Эти два объявления ИДЕНТИЧНЫ:
    name: str                    # Обязательное
    surname: str = Field(...)    # Обязательное (явно указано через ...)
    
    # А это необязательное:
    nickname: str = Field(default="Аноним")
```

### Когда использовать `...`?

```python
class Product(BaseModel):
    # Просто обязательное поле
    title: str
    
    # Обязательное с валидацией
    price: float = Field(..., gt=0, description="Цена должна быть положительной")
    
    # Обязательное с ограничениями
    name: str = Field(..., min_length=3, max_length=50)
```

**Правило:** Используй `...` когда хочешь добавить валидацию или описание к обязательному полю через `Field()`.

---

## 5. Field() - Мощный инструмент настройки

### Основные параметры Field

```python
from pydantic import BaseModel, Field
from typing import Optional

class Product(BaseModel):
    # Обязательное поле с валидацией
    name: str = Field(
        ...,                                    # Обязательное
        min_length=3,                          # Минимум 3 символа
        max_length=50,                         # Максимум 50 символов
        description="Название продукта"        # Описание для документации
    )
    
    # Числовое поле с границами
    price: float = Field(
        ...,
        gt=0,                                  # Greater than (больше 0)
        le=1000000,                            # Less or equal (меньше или равно)
        description="Цена в рублях"
    )
    
    # Поле с алиасом
    product_id: int = Field(
        ...,
        alias="id",                            # В JSON будет "id"
        description="Уникальный ID"
    )
    
    # Необязательное с default
    discount: float = Field(
        default=0.0,
        ge=0,
        le=100,
        description="Скидка в процентах"
    )
    
    # Необязательное с None
    description: Optional[str] = Field(
        default=None,
        max_length=500
    )
```

### Параметры Field для валидации

| Параметр | Описание | Пример |
|----------|----------|--------|
| `default` | Значение по умолчанию | `Field(default="test")` |
| `default_factory` | Функция для генерации default | `Field(default_factory=list)` |
| `alias` | Альтернативное имя поля | `Field(alias="userName")` |
| `title` | Заголовок для документации | `Field(title="User Name")` |
| `description` | Описание поля | `Field(description="The user's name")` |
| `gt` | Greater than (больше) | `Field(gt=0)` |
| `ge` | Greater or equal (больше или равно) | `Field(ge=18)` |
| `lt` | Less than (меньше) | `Field(lt=100)` |
| `le` | Less or equal (меньше или равно) | `Field(le=150)` |
| `min_length` | Минимальная длина | `Field(min_length=3)` |
| `max_length` | Максимальная длина | `Field(max_length=50)` |
| `pattern` | Regex паттерн | `Field(pattern=r"^\+7")` |
| `examples` | Примеры значений | `Field(examples=["user@mail.com"])` |

---

## 6. Сравнительная таблица всех способов

```python
from pydantic import BaseModel, Field
from typing import Optional

class User(BaseModel):
    # ========== ОБЯЗАТЕЛЬНЫЕ ПОЛЯ ==========
    
    # 1. Простое обязательное
    name: str
    
    # 2. Обязательное через Field(...)
    surname: str = Field(...)
    
    # 3. Обязательное с валидацией
    age: int = Field(..., ge=0, le=150)
    
    # 4. Обязательное с описанием
    email: str = Field(..., description="Email пользователя")
    
    
    # ========== НЕОБЯЗАТЕЛЬНЫЕ ПОЛЯ ==========
    
    # 5. С простым default
    nickname: str = "Аноним"
    
    # 6. С None (Optional)
    phone: Optional[str] = None
    
    # 7. Через Field с default
    is_active: bool = Field(default=True)
    
    # 8. Через Field с default_factory
    tags: list = Field(default_factory=list)
    
    # 9. Optional + Field + default
    bio: Optional[str] = Field(default=None, max_length=500)
```

---

## 7. Практические примеры

### Пример 1: Модель пользователя

```python
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

class User(BaseModel):
    # Обязательные поля
    username: str = Field(
        ...,
        min_length=3,
        max_length=20,
        pattern=r"^[a-zA-Z0-9_]+$",
        description="Имя пользователя (только буквы, цифры, _)"
    )
    
    email: EmailStr = Field(
        ...,
        description="Email адрес пользователя"
    )
    
    password: str = Field(
        ...,
        min_length=8,
        description="Пароль (минимум 8 символов)"
    )
    
    # Необязательные поля
    full_name: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Полное имя"
    )
    
    age: Optional[int] = Field(
        default=None,
        ge=0,
        le=150,
        description="Возраст пользователя"
    )
    
    is_active: bool = Field(
        default=True,
        description="Активен ли пользователь"
    )
    
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Дата создания"
    )
    
    roles: list[str] = Field(
        default_factory=list,
        description="Роли пользователя"
    )

# Использование
user = User(
    username="ivan_petrov",
    email="ivan@example.com",
    password="securepass123"
)

print(user.model_dump())
```

### Пример 2: Модель товара для e-commerce

```python
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal

class Product(BaseModel):
    # Обязательные
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Название товара"
    )
    
    price: Decimal = Field(
        ...,
        gt=0,
        decimal_places=2,
        description="Цена товара"
    )
    
    category: str = Field(
        ...,
        description="Категория товара"
    )
    
    # Необязательные
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Описание товара"
    )
    
    discount: float = Field(
        default=0.0,
        ge=0,
        le=100,
        description="Скидка в процентах"
    )
    
    in_stock: bool = Field(
        default=True,
        description="Есть ли в наличии"
    )
    
    quantity: int = Field(
        default=0,
        ge=0,
        description="Количество на складе"
    )
    
    tags: list[str] = Field(
        default_factory=list,
        description="Теги товара"
    )
    
    images: list[str] = Field(
        default_factory=list,
        description="URL изображений"
    )

# Использование
product = Product(
    name="MacBook Pro 16",
    price=Decimal("299990.00"),
    category="Ноутбуки",
    description="Мощный ноутбук для профессионалов",
    discount=10.0,
    quantity=5,
    tags=["apple", "laptop", "premium"]
)
```

### Пример 3: API запрос с вложенными моделями

```python
from pydantic import BaseModel, Field
from typing import Optional

class Address(BaseModel):
    street: str = Field(..., min_length=1)
    city: str = Field(..., min_length=1)
    country: str = Field(default="Russia")
    postal_code: Optional[str] = None

class ContactInfo(BaseModel):
    phone: str = Field(..., pattern=r"^\+?[1-9]\d{1,14}$")
    email: str = Field(...)
    telegram: Optional[str] = None

class UserRegistration(BaseModel):
    # Личные данные
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    middle_name: Optional[str] = Field(default=None, max_length=50)
    
    # Возраст
    age: int = Field(..., ge=18, le=120, description="Должен быть совершеннолетним")
    
    # Контакты (вложенная модель)
    contact: ContactInfo
    
    # Адрес (вложенная модель, необязательная)
    address: Optional[Address] = None
    
    # Согласие
    agree_terms: bool = Field(..., description="Согласие с условиями")
    
    # Дополнительно
    referral_code: Optional[str] = Field(default=None, min_length=6, max_length=10)

# Использование
registration = UserRegistration(
    first_name="Иван",
    last_name="Петров",
    age=25,
    contact=ContactInfo(
        phone="+79991234567",
        email="ivan@example.com"
    ),
    address=Address(
        street="Ленина 10",
        city="Москва",
        postal_code="123456"
    ),
    agree_terms=True
)
```

---

## 8. Особые случаи и трюки

### Использование validators

```python
from pydantic import BaseModel, Field, field_validator

class User(BaseModel):
    username: str = Field(..., min_length=3)
    password: str = Field(..., min_length=8)
    password_confirm: str = Field(..., min_length=8)
    
    @field_validator('username')
    @classmethod
    def username_alphanumeric(cls, v):
        if not v.isalnum():
            raise ValueError('Имя пользователя должно содержать только буквы и цифры')
        return v
    
    @field_validator('password_confirm')
    @classmethod
    def passwords_match(cls, v, info):
        if 'password' in info.data and v != info.data['password']:
            raise ValueError('Пароли не совпадают')
        return v
```

### Computed fields

```python
from pydantic import BaseModel, Field, computed_field

class Rectangle(BaseModel):
    width: float = Field(..., gt=0)
    height: float = Field(..., gt=0)
    
    @computed_field
    @property
    def area(self) -> float:
        return self.width * self.height

rect = Rectangle(width=5, height=10)
print(rect.area)  # 50.0
```

### Alias для разных имён в JSON

```python
from pydantic import BaseModel, Field

class User(BaseModel):
    user_id: int = Field(..., alias="id")
    user_name: str = Field(..., alias="name")
    email_address: str = Field(..., alias="email")
    
    model_config = {"populate_by_name": True}  # Позволяет использовать оба имени

# Можно создать так:
user1 = User(id=1, name="Иван", email="ivan@mail.com")

# Или так:
user2 = User(user_id=2, user_name="Пётр", email_address="petr@mail.com")
```

---

## 9. Шпаргалка: Быстрый выбор

```python
from pydantic import BaseModel, Field
from typing import Optional

class CheatSheet(BaseModel):
    # ✅ ОБЯЗАТЕЛЬНОЕ поле (простое)
    field1: str
    
    # ✅ ОБЯЗАТЕЛЬНОЕ поле с валидацией
    field2: str = Field(..., min_length=3)
    
    # ⭐ НЕОБЯЗАТЕЛЬНОЕ с default
    field3: str = "default_value"
    
    # ⭐ НЕОБЯЗАТЕЛЬНОЕ может быть None
    field4: Optional[str] = None
    
    # ⭐ НЕОБЯЗАТЕЛЬНОЕ через Field
    field5: str = Field(default="default")
    
    # ⭐ НЕОБЯЗАТЕЛЬНОЕ со списком
    field6: list[str] = Field(default_factory=list)
    
    # 🎯 ОБЯЗАТЕЛЬНОЕ число в диапазоне
    field7: int = Field(..., ge=0, le=100)
    
    # 🎯 ОБЯЗАТЕЛЬНОЕ с regex
    field8: str = Field(..., pattern=r"^\d{3}-\d{2}-\d{4}$")
```

---

## 10. Типичные ошибки и их решения

### Ошибка 1: Мутабельный default

```python
# ❌ НЕПРАВИЛЬНО!
class User(BaseModel):
    tags: list = []  # Все объекты будут иметь ОДИН И ТОТ ЖЕ список!

# ✅ ПРАВИЛЬНО!
class User(BaseModel):
    tags: list = Field(default_factory=list)  # Каждый объект получит новый список
```

### Ошибка 2: Optional без default

```python
# ❌ Это всё ещё ОБЯЗАТЕЛЬНОЕ поле!
class User(BaseModel):
    name: Optional[str]  # Нужно передать None или строку

# ✅ Теперь необязательное
class User(BaseModel):
    name: Optional[str] = None
```

### Ошибка 3: Путаница с ...

```python
# ❌ Бессмысленно
class User(BaseModel):
    name: Optional[str] = Field(...)  # Optional + ... = противоречие

# ✅ Правильные варианты:
class User(BaseModel):
    name: str = Field(...)              # Обязательное
    # ИЛИ
    name: Optional[str] = Field(default=None)  # Необязательное
```

---

## 11. Интеграция с FastAPI

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI()

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=20)
    email: str = Field(...)
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = Field(default=None, max_length=100)

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    is_active: bool = True

@app.post("/users", response_model=UserResponse)
def create_user(user: UserCreate):
    # FastAPI автоматически валидирует данные через Pydantic
    new_user = {
        "id": 1,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": True
    }
    return new_user
```

---

## Заключение

### Главные правила

1. **Обязательное поле**: Просто укажи тип `name: str` или используй `Field(...)`
2. **Необязательное поле**: Дай значение по умолчанию `name: str = "default"` или `Optional[str] = None`
3. **`...` (Ellipsis)**: Используй в `Field(...)` для обязательных полей с валидацией
4. **`Field()`**: Мощный инструмент для валидации, описания и настройки полей
5. **`default_factory`**: Используй для мутабельных default значений (list, dict)

### Когда что использовать?

| Ситуация | Решение |
|----------|---------|
| Простое обязательное поле | `name: str` |
| Обязательное с валидацией | `age: int = Field(..., ge=0)` |
| Необязательное с default | `is_active: bool = True` |
| Необязательное (может быть None) | `phone: Optional[str] = None` |
| Необязательное со списком | `tags: list = Field(default_factory=list)` |
| Обязательное с описанием | `email: str = Field(..., description="...")` |

Теперь ты эксперт по Pydantic! 🚀
