"""Command-line interface for the TypeSpec parser."""

import argparse
import subprocess
import sys
from importlib.metadata import version


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="Parse TypeSpec files and generate code."
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"tsc-py {version('tsc-py')}",
    )
    parser.add_argument("input", help="Input TypeSpec file")
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    parser.add_argument(
        "--language",
        default="python",
        choices=["python", "cpp", "rust", "go", "golang", "zig", "v", "vlang"],
        help="Output language (default: python)",
    )
    parser.add_argument(
        "--no-format",
        action="store_true",
        help="Skip formatting the output with black (Python only)",
    )
    parser.add_argument(
        "--template",
        help="Path to a custom Jinja template for the selected language",
    )

    args = parser.parse_args()

    from .parser import TypeSpecParser

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
    if args.language == "python":
        output = ts_parser.generate_python(template_path=args.template)
    elif args.language == "cpp":
        output = ts_parser.generate_cpp_headers(template_path=args.template)
    elif args.language == "rust":
        output = ts_parser.generate_rust(template_path=args.template)
    elif args.language in {"go", "golang"}:
        output = ts_parser.generate_go(template_path=args.template)
    elif args.language == "zig":
        output = ts_parser.generate_zig(template_path=args.template)
    elif args.language in {"v", "vlang"}:
        output = ts_parser.generate_vlang(template_path=args.template)
    else:
        raise ValueError(f"Unsupported language: {args.language}")

    # Format with black if Python and requested
    if args.language == "python" and not args.no_format:
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
            print(f"Generated {args.language} code written to '{args.output}'")
        except Exception as e:
            print(f"Error writing to file '{args.output}': {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(output)


if __name__ == "__main__":
    main()
