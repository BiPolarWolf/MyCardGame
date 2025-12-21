from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CardTypeBase(BaseModel):
    name: str = Field(..., min_length=5, max_length=100, description="Название")
    description: str = Field(..., min_length=5, max_length=500, description="Описание")
    image_url: Optional[str] = None


class CardTypeCreate(CardTypeBase):
    pass


class CardTypeResponse(CardTypeBase):
    id: int

    # ВАЖНО! Позволяет создавать из SQLAlchemy объектов
    model_config = ConfigDict(from_attributes=True)


class CardTypeResponseList(BaseModel):
    card_types: list[CardTypeResponse]
    total: int = Field(..., description="Общее кол-во Типов Карт")
