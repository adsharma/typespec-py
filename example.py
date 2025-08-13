#!/usr/bin/env python3
"""
Example script demonstrating the TypeSpec parser usage.
"""

from typespec_parser import TypeSpecParser

# Example TypeSpec content
typespec_content = """
model Address {
  street: string;
  city: string;
  country: string;
}

model User {
  name: string;
  age: integer;
  email: string?;
  address: Address;
  tags: string[];
  addresses: Address[];
}

enum Status {
  active,
  inactive,
}

model Company {
  name: string;
  status: Status;
  employees: User[];
}
"""


def main():
    """Main function demonstrating the parser usage."""
    print("TypeSpec Parser Example")
    print("======================")

    # Create parser and parse TypeSpec content
    parser = TypeSpecParser()
    definitions = parser.parse(typespec_content)

    # Print parsed definitions
    print("\nParsed Definitions:")
    for name, definition in definitions.items():
        print(f"- {name} ({definition.type.value})")

    # Generate Python dataclasses
    print("\nGenerated Python Dataclasses:")
    print("=" * 40)
    code = parser.generate_dataclasses()
    print(code)

    # Show how to use the generated code
    print("\nExample Usage:")
    print("=" * 40)
    print(
        """
# After saving the generated code to a file, you could use it like this:
#
# address = Address(street="123 Main St", city="Anytown", country="USA")
# user = User(
#     name="John Doe",
#     age=30,
#     email="john@example.com",
#     address=address,
#     tags=["developer", "python"],
#     addresses=[address]
# )
#
# print(user.name)  # John Doe
# print(user.address.city)  # Anytown
"""
    )


if __name__ == "__main__":
    main()
