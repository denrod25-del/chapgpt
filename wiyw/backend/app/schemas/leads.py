"""Lead-capture + event schemas. Boundary validation happens here (Pydantic v2)."""
import re
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator

E164 = re.compile(r"^\+[1-9]\d{7,14}$")


class ServiceType(str, Enum):
    water_treatment = "water_treatment"
    water_softener = "water_softener"
    whole_house_filter = "whole_house_filter"
    ro_system = "ro_system"
    water_heater = "water_heater"
    tankless = "tankless"
    repipe = "repipe"
    drain = "drain"
    emergency = "emergency"
    leak = "leak"
    other = "other"


class Urgency(str, Enum):
    emergency = "emergency"
    standard = "standard"


class WaterSource(str, Enum):
    city = "city"
    well = "well"
    unknown = "unknown"


class LeadIn(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    phone: str
    email: Optional[str] = Field(default=None, max_length=320)
    service_type: ServiceType
    urgency: Urgency = Urgency.standard
    water_source: WaterSource = WaterSource.unknown
    message: Optional[str] = Field(default=None, max_length=2000)
    source: str = Field(min_length=1, max_length=100)
    source_medium: Optional[str] = Field(default=None, max_length=100)
    source_campaign: Optional[str] = Field(default=None, max_length=200)
    landing_page: Optional[str] = Field(default=None, max_length=500)
    city: Optional[str] = Field(default=None, max_length=100)
    postal_code: Optional[str] = Field(default=None, max_length=10)

    @field_validator("phone")
    @classmethod
    def _phone_e164(cls, v: str) -> str:
        v = v.strip()
        assert E164.match(v), "phone must be E.164 (e.g. +15615550123)"
        return v


class LeadOut(BaseModel):
    id: str
    status: str


class QuoteIn(BaseModel):
    full_name: str = Field(min_length=1, max_length=200)
    phone: str
    email: Optional[str] = None
    service_type: str = Field(min_length=1, max_length=50)
    details: Optional[str] = Field(default=None, max_length=2000)
    source: str = "website"

    @field_validator("phone")
    @classmethod
    def _phone(cls, v: str) -> str:
        v = v.strip()
        assert E164.match(v), "phone must be E.164"
        return v


class EventIn(BaseModel):
    event_name: str = Field(min_length=1, max_length=100)
    lead_id: Optional[str] = None
    customer_id: Optional[str] = None
    payload: dict = Field(default_factory=dict)
    source_system: Optional[str] = None
