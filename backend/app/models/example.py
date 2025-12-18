# from sqlalchemy import Column, Integer, String
# from database import Base

# # 1. Берем наш Base и создаем от него наследника
# class User(Base):
#     __tablename__ = "users" # Имя таблицы в самой БД

#     id = Column(Integer, primary_key=True)
#     username = Column(String)
#     email = Column(String)

# Теперь, когда ты сделаешь запрос к базе:
# user = db.query(User).first()
# Ты получишь не просто текст или цифры, а объект,
# у которого можно вызвать user.username. Это и есть "python данные".
