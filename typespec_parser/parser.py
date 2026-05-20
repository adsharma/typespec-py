"""TypeSpec parser that generates Python dataclasses using parsimonious."""

import re
from dataclasses import dataclass, field
from enum import Enum
from importlib import resources
from typing import Dict, List, Optional

from jinja2 import Template

# Try to import our parsimonious parser
try:
    from .parsimonious_parser import parse_typespec as parsimonious_parse

    PARSIMONIOUS_AVAILABLE = True
except ImportError:
    PARSIMONIOUS_AVAILABLE = False


class TypeSpecType(Enum):
    """Enumeration of TypeSpec types."""

    STRING = "string"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    ENUM = "enum"
    OBJECT = "object"
    ARRAY = "array"


@dataclass
class TypeSpecField:
    """Represents a field in a TypeSpec definition."""

    name: str
    type: str
    is_optional: bool = False
    is_array: bool = False
    reference: Optional[str] = None


@dataclass
class TypeSpecDefinition:
    """Represents a TypeSpec definition (class or enum)."""

    name: str
    type: TypeSpecType
    fields: List[TypeSpecField] = field(default_factory=list)
    values: List[str] = field(default_factory=list)


class TypeSpecParser:
    """Parses TypeSpec definitions and generates Python dataclasses."""

    @staticmethod
    def _load_builtin_template(name: str) -> Template:
        """Load a bundled template from package data."""
        template_text = (
            resources.files("typespec_parser")
            .joinpath("templates", name)
            .read_text(encoding="utf-8")
        )
        return Template(template_text)

    def __init__(self):
        self.definitions: Dict[str, TypeSpecDefinition] = {}
        self.synthetic_enums: Dict[str, List[str]] = {}  # For string literal unions

    @staticmethod
    def _normalize_enum_member(value: str) -> str:
        """Convert enum member name to uppercase Python enum format."""
        return value.upper().replace("-", "_").replace(" ", "_")

    @staticmethod
    def _render_template(
        default_template_name: str,
        template_path: Optional[str] = None,
        **context,
    ) -> str:
        """Render the default template or an override template path."""
        if template_path:
            with open(template_path, encoding="utf-8") as f:
                template = Template(f.read())
        else:
            template = TypeSpecParser._load_builtin_template(default_template_name)
        return template.render(**context)

    @staticmethod
    def _split_identifier(value: str) -> List[str]:
        """Split a TypeSpec identifier or string literal into word parts."""
        value = value.strip().strip('"').strip("'")
        value = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value)
        return [part for part in re.split(r"[^0-9A-Za-z]+|\s+", value) if part]

    @classmethod
    def _to_pascal_case(cls, value: str) -> str:
        """Convert an identifier to PascalCase."""
        parts = cls._split_identifier(value)
        if not parts:
            return "Value"
        result = "".join(part[:1].upper() + part[1:] for part in parts)
        if result[0].isdigit():
            result = f"Value{result}"
        return result

    @classmethod
    def _to_snake_case(cls, value: str) -> str:
        """Convert an identifier to snake_case."""
        parts = cls._split_identifier(value)
        if not parts:
            return "value"
        result = "_".join(part.lower() for part in parts)
        if result[0].isdigit():
            result = f"value_{result}"
        return result

    @classmethod
    def _to_zig_identifier(cls, value: str) -> str:
        """Convert a value to a Zig enum field identifier."""
        snake = cls._to_snake_case(value)
        zig_keywords = {
            "align",
            "allowzero",
            "and",
            "anyframe",
            "anytype",
            "asm",
            "async",
            "await",
            "break",
            "catch",
            "comptime",
            "const",
            "continue",
            "defer",
            "else",
            "enum",
            "errdefer",
            "error",
            "export",
            "extern",
            "fn",
            "for",
            "if",
            "inline",
            "noalias",
            "noinline",
            "nosuspend",
            "opaque",
            "or",
            "orelse",
            "packed",
            "pub",
            "resume",
            "return",
            "linksection",
            "struct",
            "suspend",
            "switch",
            "test",
            "threadlocal",
            "try",
            "union",
            "unreachable",
            "usingnamespace",
            "var",
            "volatile",
            "while",
        }
        if snake in zig_keywords:
            return f'@"{snake}"'
        return snake

    def parse(self, typespec_content: str) -> Dict[str, TypeSpecDefinition]:
        """Parse TypeSpec content and return definitions."""
        # Try to use parsimonious parser if available
        if PARSIMONIOUS_AVAILABLE:
            return self._parse_with_parsimonious(typespec_content)
        else:
            raise Exception("Parsimonious parser not available")

        # Fallback disabled - use only parsimonious parser
        # return self._parse_with_lines(typespec_content)

    def _parse_with_parsimonious(
        self, typespec_content: str
    ) -> Dict[str, TypeSpecDefinition]:
        """Parse TypeSpec content using our parsimonious parser."""
        parsimonious_definitions = parsimonious_parse(typespec_content)

        self.definitions = {}
        self.synthetic_enums = {}
        for name, parsimonious_def in parsimonious_definitions.items():
            if parsimonious_def.type.name == "ENUM":
                definition_type = TypeSpecType.ENUM
            else:
                definition_type = TypeSpecType.OBJECT

            definition = TypeSpecDefinition(
                name=name, type=definition_type, fields=[], values=[]
            )

            if parsimonious_def.type.name == "ENUM":
                definition.values = parsimonious_def.values
            else:
                # Scan fields for union of string literals
                new_fields = []
                for field_obj in parsimonious_def.fields:
                    if (
                        hasattr(field_obj, "type")
                        and isinstance(field_obj.type, str)
                        and "|" in field_obj.type
                    ):
                        # Check if all union members are string literals
                        members = [m.strip() for m in field_obj.type.split("|")]
                        if all(m.startswith('"') and m.endswith('"') for m in members):
                            enum_name = f"{field_obj.name.capitalize()}Enum"
                            enum_values = [m.strip('"') for m in members]
                            self.synthetic_enums[enum_name] = enum_values
                            field_obj.reference = enum_name
                            field_obj.type = "enum"
                    new_fields.append(field_obj)
                definition.fields = new_fields

            self.definitions[name] = definition
        return self.definitions

    def _parse_with_lines(self, typespec_content: str) -> Dict[str, TypeSpecDefinition]:
        """Parse TypeSpec content using line-based approach."""
        lines = typespec_content.strip().split("\n")
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines and comments
            if not line or line.startswith("//"):
                i += 1
                continue

            # Parse model definitions
            if line.startswith("model "):
                i = self._parse_model(lines, i)
            # Parse enum definitions
            elif line.startswith("enum "):
                i = self._parse_enum(lines, i)
            else:
                i += 1

        return self.definitions

    def _parse_model(self, lines: List[str], start_index: int) -> int:
        """Parse a model definition."""
        # Extract model name (handle decorators and other keywords)
        model_line = lines[start_index].strip()

        # Skip decorators
        while model_line.startswith("@"):
            start_index += 1
            model_line = lines[start_index].strip()

        # Extract model name, handling various syntax
        model_parts = model_line.split()
        model_idx = model_parts.index("model") if "model" in model_parts else 0
        model_name = (
            model_parts[model_idx + 1].split("{")[0].split("(")[0].split("<")[0]
        )

        # Create definition
        definition = TypeSpecDefinition(name=model_name, type=TypeSpecType.OBJECT)

        # Parse fields
        i = start_index + 1
        while i < len(lines) and not lines[i].strip().startswith("}"):
            line = lines[i].strip()

            # Skip empty lines and comments
            if not line or line.startswith("//"):
                i += 1
                continue

            # Handle decorators on separate lines from field definitions
            if line.startswith("@"):
                # Parse the decorator line as a field (the decorator handling is in _parse_field)
                field = self._parse_field(line)
                if field:
                    definition.fields.append(field)
                i += 1
            else:
                # Parse field
                field = self._parse_field(line)
                if field:
                    definition.fields.append(field)
                i += 1

        self.definitions[model_name] = definition
        return i + 1  # Skip closing brace

    def _parse_enum(self, lines: List[str], start_index: int) -> int:
        """Parse an enum definition."""
        # Extract enum name (handle decorators)
        enum_line = lines[start_index].strip()

        # Skip decorators
        while enum_line.startswith("@"):
            start_index += 1
            enum_line = lines[start_index].strip()

        # Extract enum name
        enum_parts = enum_line.split()
        enum_idx = enum_parts.index("enum") if "enum" in enum_parts else 0
        enum_name = enum_parts[enum_idx + 1].split("{")[0]

        # Create definition
        definition = TypeSpecDefinition(name=enum_name, type=TypeSpecType.ENUM)

        # Parse values
        i = start_index + 1
        while i < len(lines) and not lines[i].strip().startswith("}"):
            line = lines[i].strip()

            # Skip empty lines and comments
            if not line or line.startswith("//"):
                i += 1
                continue

            # Skip decorators
            if line.startswith("@"):
                i += 1
                continue

            # Extract enum value, handling trailing commas and semicolons
            value = line.split(",")[0].split(";")[0].strip()
            if value:
                definition.values.append(value)

            i += 1

        self.definitions[enum_name] = definition
        return i + 1  # Skip closing brace

    def _parse_field(self, line: str) -> Optional[TypeSpecField]:
        """Parse a field definition."""
        # Remove trailing semicolon or comma
        line = line.rstrip(";,")

        # Check for @key decorator
        has_key_decorator = "@key" in line

        # Extract decorators but keep important ones
        while line.startswith("@"):
            # Find the end of the decorator
            if "(" in line and ")" in line:
                # Simple case: decorator with parentheses
                end_paren = line.find(")") + 1
                line = line[end_paren:].strip()
            elif " " in line:
                # Decorator without parentheses
                parts = line.split(" ", 1)
                line = parts[1] if len(parts) > 1 else ""
            else:
                # Just the decorator name, move to the next part
                # This handles cases like "@key id: string;"
                parts = line.split(" ", 1)
                if len(parts) > 1:
                    line = parts[1]
                else:
                    # Malformed line, skip it
                    return None

        # Check if optional (marked with ?)
        is_optional = "?" in line
        if is_optional:
            # Remove the ? but be careful not to remove it from string literals
            parts = line.split(":")
            if len(parts) >= 2:
                # Check if ? is in the type part (after the colon)
                type_part = parts[-1].strip()
                if type_part.endswith("?"):
                    type_part = type_part[:-1]
                    parts[-1] = type_part
                    line = ":".join(parts)
            else:
                # ? is in the name part, which shouldn't happen but let's handle it
                line = line.replace("?", "")

        # Split into name and type
        if ":" not in line:
            return None

        name, type_str = line.split(":", 1)
        name = name.strip()
        type_str = type_str.strip()

        # Handle union types like "red" | "blue"
        if "|" in type_str:
            # For union types with string literals, create an enum-like string
            if '"' in type_str or "'" in type_str:
                field_type = "string"
            else:
                # For other union types, treat as object
                field_type = "object"
            is_array = False
            reference = None
        else:
            # Check if array (marked with [])
            is_array = type_str.endswith("[]")
            if is_array:
                type_str = type_str[:-2]  # Remove []

            # Handle references to other models and special types
            reference = None
            if type_str in ["string", "integer", "int32", "boolean"]:
                field_type = type_str
                # Normalize int32 to integer
                if field_type == "int32":
                    field_type = "integer"
            elif "." in type_str:
                # Handle enum member references like WidgetKind.Heavy
                enum_ref, member_name = type_str.split(".", 1)
                if (
                    enum_ref in self.definitions
                    and self.definitions[enum_ref].type == TypeSpecType.ENUM
                ):
                    # Convert enum member name to uppercase Python enum format
                    python_member_name = self._normalize_enum_member(member_name)
                    field_type = "object"
                    reference = f"{enum_ref}.{python_member_name}"
                elif enum_ref in self.definitions:
                    field_type = "object"
                    reference = enum_ref
                else:
                    field_type = "string"
            elif type_str in self.definitions:
                field_type = "object"
                reference = type_str
            else:
                # Default to string for unknown types
                field_type = "string"

        # Add @key decorator back to the field name if it was present
        if has_key_decorator:
            name = "@key " + name

        return TypeSpecField(
            name=name,
            type=field_type,
            is_optional=is_optional,
            is_array=is_array,
            reference=reference,
        )

    def generate_python(self, template_path: Optional[str] = None) -> str:
        """Generate Python dataclasses from parsed definitions."""
        if not self.definitions:
            return ""

        # Prepare data for template
        synthetic_enums = {}
        for enum_name, values in self.synthetic_enums.items():
            normalized_values = [self._normalize_enum_member(v) for v in values]
            synthetic_enums[enum_name] = list(zip(normalized_values, values))

        enums = {}
        for name, definition in self.definitions.items():
            if definition.type == TypeSpecType.ENUM:
                normalized_values = [
                    self._normalize_enum_member(v) for v in definition.values
                ]
                enums[name] = {
                    "values": (
                        list(zip(normalized_values, definition.values))
                        if definition.values
                        else []
                    )
                }

        dataclasses = []
        for name, definition in self.definitions.items():
            if definition.type == TypeSpecType.OBJECT:
                field_lines = [
                    self._generate_field(field) for field in definition.fields
                ]
                dataclasses.append({"name": name, "fields": field_lines})

        return self._render_template(
            "py-dataclasses.j2",
            template_path,
            synthetic_enums=synthetic_enums,
            enums=enums,
            dataclasses=dataclasses,
        )

    def generate_cpp_headers(self, template_path: Optional[str] = None) -> str:
        """Generate C++ headers from parsed definitions."""
        if not self.definitions:
            return ""

        # Prepare data for template
        synthetic_enums = {}
        for enum_name, values in self.synthetic_enums.items():
            normalized_values = [self._normalize_enum_member(v) for v in values]
            synthetic_enums[enum_name] = list(zip(normalized_values, values))

        enums = {}
        for name, definition in self.definitions.items():
            if definition.type == TypeSpecType.ENUM:
                normalized_values = [
                    self._normalize_enum_member(v) for v in definition.values
                ]
                enums[name] = {
                    "values": (
                        list(zip(normalized_values, definition.values))
                        if definition.values
                        else []
                    )
                }

        dataclasses = []
        for name, definition in self.definitions.items():
            if definition.type == TypeSpecType.OBJECT:
                field_lines = [
                    self._generate_cpp_field(field) for field in definition.fields
                ]
                dataclasses.append({"name": name, "fields": field_lines})

        return self._render_template(
            "cpp-headers.j2",
            template_path,
            synthetic_enums=synthetic_enums,
            enums=enums,
            dataclasses=dataclasses,
        )

    def generate_rust(self, template_path: Optional[str] = None) -> str:
        """Generate idiomatic Rust structs and enums from parsed definitions."""
        if not self.definitions:
            return ""

        enums = self._prepare_enum_data(self._to_pascal_case)
        structs = []
        for name, definition in self.definitions.items():
            if definition.type == TypeSpecType.OBJECT:
                field_lines = [
                    self._generate_rust_field(field) for field in definition.fields
                ]
                structs.append({"name": name, "fields": field_lines})

        return self._render_template(
            "rust.j2",
            template_path,
            enums=enums,
            structs=structs,
        )

    def generate_go(
        self,
        package_name: str = "typespec",
        template_path: Optional[str] = None,
    ) -> str:
        """Generate idiomatic Go structs, aliases, and constants."""
        if not self.definitions:
            return ""

        enums = self._prepare_go_enum_data()
        structs = []
        for name, definition in self.definitions.items():
            if definition.type == TypeSpecType.OBJECT:
                fields = [self._generate_go_field(field) for field in definition.fields]
                structs.append({"name": name, "fields": fields})

        return self._render_template(
            "go.j2",
            template_path,
            package_name=package_name,
            enums=enums,
            structs=structs,
        )

    def generate_zig(self, template_path: Optional[str] = None) -> str:
        """Generate idiomatic Zig structs and enums from parsed definitions."""
        if not self.definitions:
            return ""

        enums = self._prepare_enum_data(self._to_zig_identifier)
        structs = []
        for name, definition in self.definitions.items():
            if definition.type == TypeSpecType.OBJECT:
                field_lines = [
                    self._generate_zig_field(field) for field in definition.fields
                ]
                structs.append({"name": name, "fields": field_lines})

        return self._render_template(
            "zig.j2",
            template_path,
            enums=enums,
            structs=structs,
        )

    def generate_vlang(
        self,
        module_name: str = "typespec",
        template_path: Optional[str] = None,
    ) -> str:
        """Generate idiomatic V structs and enums from parsed definitions."""
        if not self.definitions:
            return ""

        enums = self._prepare_enum_data(self._to_snake_case)
        structs = []
        for name, definition in self.definitions.items():
            if definition.type == TypeSpecType.OBJECT:
                field_lines = [
                    self._generate_vlang_field(field) for field in definition.fields
                ]
                structs.append({"name": name, "fields": field_lines})

        return self._render_template(
            "vlang.j2",
            template_path,
            module_name=module_name,
            enums=enums,
            structs=structs,
        )

    def _prepare_enum_data(self, normalizer) -> Dict[str, Dict[str, List[str]]]:
        """Prepare normal enum and synthetic string-union enum data."""
        enums = {}
        for enum_name, values in self.synthetic_enums.items():
            enums[enum_name] = {
                "values": list(zip([normalizer(v) for v in values], values))
            }

        for name, definition in self.definitions.items():
            if definition.type == TypeSpecType.ENUM:
                enums[name] = {
                    "values": list(
                        zip(
                            [normalizer(v) for v in definition.values],
                            definition.values,
                        )
                    )
                }

        return enums

    def _prepare_go_enum_data(self) -> Dict[str, Dict[str, List[Dict[str, str]]]]:
        """Prepare Go enum aliases and constants."""
        enums = {}
        for enum_name, values in self.synthetic_enums.items():
            enums[enum_name] = {
                "values": [
                    {
                        "const_name": f"{enum_name}{self._to_pascal_case(value)}",
                        "value": value,
                    }
                    for value in values
                ]
            }

        for name, definition in self.definitions.items():
            if definition.type == TypeSpecType.ENUM:
                enums[name] = {
                    "values": [
                        {
                            "const_name": f"{name}{self._to_pascal_case(value)}",
                            "value": value,
                        }
                        for value in definition.values
                    ]
                }

        return enums

    def _generate_field(self, field: TypeSpecField) -> str:
        """Generate a dataclass field."""
        # Determine the base Python type
        python_type = self._determine_python_type(field)

        # Apply container types (List, Optional) as needed
        if field.is_array:
            python_type = f"List[{python_type}]"
        elif field.is_optional or (
            isinstance(field.type, str) and field.type.endswith("?")
        ):
            python_type = f"Optional[{python_type}]"

        return f"{field.name}: {python_type}"

    def _determine_python_type(self, field: TypeSpecField) -> str:
        """Determine the base Python type for a field."""
        # Use synthetic enum if reference is set
        if field.reference and field.type == "enum":
            return field.reference

        # Check for direct enum reference
        if (
            field.reference
            and field.reference in self.definitions
            and self.definitions[field.reference].type == TypeSpecType.ENUM
        ):
            return field.reference

        # Handle enum member reference like WidgetKind.Heavy
        if (
            field.reference
            and isinstance(field.reference, str)
            and "." in field.reference
        ):
            enum_ref = field.reference.split(".")[0]
            if (
                enum_ref in self.definitions
                and self.definitions[enum_ref].type == TypeSpecType.ENUM
            ):
                return enum_ref
            else:
                return self._map_type(field.type)

        # Check for object reference
        if field.reference and field.type == "object":
            return field.reference

        # Handle union types
        if "|" in field.type:
            return "str"  # Union of string literals

        # Default case - map the base type
        return self._map_type(field.type)

    def _generate_cpp_field(self, field: TypeSpecField) -> str:
        """Generate a C++ struct field."""
        # Determine the base C++ type
        cpp_type = self._determine_cpp_type(field)

        # Apply container types (vector, optional) as needed
        if field.is_array:
            cpp_type = f"std::vector<{cpp_type}>"
        elif field.is_optional:
            cpp_type = f"std::optional<{cpp_type}>"

        return f"{cpp_type} {field.name}"

    def _determine_cpp_type(self, field: TypeSpecField) -> str:
        """Determine the base C++ type for a field."""
        # Use synthetic enum if reference is set
        if field.reference and field.type == "enum":
            return field.reference

        # Check for direct enum reference
        if (
            field.reference
            and field.reference in self.definitions
            and self.definitions[field.reference].type == TypeSpecType.ENUM
        ):
            return field.reference

        # Handle enum member reference like WidgetKind.Heavy
        if (
            field.reference
            and isinstance(field.reference, str)
            and "." in field.reference
        ):
            enum_ref = field.reference.split(".")[0]
            if (
                enum_ref in self.definitions
                and self.definitions[enum_ref].type == TypeSpecType.ENUM
            ):
                return enum_ref
            else:
                return self._map_cpp_type(field.type)

        # Check for object reference
        if field.reference and field.type == "object":
            return field.reference

        # Handle union types
        if "|" in field.type:
            return "std::string"  # Union of string literals

        # Default case - map the base type
        return self._map_cpp_type(field.type)

    def _generate_rust_field(self, field: TypeSpecField) -> str:
        """Generate a Rust struct field."""
        rust_type = self._determine_rust_type(field)
        if field.is_array:
            rust_type = f"Vec<{rust_type}>"
        elif field.is_optional:
            rust_type = f"Option<{rust_type}>"

        return f"pub {self._to_snake_case(field.name)}: {rust_type}"

    def _determine_rust_type(self, field: TypeSpecField) -> str:
        """Determine the base Rust type for a field."""
        if field.reference and field.type == "enum":
            return field.reference

        if (
            field.reference
            and field.reference in self.definitions
            and self.definitions[field.reference].type == TypeSpecType.ENUM
        ):
            return field.reference

        if (
            field.reference
            and isinstance(field.reference, str)
            and "." in field.reference
        ):
            enum_ref = field.reference.split(".")[0]
            if (
                enum_ref in self.definitions
                and self.definitions[enum_ref].type == TypeSpecType.ENUM
            ):
                return enum_ref
            return self._map_rust_type(field.type)

        if field.reference and field.type == "object":
            return field.reference

        if "|" in field.type:
            return "String"

        return self._map_rust_type(field.type)

    def _generate_go_field(self, field: TypeSpecField) -> Dict[str, str]:
        """Generate a Go struct field."""
        go_type = self._determine_go_type(field)
        if field.is_array:
            go_type = f"[]{go_type}"
        elif field.is_optional:
            go_type = f"*{go_type}"

        return {
            "name": self._to_pascal_case(field.name),
            "type": go_type,
            "json_name": field.name,
        }

    def _determine_go_type(self, field: TypeSpecField) -> str:
        """Determine the base Go type for a field."""
        if field.reference and field.type == "enum":
            return field.reference

        if (
            field.reference
            and field.reference in self.definitions
            and self.definitions[field.reference].type == TypeSpecType.ENUM
        ):
            return field.reference

        if (
            field.reference
            and isinstance(field.reference, str)
            and "." in field.reference
        ):
            enum_ref = field.reference.split(".")[0]
            if (
                enum_ref in self.definitions
                and self.definitions[enum_ref].type == TypeSpecType.ENUM
            ):
                return enum_ref
            return self._map_go_type(field.type)

        if field.reference and field.type == "object":
            return field.reference

        if "|" in field.type:
            return "string"

        return self._map_go_type(field.type)

    def _generate_zig_field(self, field: TypeSpecField) -> str:
        """Generate a Zig struct field."""
        zig_type = self._determine_zig_type(field)
        if field.is_array:
            zig_type = f"[]{zig_type}"
        elif field.is_optional:
            zig_type = f"?{zig_type}"

        return f"{self._to_snake_case(field.name)}: {zig_type}"

    def _determine_zig_type(self, field: TypeSpecField) -> str:
        """Determine the base Zig type for a field."""
        if field.reference and field.type == "enum":
            return field.reference

        if (
            field.reference
            and field.reference in self.definitions
            and self.definitions[field.reference].type == TypeSpecType.ENUM
        ):
            return field.reference

        if (
            field.reference
            and isinstance(field.reference, str)
            and "." in field.reference
        ):
            enum_ref = field.reference.split(".")[0]
            if (
                enum_ref in self.definitions
                and self.definitions[enum_ref].type == TypeSpecType.ENUM
            ):
                return enum_ref
            return self._map_zig_type(field.type)

        if field.reference and field.type == "object":
            return field.reference

        if "|" in field.type:
            return "[]const u8"

        return self._map_zig_type(field.type)

    def _generate_vlang_field(self, field: TypeSpecField) -> str:
        """Generate a V struct field."""
        vlang_type = self._determine_vlang_type(field)
        if field.is_array:
            vlang_type = f"[]{vlang_type}"
        elif field.is_optional:
            vlang_type = f"?{vlang_type}"

        return f"{self._to_snake_case(field.name)} {vlang_type}"

    def _determine_vlang_type(self, field: TypeSpecField) -> str:
        """Determine the base V type for a field."""
        if field.reference and field.type == "enum":
            return field.reference

        if (
            field.reference
            and field.reference in self.definitions
            and self.definitions[field.reference].type == TypeSpecType.ENUM
        ):
            return field.reference

        if (
            field.reference
            and isinstance(field.reference, str)
            and "." in field.reference
        ):
            enum_ref = field.reference.split(".")[0]
            if (
                enum_ref in self.definitions
                and self.definitions[enum_ref].type == TypeSpecType.ENUM
            ):
                return enum_ref
            return self._map_vlang_type(field.type)

        if field.reference and field.type == "object":
            return field.reference

        if "|" in field.type:
            return "string"

        return self._map_vlang_type(field.type)

    def _map_cpp_type(self, typespec_type: str) -> str:
        """Map TypeSpec types to C++ types."""
        type_mapping = {
            "string": "std::string",
            "integer": "int",
            "boolean": "bool",
            "object": "void*",  # Placeholder for unknown objects
        }
        return type_mapping.get(typespec_type, "std::string")

    def _map_rust_type(self, typespec_type: str) -> str:
        """Map TypeSpec types to Rust types."""
        type_mapping = {
            "string": "String",
            "integer": "i32",
            "boolean": "bool",
            "object": "String",
        }
        return type_mapping.get(typespec_type, "String")

    def _map_go_type(self, typespec_type: str) -> str:
        """Map TypeSpec types to Go types."""
        type_mapping = {
            "string": "string",
            "integer": "int",
            "boolean": "bool",
            "object": "any",
        }
        return type_mapping.get(typespec_type, "string")

    def _map_zig_type(self, typespec_type: str) -> str:
        """Map TypeSpec types to Zig types."""
        type_mapping = {
            "string": "[]const u8",
            "integer": "i32",
            "boolean": "bool",
            "object": "std.json.Value",
        }
        return type_mapping.get(typespec_type, "[]const u8")

    def _map_vlang_type(self, typespec_type: str) -> str:
        """Map TypeSpec types to V types."""
        type_mapping = {
            "string": "string",
            "integer": "int",
            "boolean": "bool",
            "object": "string",
        }
        return type_mapping.get(typespec_type, "string")

    def _map_type(self, typespec_type: str) -> str:
        """Map TypeSpec types to Python types."""
        type_mapping = {
            "string": "str",
            "integer": "int",
            "boolean": "bool",
            "object": "object",
        }
        return type_mapping.get(typespec_type, "str")
