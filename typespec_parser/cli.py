"""Command-line interface for the TypeSpec parser."""

import argparse
import subprocess
import sys

from .parser import TypeSpecParser


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Parse TypeSpec files and generate Python dataclasses."
    )
    parser.add_argument("input", help="Input TypeSpec file")
    parser.add_argument("-o", "--output", help="Output Python file (default: stdout)")
    parser.add_argument(
        "--no-format", action="store_true", help="Skip formatting the output with black"
    )

    args = parser.parse_args()

    # Read input file
    try:
        with open(args.input, "r") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: File '{args.input}' not found.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file '{args.input}': {e}", file=sys.stderr)
        sys.exit(1)

    # Parse and generate
    ts_parser = TypeSpecParser()
    ts_parser.parse(content)
    output = ts_parser.generate_dataclasses()

    # Format with black if requested
    if not args.no_format:
        try:
            result = subprocess.run(
                ["black", "-"],
                input=output,
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                output = result.stdout
            else:
                print(
                    f"Warning: Black formatting failed: {result.stderr}",
                    file=sys.stderr,
                )
        except FileNotFoundError:
            print("Warning: Black not found. Skipping formatting.", file=sys.stderr)

    # Output result
    if args.output:
        try:
            with open(args.output, "w") as f:
                f.write(output)
            print(f"Generated dataclasses written to '{args.output}'")
        except Exception as e:
            print(f"Error writing to file '{args.output}': {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(output)


if __name__ == "__main__":
    main()
