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


# TypeSpec grammar for parsimonious - based on official grammar
TYPESPEC_GRAMMAR = r"""
typespec_script = ws statement_list? ws
statement_list = statement (ws statement)*
statement = model_statement / enum_statement / union_statement / operation_statement / empty_statement
empty_statement = ";"
model_statement = decorator_list? "model" ws identifier ws template_parameters? ws model_heritage? ws "{" ws model_body? ws "}"
model_heritage = is_model_heritage / extends_model_heritage
is_model_heritage = "is" ws expression
extends_model_heritage = "extends" ws expression
model_body = model_property_list
model_property_list = model_property (ws comma_or_semicolon ws model_property)* (ws comma_or_semicolon)?
model_property = model_spread_property /
    (decorator_list? identifier ws optional_marker? ws ":" ws expression) /
    (decorator_list? string_literal ws optional_marker? ws ":" ws expression)
model_spread_property = "..." ws reference_expression
comma_or_semicolon = ~r"[,;]"
decorator_list = decorator (ws decorator)*
decorator = "@" ws identifier_or_member_expression ws decorator_arguments?
decorator_arguments = "(" ws complex_expression? ws ")"
complex_expression = object_literal / array_literal / expression_list / expression
expression_list = expression (ws "," ws expression)*
expression = union_expression_or_higher
union_expression_or_higher = intersection_expression_or_higher (ws "|" ws intersection_expression_or_higher)*
intersection_expression_or_higher = array_expression_or_higher (ws "&" ws array_expression_or_higher)*
array_expression_or_higher = primary_expression (ws "[" ws "]")*
primary_expression = literal / call_or_reference_expression / parenthesized_expression /
    object_literal / array_literal / model_expression / tuple_expression
call_or_reference_expression = call_expression / reference_expression
call_expression = identifier_or_member_expression ws call_arguments
call_arguments = "(" ws expression_list? ws ")"
reference_expression = identifier_or_member_expression ws template_arguments?
identifier_or_member_expression = identifier (ws "." ws identifier)*
template_arguments = "<" ws template_argument_list ws ">"
template_argument_list = template_argument (ws "," ws template_argument)*
template_argument = expression / (identifier ws "=" ws expression)
template_parameters = "<" ws template_parameter_list ws ">"
template_parameter_list = template_parameter (ws "," ws template_parameter)*
template_parameter = identifier ws template_parameter_constraint? ws template_parameter_default?
template_parameter_constraint = "extends" ws expression
template_parameter_default = "=" ws expression
parenthesized_expression = "(" ws expression ws ")"
object_literal = "{" ws object_literal_body? ws "}"
object_literal_body = object_property_list
object_property_list = object_property (ws comma_or_semicolon ws object_property)* (ws comma_or_semicolon)?
object_property = object_spread_property / (identifier ws ":" ws expression) / (string_literal ws ":" ws expression)
object_spread_property = "..." ws reference_expression
array_literal = "#[" ws expression_list? ws "]"
model_expression = "{" ws model_body? ws "}"
tuple_expression = "[" ws expression_list? ws "]"
literal = string_literal / boolean_literal / numeric_literal
string_literal = ~r'"[^"]*"'
boolean_literal = "true" / "false"
numeric_literal = ~r"[+-]?[0-9]+(\.[0-9]+)?"
optional_marker = ~r"\?"
enum_statement = decorator_list? "enum" ws identifier ws "{" ws enum_body? ws "}"
enum_body = enum_member_list
enum_member_list = enum_member (ws comma_or_semicolon ws enum_member)* (ws comma_or_semicolon)?
enum_member = enum_spread_member / (decorator_list? identifier ws enum_member_value?) /
              (decorator_list? string_literal ws enum_member_value?)
enum_spread_member = "..." ws reference_expression
enum_member_value = ":" ws (string_literal / numeric_literal)
union_statement = decorator_list? "union" ws identifier ws template_parameters? ws "{" ws union_body? ws "}"
union_body = union_variant_list
union_variant_list = union_variant (ws comma_or_semicolon ws union_variant)* (ws comma_or_semicolon)?
union_variant = (decorator_list? identifier ws ":" ws expression) /
    (decorator_list? string_literal ws ":" ws expression) /
    (decorator_list? expression)
operation_statement = decorator_list? "op" ws identifier ws template_parameters? ws operation_signature ws ";"
operation_signature = operation_signature_declaration / operation_signature_reference
operation_signature_declaration = "(" ws operation_parameter_list? ws ")" ws ":" ws expression
operation_signature_reference = "is" ws reference_expression
operation_parameter_list = operation_parameter (ws comma_or_semicolon ws operation_parameter)*
operation_parameter = decorator_list? identifier ws ":" ws expression
identifier = ~r"[a-zA-Z_][a-zA-Z0-9_]*"
ws = ~r"\s*"
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
        # Find the model name from the identifier nodes
        model_name = None
        for child in visited_children:
            if (
                hasattr(child, "text")
                and hasattr(child, "expr_name")
                and child.expr_name == "identifier"
            ):
                model_name = child.text
                break

        if not model_name:
            # Fallback - extract from node text
            text = node.text.strip()
            if text.startswith("model "):
                parts = text.split()
                if len(parts) > 1:
                    model_name = parts[1].split("{")[0].strip()

        if not model_name:
            model_name = "Unknown"

        # Find properties from the visited children
        properties = []
        for child in visited_children:
            if isinstance(child, TypeSpecField):
                properties.append(child)
            elif isinstance(child, list):
                # Handle nested lists
                for subitem in child:
                    if isinstance(subitem, TypeSpecField):
                        properties.append(subitem)

        # Create definition
        definition = TypeSpecDefinition(name=model_name, type=TypeSpecType.OBJECT)
        definition.fields = properties

        self.definitions[model_name] = definition
        return definition

    def visit_model_property(self, node, visited_children):
        """Process a model property."""
        # The grammar structure shows model_property has one child with the full content
        if len(visited_children) == 1 and visited_children[0] is not None:
            # Let's parse this manually from the node text
            text = node.text.strip()

            # Simple parsing: find identifier, optional marker, and type
            parts = text.split(":")
            if len(parts) >= 2:
                left_part = parts[0].strip()
                right_part = parts[1].strip().rstrip(";")

                # Check for optional marker
                is_optional = left_part.endswith("?")
                if is_optional:
                    left_part = left_part[:-1].strip()

                # Extract property name (skip decorators for now)
                property_name = left_part.split()[-1] if left_part else "unknown"

                # Extract type
                field_type = right_part if right_part else "string"

                # Check for array syntax
                is_array = field_type.endswith("[]")
                if is_array:
                    field_type = field_type[:-2]

                # Handle reference types
                reference = None
                if field_type not in [
                    "string",
                    "integer",
                    "int32",
                    "boolean",
                    "number",
                ]:
                    reference = field_type
                    field_type = "object"

                return TypeSpecField(
                    name=property_name,
                    type=field_type,
                    is_optional=is_optional,
                    is_array=is_array,
                    reference=reference,
                )

        return None

    def visit_type_expression(self, node, visited_children):
        """Process a type expression."""
        # For now, just handle simple identifiers
        if isinstance(visited_children[0], list):
            first_child = visited_children[0][0] if visited_children[0] else None
        else:
            first_child = visited_children[0]

        if first_child and hasattr(first_child, "text"):
            type_name = first_child.text
        else:
            # Handle literal types like "red" | "blue" or fallback
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
        # Find the enum name from the identifier nodes
        enum_name = None
        for child in visited_children:
            if (
                hasattr(child, "text")
                and hasattr(child, "expr_name")
                and child.expr_name == "identifier"
            ):
                enum_name = child.text
                break

        if not enum_name:
            # Fallback - extract from node text
            text = node.text.strip()
            if text.startswith("enum "):
                parts = text.split()
                if len(parts) > 1:
                    enum_name = parts[1].split("{")[0].strip()

        if not enum_name:
            enum_name = "Unknown"

        # Find members from the visited children
        members = []
        for child in visited_children:
            if isinstance(child, str) and child.strip():
                members.append(child.strip())
            elif isinstance(child, list):
                # Handle nested lists
                for subitem in child:
                    if isinstance(subitem, str) and subitem.strip():
                        members.append(subitem.strip())

        # Create definition
        definition = TypeSpecDefinition(name=enum_name, type=TypeSpecType.ENUM)
        definition.values = members

        self.definitions[enum_name] = definition
        return definition

    def visit_empty_statement(self, node, visited_children):
        """Process empty statement."""
        return None

    def visit_model_body(self, node, visited_children):
        """Process model body."""
        # Return the first child which should be the property list
        return visited_children[0] if visited_children else []

    def visit_model_property_list(self, node, visited_children):
        """Process model property list."""
        # Collect all the properties
        properties = []
        for child in visited_children:
            if isinstance(child, TypeSpecField):
                properties.append(child)
            elif isinstance(child, list):
                # Handle nested lists
                for subitem in child:
                    if isinstance(subitem, TypeSpecField):
                        properties.append(subitem)
        return properties

    def visit_enum_body(self, node, visited_children):
        """Process enum body."""
        # Return the first child which should be the member list
        return visited_children[0] if visited_children else []

    def visit_enum_member_list(self, node, visited_children):
        """Process enum member list."""
        # Collect all the members
        members = []
        for child in visited_children:
            if isinstance(child, str) and child.strip():
                members.append(child.strip())
            elif isinstance(child, list):
                # Handle nested lists
                for subitem in child:
                    if isinstance(subitem, str) and subitem.strip():
                        members.append(subitem.strip())
        return members

    def visit_enum_member(self, node, visited_children):
        """Process an enum member."""
        # Simple approach: extract from node text
        text = node.text.strip()

        # Remove any trailing comma or semicolon
        text = text.rstrip(",;")

        # For now, just return the identifier (ignoring decorators and values)
        if ":" in text:
            # Has a value, take the part before the colon
            text = text.split(":")[0].strip()

        # Remove quotes if present
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1]

        return text

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
