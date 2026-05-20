# TypeSpec Parser for Python

A Python library that parses TypeSpec definitions and generates idiomatic data models for Python, C++, Rust, Go, Zig, and V.

## Features

- Parse TypeSpec model definitions
- Generate Python dataclasses with type hints
- Generate C++ headers
- Generate Rust structs and enums
- Generate Go structs, string enum aliases, constants, and JSON tags
- Generate Zig structs and enums
- Generate V structs and enums
- Support for enums
- Support for 1:1 and 1:n relationships
- Command-line interface

## Installation

### Using uv

```bash
uv pip install tsc-py
```

### Running without installing

```bash
uvx tsc-py schema.tsp
```

## Usage

### Command Line

```bash
# Parse a TypeSpec file and output to stdout
tsc-py schema.tsp

# Parse a TypeSpec file and save to a Python file
tsc-py schema.tsp -o models.py

# Generate other languages
tsc-py schema.tsp --language rust -o models.rs
tsc-py schema.tsp --language go -o models.go
tsc-py schema.tsp --language zig -o models.zig
tsc-py schema.tsp --language vlang -o models.v

# Use a custom Jinja template for the selected language
tsc-py schema.tsp --language rust --template custom-rust.j2 -o models.rs
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
code = parser.generate_python()
print(code)

# Generate Rust, Go, Zig, or V
rust_code = parser.generate_rust()
go_code = parser.generate_go(package_name="models")
zig_code = parser.generate_zig()
v_code = parser.generate_vlang(module_name="models")

# Override the built-in Jinja template
custom_rust = parser.generate_rust(template_path="custom-rust.j2")
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

It can also generate idiomatic models for other languages:

```rust
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum Status {
    Active,
    Inactive,
}

#[derive(Debug, Clone, PartialEq)]
pub struct User {
    pub name: String,
    pub age: i32,
    pub email: Option<String>,
    pub addresses: Vec<Address>,
}
```

```go
package typespec

type Status string

const (
    StatusActive Status = "active"
    StatusInactive Status = "inactive"
)

type User struct {
    Name string `json:"name"`
    Age int `json:"age"`
    Email *string `json:"email"`
    Addresses []Address `json:"addresses"`
}
```

```zig
const std = @import("std");

pub const Status = enum {
    active,
    inactive,
};

pub const User = struct {
    name: []const u8,
    age: i32,
    email: ?[]const u8,
    addresses: []Address,
};
```

```v
module typespec

pub enum Status {
    active
    inactive
}

pub struct User {
pub:
    name string
    age int
    email ?string
    addresses []Address
}
```

See [Code Generation](docs/code-generation.md) for language-specific notes and custom template context.

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
