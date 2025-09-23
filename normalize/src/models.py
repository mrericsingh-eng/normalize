from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class Contact(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None  # numeric only, e.g. "9175551234"
    zip: Optional[str] = None


class Entity(BaseModel):
    type: Literal["city", "country", "hotel", "restaurant"]
    value: str = Field(..., description="Lowercase entity value")


class Enrichment(BaseModel):
    local_emergency_numbers: Optional[List[str]] = None
    city_typo: Optional[str] = None
    country_typo: Optional[str] = None
    phone_number_typo: Optional[str] = None
    zip_code_typo: Optional[str] = None


class NormalizeIn(BaseModel):
    message_id: str
    text: str


class NormalizeOut(BaseModel):
    message_id: str
    category: Literal["urgent", "high_risk", "base"]
    contact: Optional[Contact] = None
    entities: Optional[List[Entity]] = None
    enrichment: Optional[Enrichment] = None
