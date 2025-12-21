from typing import List

from sqlalchemy.orm import Session

from app.models import CardType
from app.schemas.cardtype import CardTypeCreate


class CardTypeRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_all(self) -> List[CardType]:
        return self.db.query(CardType).all()

    def get_by_id(self, id: int) -> CardType:
        return self.db.query(CardType).filter(CardType.id == id).first()

    def create_card_type(self, card_type_data: CardTypeCreate) -> CardType:
        new_card_type = CardType(**card_type_data.model_dump())
        self.db.add(new_card_type)
        self.db.commit()
        self.db.refresh(new_card_type)
        return new_card_type
