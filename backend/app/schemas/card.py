
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict



class CardBase(BaseModel):
    name: str = Field(..., min_length=5, max_length=100, description="Название")
    description: str = Field(..., min_length=2, max_length=500, description="Описание")
    mana_price: int = Field(default=1, ge=0, le=10, description="Расход маны")
    image_url : Optional[str] = None
    hp: int = Field(default=100, ge=0, le=100, description="Здоровье")
    attack: int = Field(default=50, ge=0, le=100, description="Урон")

    card_type_id : int = Field(..., description="Тип Карты")
    # card_type = relationship("CardType", back_populates="cards")


class CardCreate(CardBase)
    pass


class CardUpdate(CardBase)
    pass


class CardResponse(CardBase):
    id : int


    # ВАЖНО! Позволяет создавать из SQLAlchemy объектов
    model_config = ConfigDict(from_attributes=True)
