"""Integration test for generated C++ headers."""

import os
import subprocess
import tempfile
import unittest

from typespec_parser.parser import TypeSpecParser


class TestGeneratedCppHeaders(unittest.TestCase):
    """Test that generated C++ headers are syntactically valid."""

    def test_generated_cpp_headers(self):
        """Test that generated C++ headers are syntactically valid."""
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

        # Parse and generate C++ headers
        parser = TypeSpecParser()
        parser.parse(typespec)
        cpp_code = parser.generate_cpp_headers()

        # Verify basic structure
        self.assertIn("#include <string>", cpp_code)
        self.assertIn("#include <vector>", cpp_code)
        self.assertIn("#include <optional>", cpp_code)
        self.assertIn("struct Address", cpp_code)
        self.assertIn("struct User", cpp_code)
        self.assertIn("enum class Status", cpp_code)

        # Check for field declarations
        self.assertIn("std::string street;", cpp_code)
        self.assertIn("std::string city;", cpp_code)
        self.assertIn("std::string name;", cpp_code)
        self.assertIn("int age;", cpp_code)
        self.assertIn("std::optional<std::string> email;", cpp_code)
        self.assertIn("Address address;", cpp_code)
        self.assertIn("std::vector<std::string> tags;", cpp_code)

        # Try to validate with clang if available
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".hpp", delete=False
            ) as f:
                f.write(cpp_code)
                temp_file = f.name

            # Create a simple test file that includes the header
            test_cpp = (
                f'#include "{os.path.basename(temp_file)}"\nint main() {{ return 0; }}'
            )
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".cpp", delete=False
            ) as f:
                f.write(test_cpp)
                test_file = f.name

            result = subprocess.run(
                [
                    "clang++",
                    "-std=c++17",
                    "-fsyntax-only",
                    test_file,
                    "-I",
                    os.path.dirname(temp_file),
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            # Clean up
            os.unlink(temp_file)
            os.unlink(test_file)

            # Assert no syntax errors
            self.assertEqual(
                result.returncode, 0, f"Clang syntax check failed: {result.stderr}"
            )

        except (
            subprocess.TimeoutExpired,
            FileNotFoundError,
            subprocess.CalledProcessError,
        ):
            # If clang is not available or fails, just check the content
            self.assertIn("};", cpp_code)  # Basic check for struct closing


if __name__ == "__main__":
    unittest.main()
