"""TypeSpec parser that generates Python dataclasses using parsimonious."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

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

    def __init__(self):
        self.definitions: Dict[str, TypeSpecDefinition] = {}

    @staticmethod
    def _normalize_enum_member(value: str) -> str:
        """Convert enum member name to uppercase Python enum format."""
        return value.upper().replace("-", "_").replace(" ", "_")

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
        # Parse the content using our parsimonious parser
        parsimonious_definitions = parsimonious_parse(typespec_content)

        # Convert parsimonious definitions to our format
        self.definitions = {}
        for name, parsimonious_def in parsimonious_definitions.items():
            # Convert the definition type
            if parsimonious_def.type.name == "ENUM":
                definition_type = TypeSpecType.ENUM
            else:
                definition_type = TypeSpecType.OBJECT

            # Create our definition
            definition = TypeSpecDefinition(
                name=name, type=definition_type, fields=[], values=[]
            )

            # Copy fields or values
            if parsimonious_def.type.name == "ENUM":
                definition.values = parsimonious_def.values
            else:
                definition.fields = parsimonious_def.fields

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
                enum_value = self._normalize_enum_member(value)
                lines.append(f"    {enum_value} = '{value}'")

        return "\n".join(lines)

    def _generate_dataclass(self, definition: TypeSpecDefinition) -> str:
        """Generate a Python dataclass."""
        lines = ["@dataclass", f"class {definition.name}:"]

        if not definition.fields:
            lines.append("    pass")
        else:
            for field_obj in definition.fields:
                lines.append(f"    {self._generate_field(field_obj)}")

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
