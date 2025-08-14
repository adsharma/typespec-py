from dataclasses import dataclass
from enum import Enum


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


@dataclass
class User:
    name: str
    age: int


@dataclass
class Company:
    name: str
    status: Status


@dataclass
class WidgetBase:
    id: str
    weight: str


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
