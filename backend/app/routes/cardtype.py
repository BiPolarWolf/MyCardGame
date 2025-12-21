from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.cardtype import CardTypeCreate, CardTypeResponse, CardTypeResponseList
from app.services.cardtype import CardTypeService

router = APIRouter(prefix="/api/cardtypes", tags=["Типы Карт"])


@router.get(
    "",
    name="Cписок типов карт",
    status_code=status.HTTP_200_OK,
    response_model=CardTypeResponseList,
)
def get_cardtypes(db: Session = Depends(get_db)):
    service = CardTypeService(db)
    return service.get_card_types_all()


@router.get(
    "/{cardtype_id}",
    name="Детали типа карты",
    response_model=CardTypeResponse,
    status_code=status.HTTP_200_OK,
)
def get_cardtype_by_id(cardtype_id: int, db: Session = Depends(get_db)):
    service = CardTypeService(db)
    return service.get_card_type_by_id(cardtype_id)


@router.post(
    "/create",
    name="Создание типа карты",
    response_model=CardTypeResponse,
    status_code=status.HTTP_200_OK,
)
def create_card(cardtype_data: CardTypeCreate, db: Session = Depends(get_db)):
    service = CardTypeService(db)
    return service.create_card_type(cardtype_data)
