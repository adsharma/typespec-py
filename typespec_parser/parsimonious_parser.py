"""TypeSpec parser using parsimonious library."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor


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


# Simplified TypeSpec grammar for parsimonious
TYPESPEC_GRAMMAR = r"""
typespec_script = statement+
statement = model_statement / enum_statement
model_statement = "model" ~r"\s+" identifier ~r"\s*" "{" ~r"\s*" model_properties? ~r"\s*" "}"
model_properties = model_property (comma_or_semicolon model_property)* comma_or_semicolon?
model_property = identifier optional_marker? ":" ~r"\s*" type_expression
comma_or_semicolon = ~r"[,;]" ~r"\s*"
optional_marker = "?"
type_expression = identifier type_suffix?
type_suffix = ("[]") / ("?" ~r"\s*") / ("[]" "?" ~r"\s*")
enum_statement = "enum" ~r"\s+" identifier ~r"\s*" "{" ~r"\s*" enum_members? ~r"\s*" "}"
enum_members = enum_member (comma_or_semicolon enum_member)* comma_or_semicolon?
enum_member = identifier
identifier = ~r"[a-zA-Z_][a-zA-Z0-9_]*"
"""


class TypeSpecVisitor(NodeVisitor):
    """Visitor for the TypeSpec AST."""

    def __init__(self):
        self.definitions: Dict[str, TypeSpecDefinition] = {}

    def visit_typespec_script(self, node, visited_children):
        """Process the entire TypeSpec script."""
        return self.definitions

    def visit_model_statement(self, node, visited_children):
        """Process a model statement."""
        _, _, _, identifier_node, _, _, _, _, properties_node, _, _, _ = (
            visited_children
        )
        model_name = identifier_node.text

        # Create definition
        definition = TypeSpecDefinition(name=model_name, type=TypeSpecType.OBJECT)

        # Process the properties if they exist
        if properties_node is not None and properties_node != []:
            # Handle property list
            if isinstance(properties_node, list) and len(properties_node) > 0:
                for item in properties_node:
                    if isinstance(item, TypeSpecField):
                        definition.fields.append(item)
                    elif isinstance(item, list):
                        # Handle nested lists
                        for subitem in item:
                            if isinstance(subitem, TypeSpecField):
                                definition.fields.append(subitem)
            elif isinstance(properties_node, TypeSpecField):
                # Single property
                definition.fields.append(properties_node)

        self.definitions[model_name] = definition
        return definition

    def visit_model_property(self, node, visited_children):
        """Process a model property."""
        identifier_node, optional_marker_node, _, _, type_expr_node = visited_children
        property_name = identifier_node.text

        # Handle optional marker
        is_optional = optional_marker_node is not None and optional_marker_node != []

        # Handle type expression
        type_info = type_expr_node
        if isinstance(type_info, dict):
            field_type = type_info.get("type", "string")
            is_array = type_info.get("is_array", False)
            reference = type_info.get("reference")
        else:
            field_type = "string"
            is_array = False
            reference = None

        return TypeSpecField(
            name=property_name,
            type=field_type,
            is_optional=is_optional,
            is_array=is_array,
            reference=reference,
        )

    def visit_type_expression(self, node, visited_children):
        """Process a type expression."""
        identifier_node = visited_children[0]
        type_name = identifier_node.text

        # Handle suffix if present
        is_array = False
        is_optional = False

        if len(visited_children) > 1 and visited_children[1] is not None:
            suffix_node = visited_children[1]
            # Check suffix text
            suffix_text = ""
            if hasattr(suffix_node, "text"):
                suffix_text = suffix_node.text
            elif isinstance(suffix_node, list):
                for item in suffix_node:
                    if hasattr(item, "text"):
                        suffix_text += item.text

            is_array = "[]" in suffix_text
            is_optional = (
                "?" in suffix_text and not is_array
            )  # Only mark as optional if not array

        # Handle references
        reference = None
        if type_name in ["string", "integer", "boolean"]:
            field_type = type_name
        else:
            field_type = "object"
            reference = type_name

        return {
            "type": field_type,
            "is_array": is_array,
            "is_optional": is_optional,
            "reference": reference,
        }

    def visit_enum_statement(self, node, visited_children):
        """Process an enum statement."""
        _, _, _, identifier_node, _, _, _, _, members_node, _, _, _ = visited_children
        enum_name = identifier_node.text

        # Create definition
        definition = TypeSpecDefinition(name=enum_name, type=TypeSpecType.ENUM)

        # Process members if they exist
        if members_node is not None and members_node != []:
            # Handle member list
            if isinstance(members_node, list) and len(members_node) > 0:
                for item in members_node:
                    if isinstance(item, str):
                        definition.values.append(item)
                    elif isinstance(item, list):
                        # Handle nested lists
                        for subitem in item:
                            if isinstance(subitem, str):
                                definition.values.append(subitem)
            elif isinstance(members_node, str):
                # Single member
                definition.values.append(members_node)

        self.definitions[enum_name] = definition
        return definition

    def visit_enum_member(self, node, visited_children):
        """Process an enum member."""
        identifier_node = visited_children[0]
        return identifier_node.text

    def visit_identifier(self, node, visited_children):
        """Process an identifier."""
        return node

    def generic_visit(self, node, visited_children):
        """Generic visitor that returns the first non-None child."""
        for child in visited_children:
            if child is not None and child != []:
                return child
        return None


def parse_typespec(content: str) -> Dict[str, TypeSpecDefinition]:
    """Parse TypeSpec content using parsimonious grammar."""
    grammar = Grammar(TYPESPEC_GRAMMAR)
    tree = grammar.parse(content)
    visitor = TypeSpecVisitor()
    visitor.visit(tree)
    return visitor.definitions
