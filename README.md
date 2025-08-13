# TypeSpec Parser for Python

A Python library that parses TypeSpec definitions and generates Python dataclasses.

## Features

- Parse TypeSpec model definitions
- Generate Python dataclasses with type hints
- Support for enums
- Support for 1:1 and 1:n relationships
- Command-line interface

## Installation

### Using pip

```bash
pip install typespec-parser
```

### Using uv (recommended)

```bash
uv sync --dev
```

## Usage

### Command Line

```bash
# Parse a TypeSpec file and output to stdout
typespec-parser schema.tsp

# Parse a TypeSpec file and save to a Python file
typespec-parser schema.tsp -o models.py
```

### Python API

```python
from typespec_parser import TypeSpecParser

parser = TypeSpecParser()
parser.parse("""
model User {
  name: string;
  age: integer;
  email: string?;
}

enum Status {
  active,
  inactive,
}
""")

# Generate Python dataclasses
code = parser.generate_dataclasses()
print(code)
```

## Example

Given the following TypeSpec:

```typespec
model User {
  name: string;
  age: integer;
  email: string?;
  addresses: Address[];
}

model Address {
  street: string;
  city: string;
  country: string;
}

enum Status {
  active,
  inactive,
}
```

The parser will generate:

```python
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

class Status(Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'

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
    addresses: List[Address]
```

## Development

This project uses `uv` for dependency management and packaging.

To install dependencies and set up the development environment:

```bash
uv sync --dev
```

To run tests:

```bash
uv run pytest
```

## License

MIT
