"""PEG parser for TypeSpec grammar based on grammar.txt."""

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


class PEGParser:
    """Simple PEG parser for TypeSpec grammar."""

    def __init__(self, text: str):
        self.text = text
        self.pos = 0

    def parse_typespec_script(self) -> Dict[str, TypeSpecDefinition]:
        """Parse a TypeSpec script."""
        definitions = {}
        max_iterations = 1000  # Prevent infinite loops
        iterations = 0

        while self.pos < len(self.text) and iterations < max_iterations:
            iterations += 1
            self._skip_whitespace()

            # Check if we've reached the end
            if self.pos >= len(self.text):
                break

            # Parse model or enum statements
            if self._match_keyword("model"):
                try:
                    model_def = self._parse_model_statement()
                    definitions[model_def.name] = model_def
                except Exception:
                    # Skip invalid model definition
                    self._skip_to_next_statement()
            elif self._match_keyword("enum"):
                try:
                    enum_def = self._parse_enum_statement()
                    definitions[enum_def.name] = enum_def
                except Exception:
                    # Skip invalid enum definition
                    self._skip_to_next_statement()
            else:
                # Skip any other content
                self.pos += 1

        return definitions

    def _skip_to_next_statement(self):
        """Skip to the next statement (model or enum)."""
        while self.pos < len(self.text):
            if (
                self.text[self.pos : self.pos + 5] == "model"
                or self.text[self.pos : self.pos + 4] == "enum"
                or self.pos >= len(self.text) - 1
            ):
                break
            self.pos += 1

    def _skip_whitespace(self):
        """Skip whitespace and comments."""
        while self.pos < len(self.text):
            if self.text[self.pos].isspace():
                self.pos += 1
            elif (
                self.pos + 1 < len(self.text)
                and self.text[self.pos : self.pos + 2] == "//"
            ):
                # Skip single-line comment
                while self.pos < len(self.text) and self.text[self.pos] != "\n":
                    self.pos += 1
            elif (
                self.pos + 1 < len(self.text)
                and self.text[self.pos : self.pos + 2] == "/*"
            ):
                # Skip multi-line comment
                while self.pos < len(self.text) - 1:
                    if self.text[self.pos : self.pos + 2] == "*/":
                        self.pos += 2
                        break
                    self.pos += 1
            else:
                break

    def _match_keyword(self, keyword: str) -> bool:
        """Match a keyword."""
        self._skip_whitespace()
        if (
            self.pos + len(keyword) <= len(self.text)
            and self.text[self.pos : self.pos + len(keyword)] == keyword
        ):
            # Check that it's followed by a non-identifier character
            if (
                self.pos + len(keyword) >= len(self.text)
                or not self.text[self.pos + len(keyword)].isalnum()
            ):
                self.pos += len(keyword)
                return True
        return False

    def _match_string(self, string: str) -> bool:
        """Match a string."""
        if (
            self.pos + len(string) <= len(self.text)
            and self.text[self.pos : self.pos + len(string)] == string
        ):
            self.pos += len(string)
            return True
        return False

    def _parse_identifier(self) -> str:
        """Parse an identifier."""
        self._skip_whitespace()
        start = self.pos

        # First character must be a letter or underscore
        if self.pos < len(self.text) and (
            self.text[self.pos].isalpha() or self.text[self.pos] == "_"
        ):
            self.pos += 1
            # Subsequent characters can be letters, digits, or underscores
            while self.pos < len(self.text) and (
                self.text[self.pos].isalnum() or self.text[self.pos] == "_"
            ):
                self.pos += 1
            return self.text[start : self.pos]

        return ""  # Return empty string if no identifier found

    def _parse_model_statement(self) -> TypeSpecDefinition:
        """Parse a model statement."""
        name = self._parse_identifier()
        if not name:
            raise ValueError("Expected model name")

        # Skip until {
        while self.pos < len(self.text) and self.text[self.pos] != "{":
            self.pos += 1

        if self.pos >= len(self.text) or self.text[self.pos] != "{":
            raise ValueError("Expected '{' in model statement")

        self.pos += 1  # Skip {

        definition = TypeSpecDefinition(name=name, type=TypeSpecType.OBJECT)

        # Parse model body
        while self.pos < len(self.text) and self.text[self.pos] != "}":
            self._skip_whitespace()

            if self.pos >= len(self.text) or self.text[self.pos] == "}":
                break

            # Try to parse model property
            field = self._parse_model_property()
            if field and field.name:
                definition.fields.append(field)

        # Skip }
        if self.pos < len(self.text) and self.text[self.pos] == "}":
            self.pos += 1

        return definition

    def _parse_model_property(self) -> Optional[TypeSpecField]:
        """Parse a model property."""
        self._skip_whitespace()

        if self.pos >= len(self.text) or self.text[self.pos] == "}":
            return None

        # Parse property name (identifier or string literal)
        name = ""
        if self.text[self.pos] == '"':
            # String literal
            self.pos += 1  # Skip opening quote
            start = self.pos
            while self.pos < len(self.text) and self.text[self.pos] != '"':
                self.pos += 1
            name = self.text[start : self.pos]
            if self.pos < len(self.text):
                self.pos += 1  # Skip closing quote
        else:
            # Identifier
            name = self._parse_identifier()

        if not name:
            # Skip to next property
            while (
                self.pos < len(self.text)
                and self.text[self.pos] not in ";,"
                and self.text[self.pos] != "}"
            ):
                self.pos += 1
            if self.pos < len(self.text) and self.text[self.pos] in ";,":
                self.pos += 1
            return None

        # Skip until :
        while self.pos < len(self.text) and self.text[self.pos] != ":":
            self.pos += 1

        if self.pos >= len(self.text) or self.text[self.pos] != ":":
            # Skip to next property
            while (
                self.pos < len(self.text)
                and self.text[self.pos] not in ";,"
                and self.text[self.pos] != "}"
            ):
                self.pos += 1
            if self.pos < len(self.text) and self.text[self.pos] in ";,":
                self.pos += 1
            return TypeSpecField(name=name, type="string")  # Default fallback

        self.pos += 1  # Skip :

        # Parse type
        type_info = self._parse_type_expression()

        # Skip trailing semicolon or comma
        if self.pos < len(self.text) and self.text[self.pos] in ";,":
            self.pos += 1

        return TypeSpecField(
            name=name,
            type=type_info["type"],
            is_optional=type_info["is_optional"],
            is_array=type_info["is_array"],
            reference=type_info["reference"],
        )

    def _parse_type_expression(self) -> Dict:
        """Parse a type expression."""
        self._skip_whitespace()

        # Check for optional marker at the end of the type
        is_optional = False

        # Parse identifier (type name)
        type_name = self._parse_identifier()

        if not type_name:
            return {
                "type": "string",
                "is_array": False,
                "is_optional": False,
                "reference": None,
            }  # Default fallback

        # Check if it's an array
        is_array = False
        if self.pos + 1 < len(self.text) and self.text[self.pos : self.pos + 2] == "[]":
            is_array = True
            self.pos += 2

        # Check for optional marker at the end of the type
        if self.pos < len(self.text) and self.text[self.pos] == "?":
            is_optional = True
            self.pos += 1

        # Handle references
        reference = None
        if type_name in ["string", "integer", "boolean"]:
            field_type = type_name
        elif (
            type_name and type_name[0].isupper()
        ):  # Capitalized identifiers are likely references
            field_type = "object"
            reference = type_name
        else:
            field_type = "string"  # Default

        return {
            "type": field_type,
            "is_array": is_array,
            "is_optional": is_optional,
            "reference": reference,
        }

    def _parse_enum_statement(self) -> TypeSpecDefinition:
        """Parse an enum statement."""
        name = self._parse_identifier()
        if not name:
            raise ValueError("Expected enum name")

        # Skip until {
        while self.pos < len(self.text) and self.text[self.pos] != "{":
            self.pos += 1

        if self.pos >= len(self.text) or self.text[self.pos] != "{":
            raise ValueError("Expected '{' in enum statement")

        self.pos += 1  # Skip {

        definition = TypeSpecDefinition(name=name, type=TypeSpecType.ENUM)

        # Parse enum body
        while self.pos < len(self.text) and self.text[self.pos] != "}":
            self._skip_whitespace()

            if self.pos >= len(self.text) or self.text[self.pos] == "}":
                break

            # Try to parse enum member
            member = self._parse_enum_member()
            if member:
                definition.values.append(member)

        # Skip }
        if self.pos < len(self.text) and self.text[self.pos] == "}":
            self.pos += 1

        return definition

    def _parse_enum_member(self) -> Optional[str]:
        """Parse an enum member."""
        self._skip_whitespace()

        if self.pos >= len(self.text) or self.text[self.pos] == "}":
            return None

        # Parse member name (identifier or string literal)
        name = ""
        if self.text[self.pos] == '"':
            # String literal
            self.pos += 1  # Skip opening quote
            start = self.pos
            while self.pos < len(self.text) and self.text[self.pos] != '"':
                self.pos += 1
            name = self.text[start : self.pos]
            if self.pos < len(self.text):
                self.pos += 1  # Skip closing quote
        else:
            # Identifier
            name = self._parse_identifier()

        if not name:
            return None

        # Skip optional value assignment
        if self.pos < len(self.text) and self.text[self.pos] == ":":
            # Skip until , } or end
            while (
                self.pos < len(self.text)
                and self.text[self.pos] not in ",}"
                and self.text[self.pos] != "\n"
            ):
                self.pos += 1

        # Skip trailing semicolon or comma
        if self.pos < len(self.text) and self.text[self.pos] in ";,":
            self.pos += 1

        return name


def parse_typespec(content: str) -> Dict[str, TypeSpecDefinition]:
    """Parse TypeSpec content using PEG grammar."""
    parser = PEGParser(content)
    return parser.parse_typespec_script()
