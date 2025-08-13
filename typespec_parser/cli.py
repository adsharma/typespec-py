"""Command-line interface for the TypeSpec parser."""

import argparse
import sys

from .parser import TypeSpecParser


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Parse TypeSpec files and generate Python dataclasses."
    )
    parser.add_argument("input", help="Input TypeSpec file")
    parser.add_argument("-o", "--output", help="Output Python file (default: stdout)")

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
