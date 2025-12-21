from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.card import CardCreate, CardResponse, CardResponseList
from app.services.card import CardService

router = APIRouter(prefix="/api/cards", tags=["Карты"])


@router.get(
    "",
    name="Список Карт",
    status_code=status.HTTP_200_OK,
    response_model=CardResponseList,
)
def get_products(db: Session = Depends(get_db)):
    service = CardService(db)
    return service.get_cards_all()


@router.get(
    "/{card_id}",
    name="Детали карты",
    response_model=CardResponse,
    status_code=status.HTTP_200_OK,
)
def get_card_by_id(card_id: int, db: Session = Depends(get_db)):
    service = CardService(db)
    return service.get_card_by_id(card_id)


@router.post(
    "/create",
    name="Создание карты",
    response_model=CardResponse,
    status_code=status.HTTP_200_OK,
)
def create_card(card_data: CardCreate, db: Session = Depends(get_db)):
    service = CardService(db)
    return service.create_card(card_data)
