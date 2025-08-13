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
statement = model_statement / enum_statement / union_statement
model_statement = decorators? "model" ~r"\s+" identifier ~r"\s*" template_parameters? ~r"\s*" model_heritage? ~r"\s*" "{" ~r"\s*" model_properties? ~r"\s*" "}"
model_heritage = ("extends" ~r"\s+" identifier) / ("is" ~r"\s+" identifier)
model_properties = model_property (comma_or_semicolon model_property)* comma_or_semicolon?
model_property = decorators? identifier optional_marker? ":" ~r"\s*" type_expression
comma_or_semicolon = ~r"[,;]" ~r"\s*"
decorators = decorator+
decorator = "@" identifier decorator_arguments?
decorator_arguments = "(" expression_list? ")"
expression_list = expression ("," ~r"\s*" expression)*
optional_marker = "?"
type_expression = union_expression
union_expression = intersection_expression ("|" ~r"\s*" intersection_expression)*
intersection_expression = array_expression ("&" ~r"\s*" array_expression)*
array_expression = primary_expression ("[" "]" ~r"\s*")*
primary_expression = literal / identifier template_arguments? / parenthesized_expression / object_literal / array_literal / model_expression
template_arguments = "<" template_argument_list ">"
template_argument_list = template_argument ("," ~r"\s*" template_argument)*
template_argument = (identifier "=" ~r"\s*)? expression
template_parameters = "<" template_parameter_list ">"
template_parameter_list = template_parameter ("," ~r"\s*" template_parameter)*
template_parameter = identifier template_parameter_constraint? template_parameter_default?
template_parameter_constraint = "extends" ~r"\s+" identifier
template_parameter_default = "=" ~r"\s*" expression
parenthesized_expression = "(" ~r"\s*" type_expression ~r"\s*" ")"
object_literal = "#{" ~r"\s*" model_properties? ~r"\s*" "}"
array_literal = "#[" ~r"\s*" expression_list? ~r"\s*" "]"
model_expression = "{" ~r"\s*" model_properties? ~r"\s*" "}"
literal = string_literal / boolean_literal / numeric_literal
string_literal = ~r'"[^"]*"'
boolean_literal = "true" / "false"
numeric_literal = ~r"[+-]?[0-9]+(\.[0-9]+)?"
enum_statement = decorators? "enum" ~r"\s+" identifier ~r"\s*" "{" ~r"\s*" enum_members? ~r"\s*" "}"
enum_members = enum_member (comma_or_semicolon enum_member)* comma_or_semicolon?
enum_member = decorators? (identifier enum_member_value?) / (string_literal enum_member_value?)
enum_member_value = ":" ~r"\s*" (string_literal / numeric_literal)
union_statement = decorators? "union" ~r"\s+" identifier ~r"\s*" "{" ~r"\s*" union_members? ~r"\s*" "}"
union_members = union_member (comma_or_semicolon union_member)* comma_or_semicolon?
union_member = decorators? (identifier ":" ~r"\s*" type_expression) / (string_literal ":" ~r"\s*" type_expression) / type_expression
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
        # Handle decorators if present
        idx = 0
        if visited_children[0] is not None:
            idx = 1  # Skip decorators

        # Skip "model" keyword
        idx += 1

        # Get identifier
        identifier_node = visited_children[idx]
        model_name = identifier_node.text

        # Find properties (should be the last non-None child before the closing brace)
        properties_node = None
        for child in reversed(visited_children):
            if (
                child is not None
                and child != []
                and hasattr(child, "text")
                and child.text == "}"
            ):
                break
            if child is not None and child != []:
                properties_node = child
                break

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
        # Handle decorators if present
        idx = 0
        if visited_children[0] is not None:
            idx = 1  # Skip decorators

        identifier_node = visited_children[idx]
        idx += 1

        # Check for optional marker
        is_optional = False
        if visited_children[idx] is not None and visited_children[idx] != []:
            is_optional = True
            idx += 1

        # Skip colon
        idx += 1

        # Get type expression
        type_expr_node = visited_children[idx]
        property_name = identifier_node.text

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
        # For now, just handle simple identifiers
        if isinstance(visited_children[0], list):
            first_child = visited_children[0][0] if visited_children[0] else None
        else:
            first_child = visited_children[0]

        if hasattr(first_child, "text"):
            type_name = first_child.text
        else:
            # Handle literal types like "red" | "blue"
            type_name = "string"

        # Handle references
        reference = None
        if type_name in ["string", "integer", "boolean"]:
            field_type = type_name
        else:
            field_type = "object"
            reference = type_name

        return {
            "type": field_type,
            "is_array": False,
            "is_optional": False,
            "reference": reference,
        }

    def visit_enum_statement(self, node, visited_children):
        """Process an enum statement."""
        # Handle decorators if present
        idx = 0
        if visited_children[0] is not None:
            idx = 1  # Skip decorators

        # Skip "enum" keyword
        idx += 1

        # Get identifier
        identifier_node = visited_children[idx]
        enum_name = identifier_node.text

        # Find members (should be the second to last non-None child before the closing brace)
        members_node = None
        for child in reversed(visited_children):
            if (
                child is not None
                and child != []
                and hasattr(child, "text")
                and child.text == "}"
            ):
                break
            if child is not None and child != []:
                members_node = child
                break

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
        # Handle decorators if present
        idx = 0
        if visited_children[0] is not None:
            idx = 1  # Skip decorators

        # Get identifier or string literal
        member_node = visited_children[idx]
        if hasattr(member_node, "text"):
            return member_node.text
        return str(member_node)

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
