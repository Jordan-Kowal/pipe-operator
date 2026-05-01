.PHONY: help verify lint types test

help:
	@echo "Available targets:"
	@echo "  make verify  - Run all checks (lint + types + test)"
	@echo "  make lint    - Run linters (ruff + flake8)"
	@echo "  make types   - Run type checkers (mypy + pyright + ty + pyrefly)"
	@echo "  make test    - Run tests with coverage (>=90%)"

verify: lint types test

lint:
	uv run ruff check --select I .
	uv run ruff check .
	uv run ruff format --check .
	uv run flake8 .

types:
	uv run mypy .
	uv run pyright .
	uv run ty check . --error-on-warning
	uv run pyrefly check .

test:
	uv run coverage run -m unittest discover .
	uv run coverage report --fail-under=90
