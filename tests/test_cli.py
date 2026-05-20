"""Tests for the command-line interface."""

import os
import subprocess
import sys
import tempfile
import unittest


class TestCli(unittest.TestCase):
    """Test command-line generation behavior."""

    def test_custom_template_argument(self):
        typespec = """
        model User {
            name: string;
        }
        """
        template = "{% for struct in structs %}{{ struct.name }}:{{ struct.fields|length }}{% endfor %}"

        input_path = None
        template_path = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", suffix=".tsp", delete=False) as f:
                f.write(typespec)
                input_path = f.name

            with tempfile.NamedTemporaryFile(mode="w", suffix=".j2", delete=False) as f:
                f.write(template)
                template_path = f.name

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "typespec_parser.cli",
                    input_path,
                    "--language",
                    "rust",
                    "--template",
                    template_path,
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
        finally:
            if input_path:
                os.unlink(input_path)
            if template_path:
                os.unlink(template_path)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("User:1", result.stdout)


if __name__ == "__main__":
    unittest.main()
