from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


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
    address: Address
    tags: List[str]
    addresses: List[Address]


@dataclass
class Company:
    name: str
    status: Status
    employees: List[User]


@dataclass
class WidgetBase:
    id: str
    weight: str
    color: "red" | "blue"


@dataclass
class HeavyWidget:
    kind: WidgetKind.HEAVY


@dataclass
class LightWidget:
    kind: WidgetKind.LIGHT


@dataclass
class Error:
    code: str
    message: str
