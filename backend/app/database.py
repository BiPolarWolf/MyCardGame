from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.settings import settings

# connect_args={"check_same_thread": False} - специфичная настройка для sqlite
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})

# Фабрика сессий которая будет создавать новый инстанс сессии во время каждого нашего запроса
# смотрит на engine который мы настроили на нашу bd через settings.database_url
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


# это класс спомощью которого мы сможем создавать модели SqlAlchemy
# 1. Модели создают таблицы в базе данных через  init_db
# 2. Через эти модели мы можем делать запросы к таблицам из ОРМ
# | user = db.query(User).first() | где User это Класс Модели наследуемый от Base
Base = declarative_base()


# это мы будем использовать в роутах чтобы прямо там
# открывать эту сессию и когда наша вьюха завершит работу
# она выполнит код в finally чтобы закрыть сессию наверняка
# в папке guides создал гайд depends_yield_db.md
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# используется в main.py где мы инициализируем наш приложение на фастапи
# все sqlalchemy модели которые мы создавали он создает как таблицы в бд если их нет
# если они есть то он их не трогает - даже если мы как то изменили модель - он смотрит
# только на ее наличие в базе
def init_db():
    Base.metadata.create_all(bind=engine)
