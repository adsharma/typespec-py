"""TypeSpec parser that generates Python dataclasses."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


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

    def __init__(self):
        self.definitions: Dict[str, TypeSpecDefinition] = {}

    def parse(self, typespec_content: str) -> Dict[str, TypeSpecDefinition]:
        """Parse TypeSpec content and return definitions."""
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
        # Extract model name
        model_line = lines[start_index].strip()
        model_name = model_line.split(" ")[1].split("{")[0]

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

            # Parse field
            field = self._parse_field(line)
            if field:
                definition.fields.append(field)

            i += 1

        self.definitions[model_name] = definition
        return i + 1  # Skip closing brace

    def _parse_enum(self, lines: List[str], start_index: int) -> int:
        """Parse an enum definition."""
        # Extract enum name
        enum_line = lines[start_index].strip()
        enum_name = enum_line.split(" ")[1].split("{")[0]

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

            # Extract enum value
            value = line.split(",")[0]  # Remove trailing comma if present
            if value:
                definition.values.append(value)

            i += 1

        self.definitions[enum_name] = definition
        return i + 1  # Skip closing brace

    def _parse_field(self, line: str) -> Optional[TypeSpecField]:
        """Parse a field definition."""
        # Remove trailing semicolon or comma
        line = line.rstrip(";,")

        # Check if optional (marked with ?)
        is_optional = "?" in line
        line = line.replace("?", "")

        # Split into name and type
        if ":" not in line:
            return None

        name, type_str = line.split(":", 1)
        name = name.strip()
        type_str = type_str.strip()

        # Check if array (marked with [])
        is_array = type_str.endswith("[]")
        if is_array:
            type_str = type_str[:-2]  # Remove []

        # Handle references to other models
        reference = None
        if type_str in ["string", "integer", "boolean"]:
            field_type = type_str
        elif type_str in self.definitions:
            field_type = "object"
            reference = type_str
        else:
            # Default to string for unknown types
            field_type = "string"

        return TypeSpecField(
            name=name,
            type=field_type,
            is_optional=is_optional,
            is_array=is_array,
            reference=reference,
        )

    def generate_dataclasses(self) -> str:
        """Generate Python dataclasses from parsed definitions."""
        if not self.definitions:
            return ""

        result = [
            "from dataclasses import dataclass",
            "from typing import List, Optional",
            "from enum import Enum",
            "",
            "",
        ]

        # Generate enums first
        for name, definition in self.definitions.items():
            if definition.type == TypeSpecType.ENUM:
                result.append(self._generate_enum(definition))
                result.append("")

        # Generate classes
        for name, definition in self.definitions.items():
            if definition.type == TypeSpecType.OBJECT:
                result.append(self._generate_dataclass(definition))
                result.append("")

        return "\n".join(result)

    def _generate_enum(self, definition: TypeSpecDefinition) -> str:
        """Generate a Python enum."""
        lines = [f"class {definition.name}(Enum):"]

        if not definition.values:
            lines.append("    pass")
        else:
            for value in definition.values:
                # Convert to valid Python enum format
                enum_value = value.upper().replace("-", "_").replace(" ", "_")
                lines.append(f"    {enum_value} = '{value}'")

        return "\n".join(lines)

    def _generate_dataclass(self, definition: TypeSpecDefinition) -> str:
        """Generate a Python dataclass."""
        lines = ["@dataclass", f"class {definition.name}:"]

        if not definition.fields:
            lines.append("    pass")
        else:
            for field_name in definition.fields:
                lines.append(f"    {self._generate_field(field_name)}")

        return "\n".join(lines)

    def _generate_field(self, field: TypeSpecField) -> str:
        """Generate a dataclass field."""
        # Determine Python type
        if field.is_array:
            if field.reference:
                python_type = f"List[{field.reference}]"
            else:
                python_type = f"List[{self._map_type(field.type)}]"
        elif field.is_optional:
            if field.reference:
                python_type = f"Optional[{field.reference}]"
            else:
                python_type = f"Optional[{self._map_type(field.type)}]"
        else:
            if field.reference:
                python_type = field.reference
            else:
                python_type = self._map_type(field.type)

        return f"{field.name}: {python_type}"

    def _map_type(self, typespec_type: str) -> str:
        """Map TypeSpec types to Python types."""
        type_mapping = {
            "string": "str",
            "integer": "int",
            "boolean": "bool",
            "object": "object",
        }
        return type_mapping.get(typespec_type, "str")
