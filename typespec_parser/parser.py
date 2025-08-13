"""TypeSpec parser that generates Python dataclasses using PEG grammar."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

try:
    import pypeg2 as peg

    PEG_AVAILABLE = True
except ImportError:
    PEG_AVAILABLE = False


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


# PEG Grammar for TypeSpec based on grammar.txt
if PEG_AVAILABLE:

    class Identifier(str):
        """Identifier in TypeSpec."""

        grammar = peg.word

    class TypeExpression(str):
        """Type expression in TypeSpec."""

        grammar = peg.word

    class ModelProperty:
        """Property in a model."""

        grammar = (
            peg.attr("name", [Identifier]),
            peg.optional(peg.flag("?")),
            ":",
            peg.attr("type", TypeExpression),
            peg.ignore(peg.maybe_some(";")),
        )

    class ModelPropertyList(peg.List):
        """List of model properties."""

        grammar = peg.maybe_some(ModelProperty)

    class ModelBody:
        """Body of a model."""

        grammar = "{", peg.optional(peg.attr("properties", ModelPropertyList)), "}"

    class ModelStatement:
        """Model statement in TypeSpec."""

        grammar = (
            peg.Keyword("model"),
            peg.attr("name", Identifier),
            peg.attr("body", ModelBody),
        )

    class EnumMember:
        """Member of an enum."""

        grammar = peg.attr("name", [Identifier]), peg.ignore(peg.maybe_some(";"))

    class EnumMemberList(peg.List):
        """List of enum members."""

        grammar = peg.maybe_some(EnumMember)

    class EnumBody:
        """Body of an enum."""

        grammar = "{", peg.optional(peg.attr("members", EnumMemberList)), "}"

    class EnumStatement:
        """Enum statement in TypeSpec."""

        grammar = (
            peg.Keyword("enum"),
            peg.attr("name", Identifier),
            peg.attr("body", EnumBody),
        )

    class Statement:
        """A statement in TypeSpec."""

        grammar = [ModelStatement, EnumStatement]

    class TypeSpecScriptItemList(peg.List):
        """List of TypeSpec script items."""

        grammar = peg.maybe_some(Statement)

    class TypeSpecScript:
        """Top-level TypeSpec script."""

        grammar = peg.optional(TypeSpecScriptItemList)


class TypeSpecParser:
    """Parses TypeSpec definitions and generates Python dataclasses."""

    def __init__(self):
        self.definitions: Dict[str, TypeSpecDefinition] = {}

    def parse(self, typespec_content: str) -> Dict[str, TypeSpecDefinition]:
        """Parse TypeSpec content and return definitions."""
        # Try to use PEG parser if available
        if PEG_AVAILABLE:
            try:
                return self._parse_with_peg(typespec_content)
            except Exception as e:
                print(f"PEG parsing failed: {e}")
                print("Falling back to line-based parser")

        # Fallback to original line-based parser
        return self._parse_with_lines(typespec_content)

    def _parse_with_peg(self, typespec_content: str) -> Dict[str, TypeSpecDefinition]:
        """Parse TypeSpec content using PEG grammar."""
        # Preprocess the content to remove comments and handle basic formatting
        content = self._preprocess_content(typespec_content)

        # Parse the content using the PEG grammar
        parsed = peg.parse(content, TypeSpecScript)

        # Convert parsed AST to our definitions
        self._convert_ast_to_definitions(parsed)

        return self.definitions

    def _preprocess_content(self, content: str) -> str:
        """Preprocess content to make it suitable for PEG parsing."""
        # Remove single-line comments but preserve strings
        lines = content.split("\n")
        processed_lines = []
        for line in lines:
            # Simple comment removal (this is a basic implementation)
            if "//" in line and '"' not in line and "'" not in line:
                line = line[: line.index("//")]
            if line.strip():
                processed_lines.append(line)
        return " ".join(processed_lines)

    def _convert_ast_to_definitions(self, parsed_script):
        """Convert parsed AST to TypeSpec definitions."""
        self.definitions = {}  # Reset definitions

        if not hasattr(parsed_script, "TypeSpecScriptItemList"):
            return

        for item in parsed_script.TypeSpecScriptItemList:
            if isinstance(item, ModelStatement):
                self._convert_model_statement(item)
            elif isinstance(item, EnumStatement):
                self._convert_enum_statement(item)

    def _convert_model_statement(self, model_stmt):
        """Convert a model statement to a TypeSpec definition."""
        model_name = str(model_stmt.name)
        definition = TypeSpecDefinition(name=model_name, type=TypeSpecType.OBJECT)

        if hasattr(model_stmt, "body") and hasattr(model_stmt.body, "properties"):
            for prop in model_stmt.body.properties:
                field = self._convert_model_property(prop)
                if field:
                    definition.fields.append(field)

        self.definitions[model_name] = definition

    def _convert_model_property(self, prop):
        """Convert a model property to a TypeSpec field."""
        name = str(prop.name)
        is_optional = hasattr(prop, "?") and prop["?"]

        # Extract type information
        type_str = str(prop.type)

        # Check if array
        is_array = type_str.endswith("[]")
        if is_array:
            type_str = type_str[:-2]

        # Handle references
        reference = None
        if type_str in ["string", "integer", "boolean"]:
            field_type = type_str
        elif type_str in self.definitions or (
            type_str[0].isupper() and type_str != "List"
        ):
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

    def _convert_enum_statement(self, enum_stmt):
        """Convert an enum statement to a TypeSpec definition."""
        enum_name = str(enum_stmt.name)
        definition = TypeSpecDefinition(name=enum_name, type=TypeSpecType.ENUM)

        if hasattr(enum_stmt, "body") and hasattr(enum_stmt.body, "members"):
            for member in enum_stmt.body.members:
                value = str(member.name)
                definition.values.append(value)

        self.definitions[enum_name] = definition

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
