# Code Generation

`tsc-py` parses TypeSpec models and enums, then renders code with language-specific templates in `templates/`.

## CLI

Generate Python dataclasses:

```bash
tsc-py schema.tsp --language python -o models.py
```

Generate C++ headers:

```bash
tsc-py schema.tsp --language cpp -o models.hpp
```

Generate Rust:

```bash
tsc-py schema.tsp --language rust -o models.rs
```

Generate Go:

```bash
tsc-py schema.tsp --language go -o models.go
```

`golang` is accepted as an alias for `go`.

Generate Zig:

```bash
tsc-py schema.tsp --language zig -o models.zig
```

Generate V:

```bash
tsc-py schema.tsp --language vlang -o models.v
```

`v` is accepted as an alias for `vlang`.

Use a custom Jinja template for the selected language:

```bash
tsc-py schema.tsp --language rust --template custom-rust.j2 -o models.rs
```

## Python API

```python
from typespec_parser import TypeSpecParser

parser = TypeSpecParser()
parser.parse(open("schema.tsp").read())

python_code = parser.generate_python()
cpp_code = parser.generate_cpp_headers()
rust_code = parser.generate_rust()
go_code = parser.generate_go(package_name="models")
zig_code = parser.generate_zig()
v_code = parser.generate_vlang(module_name="models")

custom_python = parser.generate_python(template_path="custom-python.j2")
custom_rust = parser.generate_rust(template_path="custom-rust.j2")
```

## Language Notes

Rust output uses `pub struct` and `pub enum`, derives common debug/clone/equality traits, maps optional fields to `Option<T>`, and maps arrays to `Vec<T>`. Field names are converted to `snake_case`.

Go output uses exported struct fields, JSON tags preserving the original TypeSpec field names, string aliases for enums, and typed constants for enum values. Optional fields become pointers and arrays become slices.

Zig output uses `pub const` structs and enums. Optional fields become `?T`, arrays become `[]T`, strings become `[]const u8`, and field names are converted to `snake_case`.

V output uses `module`, `pub struct`, and `pub enum`. Optional fields become `?T`, arrays become `[]T`, strings become `string`, and field names are converted to `snake_case`.

## Type Mapping

| TypeSpec | Rust | Go | Zig | V |
| --- | --- | --- | --- | --- |
| `string` | `String` | `string` | `[]const u8` | `string` |
| `integer` / `int32` | `i32` | `int` | `i32` | `int` |
| `boolean` | `bool` | `bool` | `bool` | `bool` |
| `T?` | `Option<T>` | `*T` | `?T` | `?T` |
| `T[]` | `Vec<T>` | `[]T` | `[]T` | `[]T` |

## Custom Templates

`--template` replaces only the final Jinja template. Parsing, naming, and type mapping still come from the selected `--language`.

Python and C++ templates receive:

| Name | Description |
| --- | --- |
| `synthetic_enums` | String-literal union enums keyed by generated enum name |
| `enums` | TypeSpec enums keyed by enum name |
| `dataclasses` | Object definitions with `name` and rendered `fields` |

Rust and Zig templates receive:

| Name | Description |
| --- | --- |
| `enums` | TypeSpec and synthetic enums keyed by enum name |
| `structs` | Object definitions with `name` and rendered `fields` |

Go templates receive `package_name`, `enums`, and `structs`. Go struct fields include `name`, `type`, and `json_name`.

V templates receive `module_name`, `enums`, and `structs`.
