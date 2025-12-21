from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.card import CardRepository
from app.schemas.card import CardCreate, CardResponse, CardResponseList


class CardService:
    def __init__(self, db: Session):
        self.card_repo = CardRepository(db)

    def get_cards_all(self) -> CardResponseList:
        cards = self.card_repo.get_all()
        validated_cards = [CardResponse.model_validate(card) for card in cards]
        return CardResponseList(products=validated_cards, total=len(validated_cards))

    def get_card_by_id(self, id: int) -> CardResponse:
        card = self.card_repo.get_by_id(id)

        if not card:
            raise HTTPException(status_code=404, detail="Карта с таким id не найдена")

        return CardResponse.model_validate(card)

    def get_by_card_type(self, cardtype_id: int) -> CardResponseList:
        cards = self.card_repo.get_by_card_type(cardtype_id)
        validated_cards = [CardResponse.model_validate(card) for card in cards]
        return CardResponseList(products=validated_cards, total=len(validated_cards))

    def create_card(self, card_data: CardCreate) -> CardResponse:
        card = self.card_repo.create_card(card_data)
        return CardResponse.model_validate(card)
