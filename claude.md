---
alwaysApply: true
---

# Claude AI Assistant - Pipe Operator Project

This document provides context and guidelines for Claude AI when working on the pipe-operator project.

## Context Files

Reference these for project details:

- @pyproject.toml - Project configuration, dependencies, and tool settings
- @CONTRIBUTING.md - Contribution guidelines
- @.githooks/pre-commit - Pre-commit validation script
- @README.md - User-facing documentation
- @CHANGELOG.md - Version history

## Project Overview

**pipe-operator** is a Python library that brings Elixir's pipe operator functionality to Python. It provides two main implementations:

- **Elixir Flow**: Mimics Elixir's `|>` operator using Python's `>>` operator
- **Python Flow**: A more Pythonic approach using chaining

The project focuses on type safety, code quality, and compatibility across multiple Python versions (3.9-3.14).

## Technology Stack

- **Language**: Python 3.9+
- **Package Manager**: uv
- **Type Checkers**: mypy, pyright, ty
- **Linters**: ruff, flake8
- **Testing**: unittest with coverage (minimum 90%)
- **Build**: setuptools

## Project Structure

```txt
pipe_operator/
├── pipe_operator/           # Main package
│   ├── elixir_flow/        # Elixir-style pipe implementation
│   ├── python_flow/        # Python-style chaining implementation
│   └── shared/             # Shared utilities and exceptions
├── .githooks/              # Git hooks for pre-commit checks
├── .github/                # CI/CD workflows
└── pyproject.toml          # Project configuration and dependencies
```

## Python Version Compatibility **(Critical)**

Code must work on Python 3.9 through 3.14. Avoid Python 3.10+ only features.

**Anti-patterns - DO NOT USE:**

- ❌ `match`/`case` statements (Python 3.10+)
- ❌ `|` operator for type unions in annotations (use `Union[A, B]` instead)
- ❌ Structural pattern matching
- ❌ `TypeAlias` without `from typing_extensions import TypeAlias`
- ❌ `Self` type without `from typing_extensions import Self`
- ❌ Built-in generic types in annotations like `list[int]` (use `List[int]`)

**Correct patterns:**

- ✅ Use `Union[A, B]` or `Optional[A]` for type unions
- ✅ Use `List`, `Dict`, `Set`, `Tuple` from `typing` module
- ✅ Use `if`/`elif`/`else` instead of match statements
- ✅ Import from `typing_extensions` for newer type features

### Type Safety

- ✅ All functions must have complete type annotations
- ✅ Use specific types, avoid `Any` unless absolutely necessary
- ✅ Compatible with mypy, pyright, and ty (all three must pass)
- ❌ Never use `type: ignore` without justification
- ❌ Don't skip type annotations on function parameters or returns

Some test files have special type checking overrides (see @pyproject.toml).

### Testing

- ✅ Write comprehensive unit tests for all new code
- ✅ Maintain at least 90% code coverage (enforced)
- ✅ Tests located in `tests/` subdirectories or `tests.py` files
- ✅ Use unittest framework

### Code Style

- ✅ Use ruff for formatting (runs automatically via hooks)
- ✅ Follow PEP 8 guidelines
- ✅ Use double quotes for strings
- ✅ Descriptive variable names

## Context Management

- Use `/clear` between unrelated features to reset context
- Use `/compact` if responses slow down or context feels bloated

## Claude Commands

Custom Claude commands are available in `.claude/commands/`:

- `/verify`: Run all quality checks before committing
- `/test`: Run unit tests with coverage
- `/type-check`: Run all type checkers (mypy, pyright, ty)
