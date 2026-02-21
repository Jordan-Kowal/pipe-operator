---
alwaysApply: true
---

# Claude AI Assistant - Pipe Operator Project

This document provides context and guidelines for Claude AI when working on the pipe-operator project.

## Key Files (read on-demand, not auto-loaded)

- `pyproject.toml` - Project config, dependencies, tool settings, type-checker overrides
- `CONTRIBUTING.md` - Setup and QA instructions
- `CHANGELOG.md` - Version history (update TBD section for unreleased changes)
- `.githooks/pre-commit` - Pre-commit validation script (7 steps)
- `.flake8` - Flake8 config (ignores: W503, F821, E501, E704; max-line-length: 88)

## Project Overview

**pipe-operator** is a Python library that brings Elixir's pipe operator functionality to Python. It provides two main implementations:

- **Elixir Flow**: Mimics Elixir's `|>` operator using Python's `>>` operator
- **Python Flow**: A more Pythonic approach using chaining

The project focuses on type safety, code quality, and compatibility across multiple Python versions (3.9-3.14).

## Technology Stack

- **Language**: Python 3.9+
- **Package Manager**: uv
- **Type Checkers**: mypy, pyright, ty, pyrefly
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

## Quick Reference Commands

```shell
# Full QA (mirrors pre-commit hook)
ruff check --select I . && ruff check . && ruff format --check .
flake8 .
mypy .
pyright .
ty check . --error-on-warning
pyrefly check .
coverage run -m unittest discover . && coverage report --fail-under=90
```

## Python Version Compatibility **(Critical)**

Code must work on Python 3.9 through 3.14. Avoid Python 3.10+ only features.

**Anti-patterns - DO NOT USE:**

- `match`/`case` statements (Python 3.10+)
- `|` operator for type unions in annotations (use `Union[A, B]` instead)
- Structural pattern matching
- `TypeAlias` without `from typing_extensions import TypeAlias`
- `Self` type without `from typing_extensions import Self`
- Built-in generic types in annotations like `list[int]` (use `List[int]`)

**Correct patterns:**

- Use `Union[A, B]` or `Optional[A]` for type unions
- Use `List`, `Dict`, `Set`, `Tuple` from `typing` module
- Use `if`/`elif`/`else` instead of match statements
- Import from `typing_extensions` for newer type features

### Type Safety

- All functions must have complete type annotations
- Use specific types, avoid `Any` unless absolutely necessary
- Compatible with mypy, pyright, ty, and pyrefly (all four must pass)
- Never use `type: ignore` without justification
- Some test files have special type checking overrides (see `pyproject.toml`)

### Testing

- Write comprehensive unit tests for all new code
- Maintain at least 90% code coverage (enforced)
- Tests located in `tests/` subdirectories or `tests.py` files alongside source
- Use unittest framework

### Code Style

- Use ruff for formatting (runs automatically via hooks)
- Follow PEP 8 guidelines
- Use double quotes for strings
- Descriptive variable names

### Code Conventions

- Use `# region ClassName` comments to separate classes in a file
- Use `__slots__` on all classes
- Imports: stdlib first, then `typing_extensions`, then internal (`pipe_operator.`)
- Internal imports use explicit relative paths (e.g., `from .classes import ...`)
- `__init__.py` files re-export with aliases (e.g., `PipeObject as start`) and define `__all__`
- Custom exception: `PipeError` in `pipe_operator.shared.exceptions`

## Claude Code Hooks (active in .claude/settings.json)

- **PostToolUse (Write|Edit)**: Auto-runs `ruff format` + `ruff check --fix --select I` on changed files
- **Stop**: Runs `mypy .` (first 20 lines) as a quick type-check sanity check
- **SessionStart**: Shows `git status --short` and last 3 commits
- **Plugin**: `pyright-lsp` enabled for real-time type checking

## Claude Commands

- `/verify` - Run all 7 quality checks (ruff, flake8, mypy, pyright, ty, pyrefly, coverage)
- `/test` - Run unit tests with coverage
- `/type-check` - Run all 4 type checkers
- Use `/clear` between unrelated features; `/compact` if context feels bloated
