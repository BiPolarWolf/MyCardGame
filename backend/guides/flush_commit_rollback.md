# Полный гайд по работе с сессиями SQLAlchemy

## Содержание
- [Основные команды](#основные-команды)
- [add() - Добавление объекта](#add---добавление-объекта)
- [flush() - Синхронизация с БД](#flush---синхронизация-с-бд)
- [commit() - Фиксация транзакции](#commit---фиксация-транзакции)
- [rollback() - Откат изменений](#rollback---откат-изменений)
- [merge() - Умное добавление/обновление](#merge---умное-добавлениеобновление)
- [Транзакции и их границы](#транзакции-и-их-границы)
- [Состояния объектов](#состояния-объектов)
- [Лучшие практики](#лучшие-практики)
- [Типичные ошибки](#типичные-ошибки)

---

## Основные команды

| Команда | Назначение | Закрывает транзакцию | Выполняет SQL |
|---------|-----------|---------------------|---------------|
| `add()` | Добавить объект в сессию | ❌ | ❌ |
| `flush()` | Синхронизировать с БД | ❌ | ✅ |
| `commit()` | Сохранить изменения | ✅ | ✅ |
| `rollback()` | Откатить изменения | ✅ | ✅ |
| `merge()` | Добавить или обновить | ❌ | ⚠️ |

---

## add() - Добавление объекта

### Описание
Помещает объект в **Unit of Work** (единицу работы) сессии для отслеживания.

### Что происходит
- Объект переходит в состояние **pending**
- **НЕ отправляется** никаких SQL запросов
- Объект просто помечается для последующего сохранения

### Примеры

```python
# Базовое использование
card = CardType(name="Premium", description="Premium card")
db.add(card)

# ID ещё нет - запроса в БД не было
print(card.id)  # None
```

```python
# Добавление нескольких объектов
card1 = CardType(name="Basic")
card2 = CardType(name="Premium")
card3 = CardType(name="Gold")

# Способ 1: по одному
db.add(card1)
db.add(card2)
db.add(card3)

# Способ 2: всё сразу
db.add_all([card1, card2, card3])
```

```python
# Автоматическое добавление связанных объектов
user = User(name="John")
card = CardType(name="Premium", owner=user)
db.add(card)  # user также будет добавлен автоматически
```

### Важные моменты
- После `add()` объект в состоянии **pending**
- SQL запрос **не выполняется** до `flush()` или `commit()`
- Объект не имеет ID до синхронизации с БД
- Можно добавлять объекты с несуществующими foreign keys - ошибка будет только при `flush()`

---

## flush() - Синхронизация с БД

### Описание
Отправляет накопленные изменения в базу данных, но **не закрывает транзакцию**.

### Что происходит
1. SQLAlchemy генерирует SQL запросы (INSERT, UPDATE, DELETE)
2. Запросы **выполняются** в БД
3. Транзакция **остаётся открытой**
4. Изменения видны только внутри текущей транзакции
5. Объекты получают ID и другие generated values

### Примеры

```python
# Получение ID после flush
card = CardType(name="Premium")
print(card.id)  # None

db.add(card)
print(card.id)  # Всё ещё None

db.flush()
print(card.id)  # 1 - ID получен из БД!
```

```python
# Зависимые операции с использованием flush
user = User(name="John")
db.add(user)
db.flush()  # Получаем user.id

# Теперь можем использовать user.id
card = CardType(name="Premium", user_id=user.id)
db.add(card)
db.flush()

# Но транзакция ещё открыта!
# Если будет ошибка, можно откатить ВСЁ
```

```python
# Проверка constraints до commit
try:
    card = CardType(name="Duplicate")
    db.add(card)
    db.flush()  # Проверит UNIQUE constraint
    
    # Если дошли сюда - всё OK
    db.commit()
except IntegrityError:
    db.rollback()
    print("Такая карта уже существует")
```

### Autoflush - автоматический flush

SQLAlchemy автоматически вызывает `flush()` перед:
- Любым SELECT запросом
- Вызовом `commit()`

```python
card1 = CardType(name="Card1")
db.add(card1)

# Запрос автоматически вызовет flush()
result = db.query(CardType).filter(CardType.name == "Card1").first()
print(card1.id)  # ID уже есть!
```

Отключение autoflush:
```python
# Глобально для сессии
session = Session(autoflush=False)

# Временно
with db.no_autoflush:
    # Здесь autoflush отключен
    result = db.query(CardType).all()
```

### Важные моменты
- `flush()` **НЕ закрывает** транзакцию
- Изменения видны только внутри текущей транзакции
- Другие соединения/транзакции изменений **не видят**
- После `flush()` можно сделать `rollback()`

---

## commit() - Фиксация транзакции

### Описание
Сохраняет все изменения в базе данных **навсегда** и закрывает транзакцию.

### Что происходит
1. Автоматически вызывается `flush()` (если не было)
2. Выполняется SQL **COMMIT**
3. Транзакция **закрывается**
4. Изменения становятся видны **всем** соединениям
5. Автоматически начинается **новая транзакция**

### Примеры

```python
# Базовое использование
card = CardType(name="Premium")
db.add(card)
db.commit()  # Сохранено навсегда

# Теперь в другой сессии эта запись видна
```

```python
# Атомарное сохранение нескольких объектов
try:
    user = User(name="John")
    card1 = CardType(name="Card1", owner=user)
    card2 = CardType(name="Card2", owner=user)
    
    db.add(user)
    db.add(card1)
    db.add(card2)
    
    db.commit()  # Всё сохранится атомарно (всё или ничего)
    
except Exception:
    db.rollback()
    raise
```

```python
# После commit объекты могут быть в состоянии expired
card = CardType(name="Premium")
db.add(card)
db.commit()

# Первое обращение может вызвать SELECT!
print(card.name)  # Может быть дополнительный запрос

# Явное обновление объекта
db.refresh(card)  # SELECT из БД
```

### Множественные commit - опасность!

```python
# ❌ ПЛОХО: несколько commit = несколько транзакций
def create_order(order_data, items_data):
    order = Order(**order_data)
    db.add(order)
    db.commit()  # Транзакция 1 - заказ сохранён
    
    for item_data in items_data:
        item = OrderItem(**item_data, order_id=order.id)
        db.add(item)
        db.commit()  # Транзакция 2, 3, 4...
    
    # Если ошибка на 3-м товаре:
    # заказ и первые 2 товара УЖЕ В БД
    # = несогласованное состояние!
```

```python
# ✅ ХОРОШО: один commit для связанных операций
def create_order(order_data, items_data):
    try:
        order = Order(**order_data)
        db.add(order)
        db.flush()  # Получаем order.id
        
        for item_data in items_data:
            item = OrderItem(**item_data, order_id=order.id)
            db.add(item)
        
        db.commit()  # Одна атомарная транзакция
        
    except Exception:
        db.rollback()
        raise
```

### Важные моменты
- После `commit()` откат **невозможен**
- `commit()` закрывает текущую транзакцию
- Автоматически начинается новая транзакция
- Используйте один `commit()` для логически связанных операций

---

## rollback() - Откат изменений

### Описание
Отменяет все изменения с момента последнего `commit()` и закрывает транзакцию.

### Что происходит
1. Выполняется SQL **ROLLBACK**
2. Все изменения с последнего `commit()` **отменяются**
3. Транзакция **закрывается**
4. Сессия очищается от pending объектов
5. Persistent объекты становятся **expired**
6. Автоматически начинается новая транзакция

### Примеры

```python
# Базовое использование
card = CardType(name="Test")
db.add(card)
db.flush()  # Запись в БД (в транзакции)

db.rollback()  # Отменяет изменение
# Записи в БД нет
```

```python
# Откат после ошибки
try:
    card1 = CardType(name="Card1")
    db.add(card1)
    db.flush()  # INSERT выполнен
    
    card2 = CardType(name="Card1")  # Нарушение UNIQUE
    db.add(card2)
    db.flush()  # IntegrityError!
    
except IntegrityError:
    db.rollback()  # Card1 тоже откатится!
    # БД вернётся к состоянию до начала транзакции
```

```python
# Критически важно: всегда rollback при ошибке
try:
    user = User(name="John")
    db.add(user)
    
    # Какая-то бизнес-логика
    if not validate_user(user):
        raise ValueError("Invalid user")
    
    db.commit()
    
except Exception as e:
    db.rollback()  # ОБЯЗАТЕЛЬНО!
    # Без rollback сессия будет в "битом" состоянии
    raise
```

### rollback НЕ откатывает commit

```python
# Транзакция 1
card1 = CardType(name="Card1")
db.add(card1)
db.commit()  # ✅ Card1 сохранён навсегда

# Транзакция 2
card2 = CardType(name="Card2")
db.add(card2)
db.rollback()  # ❌ Откатит только Card2

# Результат: Card1 в БД, Card2 нет
```

### Состояние объектов после rollback

```python
card = CardType(name="Test")
db.add(card)
print(card in db)  # True

db.rollback()
print(card in db)  # False - объект выброшен из сессии
print(card.id)     # None - состояние сброшено
```

### Важные моменты
- `rollback()` **обязателен** при обработке ошибок
- Откатывает только текущую транзакцию (с последнего `commit()`)
- После `rollback()` сессия снова в валидном состоянии
- Без `rollback()` сессия остаётся "битой" и непригодной для работы

---

## merge() - Умное добавление/обновление

### Описание
Интеллектуальная операция, которая может создать новый объект или обновить существующий.

### Что происходит
1. Проверяет, есть ли объект с таким primary key в сессии
2. Если есть - **обновляет** его атрибуты
3. Если нет - делает **SELECT** из БД
4. Если найден в БД - **загружает и обновляет**
5. Если нигде не найден - создаёт **новый pending объект**

### Примеры

#### Сценарий 1: Объект уже в сессии
```python
# Загружаем объект
card = db.query(CardType).get(1)
print(card.name)  # "Old Name"

# Создаём копию с новыми данными
card_data = CardType(id=1, name="New Name", description="Updated")

# merge находит объект в сессии и обновляет его
merged = db.merge(card_data)

# merged и card - ЭТО ОДИН И ТОТ ЖЕ объект!
print(card is merged)    # True
print(card.name)         # "New Name"
print(merged.name)       # "New Name"

db.commit()
```

#### Сценарий 2: Объект в БД, но не в сессии
```python
# Объект есть в БД, но не загружен в сессию
card_data = CardType(id=1, name="Updated Name")

# merge сделает SELECT, загрузит объект, обновит атрибуты
merged = db.merge(card_data)

print(merged.id)    # 1
print(merged.name)  # "Updated Name"

db.commit()  # UPDATE в БД
```

#### Сценарий 3: Объекта нет нигде (новый)
```python
# Объекта с id=999 нет ни в сессии, ни в БД
card_new = CardType(id=999, name="Brand New")

# merge создаст новый pending объект
merged = db.merge(card_new)

db.commit()  # INSERT в БД
```

#### Сценарий 4: Upsert без указания ID
```python
# Если не указан primary key - всегда INSERT
card = CardType(name="New Card")  # id не указан
merged = db.merge(card)
db.commit()  # INSERT

# Для настоящего upsert нужен ID
card_with_id = CardType(id=1, name="Update or Insert")
merged = db.merge(card_with_id)
db.commit()  # UPDATE если есть, INSERT если нет
```

### merge vs add

```python
# add() - ошибка если объект с таким ID уже в сессии
card = db.query(CardType).get(1)
db.add(card)  # InvalidRequestError: Object already in session!

# merge() - безопасно в любом случае
merged = db.merge(CardType(id=1, name="Updated"))  # OK
```

### Практический пример: безопасный upsert
```python
def upsert_card(card_data: dict) -> CardType:
    """Создать или обновить карту"""
    card = CardType(**card_data)
    merged = db.merge(card)
    db.commit()
    db.refresh(merged)
    return merged

# Использование
card1 = upsert_card({"id": 1, "name": "Card 1"})  # INSERT если нет
card2 = upsert_card({"id": 1, "name": "Updated"}) # UPDATE если есть
```

### Работа со связями
```python
# merge также обрабатывает связанные объекты
user = User(id=1, name="John")
card = CardType(id=1, name="Premium", owner=user)

# merge обработает и user, и card
merged_card = db.merge(card)
db.commit()
```

### Важные моменты
- `merge()` возвращает объект из сессии (не тот, что передали)
- Всегда работайте с возвращённым объектом
- `merge()` может выполнить SELECT для проверки существования
- Безопасен для повторного использования
- Идеален для API endpoints, где могут прийти обновления

---

## Транзакции и их границы

### Что такое транзакция

Транзакция - это логическая единица работы, которая выполняется атомарно (всё или ничего).

```
┌─────────────────────────────────────┐
│      ТРАНЗАКЦИЯ 1                   │
├─────────────────────────────────────┤
│ db.add(obj1)                        │
│ db.flush()      ← SQL выполнен      │
│ db.add(obj2)                        │
│ db.commit()     ← ГРАНИЦА           │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│      ТРАНЗАКЦИЯ 2 (автоматически)   │
├─────────────────────────────────────┤
│ db.add(obj3)                        │
│ db.rollback()   ← ГРАНИЦА           │
└─────────────────────────────────────┘
```

### Команды внутри и вне транзакции

```python
# ============ ТРАНЗАКЦИЯ 1 ============
db.add(card1)        # внутри транзакции
db.flush()           # внутри транзакции
db.add(card2)        # внутри транзакции
db.commit()          # ← ЗАКРЫВАЕТ транзакцию
# ======================================

# ============ ТРАНЗАКЦИЯ 2 ============
# (автоматически началась после commit)
db.add(card3)        # внутри новой транзакции
db.add(card4)        # внутри транзакции
db.rollback()        # ← ЗАКРЫВАЕТ транзакцию
# ======================================

# Результат:
# card1, card2 - в БД (commit)
# card3, card4 - НЕ в БД (rollback)
```

### Граница отката - только текущая транзакция

```python
try:
    # === ТРАНЗАКЦИЯ 1 ===
    user = User(name="John")
    db.add(user)
    db.commit()  # ✅ User сохранён навсегда
    # === Граница ===
    
    # === ТРАНЗАКЦИЯ 2 ===
    card = CardType(name="Premium", user_id=user.id)
    db.add(card)
    db.flush()
    
    raise Exception("Error!")
    
except Exception:
    db.rollback()  # Откатит только ТРАНЗАКЦИЮ 2
    # User остаётся в БД!
```

### Правильная атомарность

```python
# ✅ ВСЁ в одной транзакции
try:
    user = User(name="John")
    db.add(user)
    db.flush()  # Получаем user.id, НО не commit!
    
    card = CardType(name="Premium", user_id=user.id)
    db.add(card)
    
    db.commit()  # Одна граница транзакции
    
except Exception:
    db.rollback()  # Откатит И user, И card
    raise
```

### Вложенные транзакции (savepoints)

```python
# Основная транзакция
user = User(name="John")
db.add(user)

# Вложенная транзакция (savepoint)
savepoint = db.begin_nested()
try:
    card = CardType(name="Premium", user_id=user.id)
    db.add(card)
    savepoint.commit()  # Подтверждаем savepoint
except:
    savepoint.rollback()  # Откатываем только savepoint
    # user остаётся в транзакции

# Основной commit
db.commit()  # Сохраняет user и возможно card
```

### Визуализация уровней изоляции

```
Уровень изоляции транзакций:

READ UNCOMMITTED  ← Видит незакоммиченные изменения
READ COMMITTED    ← Видит только commit (по умолчанию)
REPEATABLE READ   ← Фиксирует снимок при начале транзакции
SERIALIZABLE      ← Полная изоляция
```

---

## Состояния объектов

### Жизненный цикл объекта в сессии

```
[Создан в Python]
       ↓
   transient ← Объект не связан с сессией
       ↓
   add()
       ↓
   pending ← В сессии, но не в БД
       ↓
   flush()/commit()
       ↓
   persistent ← В сессии И в БД
       ↓
   commit()/close()
       ↓
   detached ← Был в сессии, но сессия закрыта
```

### Проверка состояния

```python
from sqlalchemy import inspect

card = CardType(name="Test")
state = inspect(card)

print(state.transient)   # True - объект новый
print(state.pending)     # False
print(state.persistent)  # False
print(state.detached)    # False

db.add(card)
print(state.pending)     # True - добавлен в сессию

db.flush()
print(state.persistent)  # True - в БД
print(state.pending)     # False

db.commit()
print(state.persistent)  # True - всё ещё в сессии
```

### Состояние после операций

```python
card = CardType(name="Test")

# transient
print(card in db)  # False

db.add(card)
# pending
print(card in db)  # True
print(card.id)     # None

db.flush()
# persistent
print(card.id)     # 1

db.commit()
# persistent (expired)
print(card in db)  # True

db.close()
# detached
print(card in db)  # False
print(card.id)     # 1 (значение закэшировано)
```

---

## Лучшие практики

### 1. Всегда используйте try-except с rollback

```python
# ✅ ПРАВИЛЬНО
try:
    card = CardType(**data)
    db.add(card)
    db.commit()
except Exception as e:
    db.rollback()  # КРИТИЧЕСКИ ВАЖНО
    logger.error(f"Error: {e}")
    raise

# ❌ НЕПРАВИЛЬНО
card = CardType(**data)
db.add(card)
db.commit()  # Если ошибка - сессия "битая"
```

### 2. Один commit для связанных операций

```python
# ✅ Атомарная операция
try:
    user = User(name="John")
    db.add(user)
    db.flush()
    
    profile = Profile(user_id=user.id, bio="...")
    db.add(profile)
    
    db.commit()  # Всё или ничего
except:
    db.rollback()
    raise
```

### 3. Используйте контекстный менеджер

```python
from contextlib import contextmanager

@contextmanager
def get_db_transaction():
    """Автоматический commit/rollback"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

# Использование
with get_db_transaction() as db:
    card = CardType(name="Premium")
    db.add(card)
    # автоматический commit при выходе
```

### 4. Избегайте N+1 проблем

```python
# ❌ ПЛОХО: N+1 запросов
cards = db.query(CardType).all()
for card in cards:
    print(card.owner.name)  # SELECT для каждой карты!

# ✅ ХОРОШО: один запрос
from sqlalchemy.orm import joinedload

cards = db.query(CardType).options(
    joinedload(CardType.owner)
).all()
for card in cards:
    print(card.owner.name)  # Без дополнительных запросов
```

### 5. Используйте bulk операции для больших объёмов

```python
# Для вставки тысяч записей
data = [{"name": f"Card{i}"} for i in range(10000)]

# ❌ МЕДЛЕННО
for item in data:
    db.add(CardType(**item))
db.commit()

# ✅ БЫСТРО
db.bulk_insert_mappings(CardType, data)
db.commit()
```

### 6. Явно указывайте что нужно обновить

```python
# ❌ Неэффективно
card = db.query(CardType).get(1)
card.name = "Updated"
db.commit()  # UPDATE всех полей

# ✅ Эффективно
db.query(CardType).filter(CardType.id == 1).update({
    "name": "Updated"
})
db.commit()  # UPDATE только name
```

### 7. Используйте refresh() после commit

```python
card = CardType(name="Premium")
db.add(card)
db.commit()

# Некоторые поля могут быть установлены БД
db.refresh(card)  # Гарантирует актуальность
print(card.created_at)  # Точное значение из БД
```

### 8. Закрывайте сессии

```python
# FastAPI - автоматическое закрытие
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Или с context manager
with Session() as db:
    # работа с сессией
    pass
# автоматически закроется
```

---

## Типичные ошибки

### Ошибка 1: Забыть rollback при exception

```python
# ❌ ОШИБКА
try:
    db.add(card)
    db.commit()
except:
    pass  # Сессия осталась в битом состоянии!

# ✅ ПРАВИЛЬНО
try:
    db.add(card)
    db.commit()
except:
    db.rollback()  # Обязательно!
    raise
```

### Ошибка 2: Множественные commit для связанных данных

```python
# ❌ ОШИБКА: несогласованное состояние
user = User(name="John")
db.add(user)
db.commit()  # Если дальше ошибка - user останется!

card = CardType(user_id=user.id)
db.add(card)
db.commit()  # Может не выполниться

# ✅ ПРАВИЛЬНО: одна транзакция
try:
    user = User(name="John")
    db.add(user)
    db.flush()
    
    card = CardType(user_id=user.id)
    db.add(card)
    
    db.commit()
except:
    db.rollback()
    raise
```

### Ошибка 3: Работа с detached объектами

```python
# ❌ ОШИБКА
db1 = SessionLocal()
card = CardType(name="Test")
db1.add(card)
db1.commit()
db1.close()  # Объект detached

db2 = SessionLocal()
card.name = "Updated"
db2.commit()  # Ошибка! card не в сессии db2

# ✅ ПРАВИЛЬНО
db1 = SessionLocal()
card = CardType(name="Test")
db1.add(card)
db1.commit()
card_id = card.id
db1.close()

db2 = SessionLocal()
card = db2.query(CardType).get(card_id)
card.name = "Updated"
db2.commit()
```

### Ошибка 4: Использование add() вместо merge()

```python
# ❌ ОШИБКА
card = db.query(CardType).get(1)
db.add(card)  # InvalidRequestError!

# ✅ ПРАВИЛЬНО
card_data = CardType(id=1, name="Updated")
merged = db.merge(card_data)
db.commit()
```

### Ошибка 5: Забыть flush() перед использованием ID

```python
# ❌ ОШИБКА
user = User(name="John")
db.add(user)
card = CardType(user_id=user.id)  # user.id = None!

# ✅ ПРАВИЛЬНО
user = User(name="John")
db.add(user)
db.flush()  # Получаем user.id
card = CardType(user_id=user.id)
db.add(card)
```

### Ошибка 6: Изменение объекта после detach

```python
# ❌ ОШИБКА
card = CardType(name="Test")
db.add(card)
db.commit()
db.close()

card.name = "Updated"  # Изменение потеряно!

# ✅ ПРАВИЛЬНО
card = CardType(name="Test")
db.add(card)
db.commit()

card.name = "Updated"  # Изменение в той же сессии
db.commit()
db.close()
```

---

## Сравнительная таблица операций

| Операция | SQL | Транзакция | Использование |
|----------|-----|------------|---------------|
| `add()` | - | Открыта | Пометить объект для сохранения |
| `flush()` | INSERT/UPDATE/DELETE | Открыта | Получить ID, проверить constraints |
| `commit()` | COMMIT | Закрыта | Сохранить навсегда |
| `rollback()` | ROLLBACK | Закрыта | Отменить изменения |
| `merge()` | SELECT (может) | Открыта | Upsert, безопасное обновление |
| `refresh()` | SELECT | Открыта | Обновить объект из БД |
| `expunge()` | - | Открыта | Удалить объект из сессии |
| `expunge_all()` | - | Открыта | Очистить всю сессию |
| `close()` | - | - | Закрыть сессию |

---

## Дополнительные методы

### expire() и expire_all()

```python
# Пометить объект как устаревший
card = db.query(CardType).get(1)
db.expire(card)
print(card.name)  # Вызовет SELECT

# Пометить все объекты как устаревшие
db.expire_all()
```

### expunge() и expunge_all()

```python
# Удалить объект из сессии (detach)
card = db.query(CardType).get(1)
db.expunge(card)
print(card in db)  # False

# Удалить все объекты из сессии
db.expunge_all()
```

### refresh()

```python
# Перезагрузить объект из БД
card = db.query(CardType).get(1)
card.name = "Modified"
db.refresh(card)  # Отменяет локальные изменения
print(card.name)  # Значение из БД
```

---

## Заключение

### Ключевые принципы

1. **add()** - только маркирует для отслеживания
2. **flush()** - отправляет SQL, но транзакция открыта
3. **commit()** - сохраняет навсегда и закрывает транзакцию
4. **rollback()** - откатывает текущую транзакцию
5. **merge()** - умный upsert для любых ситуаций

### Золотой стандарт

```python
try:
    # Все операции в одной транзакции
    obj1 = Model1(**data1)
    db.add(obj1)
    db.flush()  # Если нужен ID
    
    obj2 = Model2(**data2, foreign_key=obj1.id)
    db.add(obj2)
    
    db.commit()  # Одна атомарная операция
    
except Exception as e:
    db.rollback()  # Обязательный откат
    logger.error(f"Transaction failed: {e}")
    raise
finally:
    db.close()  # Закрыть сессию
```

### Помните

- Транзакция = логическая единица работы
- Один commit = одна атомарная операция  
- Всегда rollback при ошибках
- Не бойтесь flush() для промежуточных результатов
- merge() для upsert-логики

---

## Полезные ссылки

- [SQLAlchemy ORM Tutorial](https://docs.sqlalchemy.org/en/20/orm/tutorial.html)
- [Session Basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)
- [Session API](https://docs.sqlalchemy.org/en/20/orm/session_api.html)
