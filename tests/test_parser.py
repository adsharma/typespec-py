"""Tests for the TypeSpec parser."""

import unittest

from typespec_parser.parser import TypeSpecParser, TypeSpecType


class TestTypeSpecParser(unittest.TestCase):
    """Test cases for the TypeSpecParser class."""

    def setUp(self):
        """Set up test fixtures."""
        self.parser = TypeSpecParser()

    def test_parse_enum(self):
        """Test parsing enum definitions."""
        typespec = """
        enum Status {
            active,
            inactive,
        }
        """

        definitions = self.parser.parse(typespec)

        self.assertIn("Status", definitions)
        status_def = definitions["Status"]
        self.assertEqual(status_def.type, TypeSpecType.ENUM)
        self.assertEqual(status_def.values, ["active", "inactive"])

    def test_parse_simple_model(self):
        """Test parsing simple model definitions."""
        typespec = """
        model User {
            name: string;
            age: integer;
            active: boolean;
        }
        """

        definitions = self.parser.parse(typespec)

        self.assertIn("User", definitions)
        user_def = definitions["User"]
        self.assertEqual(user_def.type, TypeSpecType.OBJECT)
        self.assertEqual(len(user_def.fields), 3)

        # Check fields
        name_field = next(f for f in user_def.fields if f.name == "name")
        self.assertEqual(name_field.type, "string")
        self.assertFalse(name_field.is_optional)
        self.assertFalse(name_field.is_array)

        age_field = next(f for f in user_def.fields if f.name == "age")
        self.assertEqual(age_field.type, "integer")
        self.assertFalse(age_field.is_optional)
        self.assertFalse(age_field.is_array)

        active_field = next(f for f in user_def.fields if f.name == "active")
        self.assertEqual(active_field.type, "boolean")
        self.assertFalse(active_field.is_optional)
        self.assertFalse(active_field.is_array)

    def test_parse_model_with_optional_field(self):
        """Test parsing model with optional fields."""
        typespec = """
        model User {
            name: string;
            email: string?;
        }
        """

        definitions = self.parser.parse(typespec)

        user_def = definitions["User"]
        email_field = next(f for f in user_def.fields if f.name == "email")
        self.assertTrue(email_field.is_optional)

    def test_parse_model_with_array_field(self):
        """Test parsing model with array fields."""
        typespec = """
        model User {
            name: string;
            tags: string[];
        }
        """

        definitions = self.parser.parse(typespec)

        user_def = definitions["User"]
        tags_field = next(f for f in user_def.fields if f.name == "tags")
        self.assertTrue(tags_field.is_array)
        self.assertEqual(tags_field.type, "string")

    def test_parse_model_with_reference(self):
        """Test parsing model with references to other models (1:1 relationship)."""
        typespec = """
        model Address {
            street: string;
            city: string;
        }

        model User {
            name: string;
            address: Address;
        }
        """

        definitions = self.parser.parse(typespec)

        # Check Address model
        self.assertIn("Address", definitions)
        address_def = definitions["Address"]
        self.assertEqual(address_def.type, TypeSpecType.OBJECT)
        self.assertEqual(len(address_def.fields), 2)

        # Check User model
        self.assertIn("User", definitions)
        user_def = definitions["User"]
        self.assertEqual(user_def.type, TypeSpecType.OBJECT)
        self.assertEqual(len(user_def.fields), 2)

        # Check reference field
        address_field = next(f for f in user_def.fields if f.name == "address")
        self.assertEqual(address_field.type, "object")
        self.assertEqual(address_field.reference, "Address")
        self.assertFalse(address_field.is_optional)
        self.assertFalse(address_field.is_array)

    def test_parse_model_with_array_of_references(self):
        """Test parsing model with array of references (1:n relationship)."""
        typespec = """
        model Address {
            street: string;
            city: string;
        }

        model User {
            name: string;
            addresses: Address[];
        }
        """

        definitions = self.parser.parse(typespec)

        user_def = definitions["User"]
        addresses_field = next(f for f in user_def.fields if f.name == "addresses")
        self.assertEqual(addresses_field.type, "object")
        self.assertEqual(addresses_field.reference, "Address")
        self.assertTrue(addresses_field.is_array)
        self.assertFalse(addresses_field.is_optional)

    def test_generate_enum(self):
        """Test generating Python enum from TypeSpec enum."""
        typespec = """
        enum Status {
            active,
            inactive,
        }
        """

        self.parser.parse(typespec)
        code = self.parser.generate_python()

        expected = """class Status(Enum):
    ACTIVE = 'active'
    INACTIVE = 'inactive'"""

        self.assertIn(expected, code)

    def test_generate_simple_model(self):
        """Test generating Python dataclass from simple TypeSpec model."""
        typespec = """
        model User {
            name: string;
            age: integer;
        }
        """

        self.parser.parse(typespec)
        code = self.parser.generate_python()

        expected = """@dataclass
class User:
    name: str
    age: int"""

        self.assertIn(expected, code)

    def test_generate_model_with_optional_field(self):
        """Test generating Python dataclass with optional field."""
        typespec = """
        model User {
            name: string;
            email: string?;
        }
        """

        self.parser.parse(typespec)
        code = self.parser.generate_python()

        expected = """@dataclass
class User:
    name: str
    email: Optional[str]"""

        self.assertIn(expected, code)

    def test_generate_model_with_array_field(self):
        """Test generating Python dataclass with array field."""
        typespec = """
        model User {
            name: string;
            tags: string[];
        }
        """

        self.parser.parse(typespec)
        code = self.parser.generate_python()

        expected = """@dataclass
class User:
    name: str
    tags: List[str]"""

        self.assertIn(expected, code)

    def test_generate_model_with_reference(self):
        """Test generating Python dataclasses with 1:1 relationship."""
        typespec = """
        model Address {
            street: string;
            city: string;
        }

        model User {
            name: string;
            address: Address;
        }
        """

        self.parser.parse(typespec)
        code = self.parser.generate_python()

        # Check that both classes are generated
        self.assertIn("@dataclass\nclass Address:", code)
        self.assertIn("@dataclass\nclass User:", code)

        # Check 1:1 relationship
        expected = "address: Address"
        self.assertIn(expected, code)

    def test_generate_model_with_array_of_references(self):
        """Test generating Python dataclasses with 1:n relationship."""
        typespec = """
        model Address {
            street: string;
            city: string;
        }

        model User {
            name: string;
            addresses: Address[];
        }
        """

        self.parser.parse(typespec)
        code = self.parser.generate_python()

        # Check 1:n relationship
        expected = "addresses: List[Address]"
        self.assertIn(expected, code)

    def test_parse_discriminated_union_with_value_object_decorator(self):
        """Test parsing discriminated unions with TypeSpec value object arguments."""
        typespec = """
        // Comments and imports should not prevent parsing declarations.
        import "../common.tsp";

        model BoundAlterInfoPayload {
            alterType: AlterType;
            extraInfo: AlterExtraInfo;
        }

        @discriminated(#{discriminatorPropertyName: "alterType", envelope: "none"})
        union AlterExtraInfo {
            addProperty: AddPropertyAlterPayload,
            dropProperty: DropPropertyAlterPayload,
        }

        model AddPropertyAlterPayload {
            propertyName: string;
        }

        model DropPropertyAlterPayload {
            propertyName: string;
        }
        """

        definitions = self.parser.parse(typespec)

        self.assertIn("AlterExtraInfo", definitions)
        union_def = definitions["AlterExtraInfo"]
        self.assertEqual(union_def.type, TypeSpecType.UNION)
        self.assertEqual(union_def.discriminator_property_name, "alterType")
        self.assertEqual(union_def.envelope, "none")
        self.assertEqual(
            [(field.name, field.reference) for field in union_def.fields],
            [
                ("addProperty", "AddPropertyAlterPayload"),
                ("dropProperty", "DropPropertyAlterPayload"),
            ],
        )

        payload_def = definitions["BoundAlterInfoPayload"]
        extra_info = next(f for f in payload_def.fields if f.name == "extraInfo")
        self.assertEqual(extra_info.reference, "AlterExtraInfo")

    def test_generate_discriminated_union_alias(self):
        """Test generating a Python alias for discriminated unions."""
        typespec = """
        model AddPropertyAlterPayload {
            propertyName: string;
        }

        model DropPropertyAlterPayload {
            propertyName: string;
        }

        @discriminated(#{discriminatorPropertyName: "alterType", envelope: "none"})
        union AlterExtraInfo {
            addProperty: AddPropertyAlterPayload,
            dropProperty: DropPropertyAlterPayload,
        }

        model BoundAlterInfoPayload {
            extraInfo: AlterExtraInfo;
        }
        """

        self.parser.parse(typespec)
        code = self.parser.generate_python()

        self.assertIn(
            "AlterExtraInfo = Union[AddPropertyAlterPayload, DropPropertyAlterPayload]",
            code,
        )
        self.assertIn("extraInfo: AlterExtraInfo", code)

    def test_parse_general_decorators(self):
        """Test parsing decorators on definitions and members."""
        typespec = """
        @doc("A user")
        model User {
            @key
            @format("uuid")
            id: string;
        }

        @doc("Status enum")
        enum Status {
            @doc("Enabled")
            active,
            inactive,
        }

        model Circle {
            radius: integer;
        }

        model Square {
            side: integer;
        }

        @doc("Shape union")
        union Shape {
            @doc("Circle variant")
            circle: Circle,
            square: Square,
        }
        """

        definitions = self.parser.parse(typespec)

        user_def = definitions["User"]
        self.assertEqual(user_def.decorators, ["doc"])
        self.assertEqual(user_def.decorator_arguments, {"doc": '"A user"'})
        id_field = user_def.fields[0]
        self.assertEqual(id_field.decorators, ["key", "format"])
        self.assertEqual(id_field.decorator_arguments, {"format": '"uuid"'})

        status_def = definitions["Status"]
        self.assertEqual(status_def.decorators, ["doc"])
        self.assertEqual(status_def.decorator_arguments, {"doc": '"Status enum"'})
        self.assertEqual(status_def.value_decorators, {"active": ["doc"]})
        self.assertEqual(
            status_def.value_decorator_arguments,
            {"active": {"doc": '"Enabled"'}},
        )

        shape_def = definitions["Shape"]
        self.assertEqual(shape_def.decorators, ["doc"])
        self.assertEqual(shape_def.decorator_arguments, {"doc": '"Shape union"'})
        self.assertEqual(shape_def.fields[0].decorators, ["doc"])
        self.assertEqual(
            shape_def.fields[0].decorator_arguments,
            {"doc": '"Circle variant"'},
        )
        self.assertEqual(shape_def.fields[1].decorators, [])


if __name__ == "__main__":
    unittest.main()
