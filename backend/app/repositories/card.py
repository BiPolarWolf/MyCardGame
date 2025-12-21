from typing import List

from sqlalchemy.orm import Session, joinedload

from app.models import Card
from app.schemas.card import CardCreate


class CardRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_all(self) -> List[Card]:
        return self.db.query(Card).options(joinedload(Card.card_type)).all()

    def get_by_card_type(self, cardtype_id: int) -> List[Card]:
        return (
            self.db.query(Card)
            .options(joinedload(Card.card_type))
            .filter(Card.card_type_id == cardtype_id)
        ).all()

    def get_by_id(self, id: int) -> Card:
        return (
            self.db.query(Card)
            .options(joinedload(Card.card_type))
            .filter(Card.id == id)
            .first()
        )

    def create_card(self, card_data: CardCreate) -> Card:
        new_card = Card(**card_data.model_dump())
        self.db.add(new_card)
        self.db.commit()
        self.db.refresh(new_card)
        return new_card
