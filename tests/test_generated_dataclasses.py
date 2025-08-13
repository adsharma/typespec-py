"""Integration test for generated dataclasses."""

import unittest

from typespec_parser.parser import TypeSpecParser


class TestGeneratedDataclasses(unittest.TestCase):
    """Test that generated dataclasses work correctly."""

    def test_generated_dataclasses_functionality(self):
        """Test that generated dataclasses can be instantiated and used."""
        typespec = """
        model Address {
            street: string;
            city: string;
        }

        model User {
            name: string;
            age: integer;
            email: string?;
            address: Address;
            tags: string[];
        }

        enum Status {
            active,
            inactive,
        }
        """

        # Parse and generate dataclasses
        parser = TypeSpecParser()
        parser.parse(typespec)
        code = parser.generate_dataclasses()

        # Execute the generated code in a separate namespace
        namespace = {}
        exec(code, namespace)

        # Import the generated classes from the namespace
        Address = namespace["Address"]
        User = namespace["User"]
        Status = namespace["Status"]

        # Test enum creation
        self.assertEqual(Status.ACTIVE.value, "active")
        self.assertEqual(Status.INACTIVE.value, "inactive")

        # Test dataclass creation
        address = Address(street="123 Main St", city="Anytown")
        user = User(
            name="John Doe",
            age=30,
            email="john@example.com",
            address=address,
            tags=["developer", "python"],
        )

        # Verify attributes
        self.assertEqual(user.name, "John Doe")
        self.assertEqual(user.age, 30)
        self.assertEqual(user.email, "john@example.com")
        self.assertEqual(user.address.street, "123 Main St")
        self.assertEqual(user.tags, ["developer", "python"])

        # Test with optional field as None
        user2 = User(name="Jane Doe", age=25, email=None, address=address, tags=[])

        self.assertIsNone(user2.email)
        self.assertEqual(user2.tags, [])


if __name__ == "__main__":
    unittest.main()
