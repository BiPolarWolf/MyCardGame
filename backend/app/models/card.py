from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class CardType(Base):
    __tablename__ = "card_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String)
    image_url = Column(String)

    cards = relationship("Card", back_populates="card_type")

    def __repr__(self):
        return f"<CardType(id={self.id}, name='{self.name}')>"


class Card(Base):
    __tablename__ = "cards"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String)
    image_url = Column(String)
    mana_price = Column(Integer, index=True, default=1)
    hp = Column(Integer, default=100)
    attack = Column(Integer, default=50)

    card_type_id = Column(Integer, ForeignKey("card_types.id"), nullable=False)
    card_type = relationship("CardType", back_populates="cards")

    def __repr__(self):
        return f"<Card(id={self.id}, name='{self.name}')>"


# relationship создаёт атрибут, back_populates — только связывает.
# Если ты написал relationship только в Card, то:
# card.card_type → будет
# card_type.cards → не будет
# back_populates="cards" не создаёт CardType.cards, он лишь говорит:
# “эта связь соответствует уже существующей связи cards”
# Чтобы CardType.cards существовало — relationship должен быть объявлен и там.
# Запомни формулу:
# 👉 нет relationship — нет атрибута, back_populates магию не делает.
