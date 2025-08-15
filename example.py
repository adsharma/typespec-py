from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class ColorEnum(Enum):
    RED = "red"
    BLUE = "blue"


class Status(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class WidgetKind(Enum):
    HEAVY = "Heavy"
    LIGHT = "Light"


@dataclass
class Address:
    street: str
    city: str
    country: str


@dataclass
class User:
    name: str
    age: int
    email: Optional[str]
    address: object
    tags: List[str]
    addresses: List[object]


@dataclass
class Company:
    name: str
    status: Status
    employees: List[object]


@dataclass
class WidgetBase:
    id: str
    weight: str
    color: ColorEnum


@dataclass
class HeavyWidget:
    kind: WidgetKind


@dataclass
class LightWidget:
    kind: WidgetKind


@dataclass
class Error:
    code: str
    message: str
