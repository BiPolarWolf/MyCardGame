from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.settings import settings

engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})

# Фабрика сессий которая будет создавать новый инстанс сессии во время каждого нашего запроса
# смотрит на engine который мы настроили на нашу bd через settings.database_url
# connect_args={"check_same_thread": False} - специфичная настройка для sqlite
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


# это класс спомощью которого мы сможем создавать модели SqlAlchemy
# 1. Модели создают таблицы в базе данных через  init_db
# 2. Через эти модели мы можем делать запросы к таблицам из ОРМ
# | user = db.query(User).first() | где User это Класс Модели наследуемый от Base
Base = declarative_base()


# это мы будем использовать в роутах чтобы прямо там
# открывать эту сессию и когда наша вьюха завершит работу
# она выполнит код в finally чтобы закрыть сессию наверняка
# я пожалуй создам пример в папке app yield.md в котором
# напишу то как работает функция с yield
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
