.PHONY: help install test clean example

help:
	@echo "Available targets:"
	@echo "  install     Install dependencies with uv"
	@echo "  test        Run tests"
	@echo "  example     Run example script"
	@echo "  clean       Clean generated files"

install:
	uv sync --dev

test:
	uv run pytest

example:
	uv run python example.py

clean:
	rm -rf .venv
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
