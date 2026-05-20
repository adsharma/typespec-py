"""Tests for generated Rust, Go, Zig, and V code."""

import unittest

from typespec_parser.parser import TypeSpecParser


TYPESPEC = """
model Address {
    street: string;
    city: string;
}

model User {
    displayName: string;
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


class TestGeneratedLanguages(unittest.TestCase):
    """Test non-Python language generators."""

    def setUp(self):
        self.parser = TypeSpecParser()
        self.parser.parse(TYPESPEC)

    def test_generate_rust(self):
        code = self.parser.generate_rust()

        self.assertIn("pub enum Status", code)
        self.assertIn("Active,", code)
        self.assertIn("pub struct User", code)
        self.assertIn("pub display_name: String,", code)
        self.assertIn("pub email: Option<String>,", code)
        self.assertIn("pub address: Address,", code)
        self.assertIn("pub tags: Vec<String>,", code)

    def test_generate_go(self):
        code = self.parser.generate_go()

        self.assertIn("package typespec", code)
        self.assertIn("type Status string", code)
        self.assertIn('StatusActive Status = "active"', code)
        self.assertIn("type User struct", code)
        self.assertIn('DisplayName string `json:"displayName"`', code)
        self.assertIn('Email *string `json:"email"`', code)
        self.assertIn('Address Address `json:"address"`', code)
        self.assertIn('Tags []string `json:"tags"`', code)

    def test_generate_zig(self):
        code = self.parser.generate_zig()

        self.assertIn("const std = @import(\"std\");", code)
        self.assertIn("pub const Status = enum", code)
        self.assertIn("active,", code)
        self.assertIn("pub const User = struct", code)
        self.assertIn("display_name: []const u8", code)
        self.assertIn("email: ?[]const u8", code)
        self.assertIn("address: Address", code)
        self.assertIn("tags: [][]const u8", code)

    def test_generate_vlang(self):
        code = self.parser.generate_vlang()

        self.assertIn("module typespec", code)
        self.assertIn("pub enum Status", code)
        self.assertIn("active", code)
        self.assertIn("pub struct User", code)
        self.assertIn("display_name string", code)
        self.assertIn("email ?string", code)
        self.assertIn("address Address", code)
        self.assertIn("tags []string", code)


if __name__ == "__main__":
    unittest.main()
