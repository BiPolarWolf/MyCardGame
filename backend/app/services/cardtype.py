from logging import raiseExceptions

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.repositories.cardtype import CardTypeRepository
from app.schemas.cardtype import CardTypeCreate, CardTypeResponse, CardTypeResponseList


class CardTypeService:
    def __init__(self, db: Session):
        self.cardtype_repo = CardTypeRepository(db)

    def get_card_types_all(self) -> CardTypeResponseList:
        cardtypes = self.cardtype_repo.get_all()
        validated_cardtypes = [
            CardTypeResponse.model_validate(cardtype) for cardtype in cardtypes
        ]
        return CardTypeResponseList(
            card_types=validated_cardtypes, total=len(validated_cardtypes)
        )

    def get_card_type_by_id(self, id: int) -> CardTypeResponse:
        card_type = self.cardtype_repo.get_by_id(id)

        if not card_type:
            raise HTTPException(
                status_code=404, detail="Тип карты с таким id не найдена"
            )

        validated_card_type = CardTypeResponse.model_validate(card_type)
        return validated_card_type

    def create_card_type(self, cardtype_data: CardTypeCreate) -> CardTypeResponse:
        card_type = self.cardtype_repo.create_card_type(cardtype_data)
        validated_card_type = CardTypeResponse.model_validate(card_type)
        return validated_card_type
