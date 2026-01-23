# Claude AI Assistant - Pipe Operator Project

This document provides context and guidelines for Claude AI when working on the pipe-operator project.

## Project Overview

**pipe-operator** is a Python library that brings Elixir's pipe operator functionality to Python. It provides two main implementations:

- **Elixir Flow**: Mimics Elixir's `|>` operator using Python's `>>` operator
- **Python Flow**: A more Pythonic approach using chaining

The project focuses on type safety, code quality, and compatibility across multiple Python versions (3.9-3.13).

## Technology Stack

- **Language**: Python 3.9+
- **Package Manager**: uv
- **Type Checkers**: mypy, pyright, ty
- **Linters**: ruff, flake8
- **Testing**: unittest with coverage (minimum 90%)
- **Build**: setuptools

## Project Structure

```
pipe_operator/
├── pipe_operator/           # Main package
│   ├── elixir_flow/        # Elixir-style pipe implementation
│   ├── python_flow/        # Python-style chaining implementation
│   └── shared/             # Shared utilities and exceptions
├── .githooks/              # Git hooks for pre-commit checks
├── .github/                # CI/CD workflows
└── pyproject.toml          # Project configuration and dependencies
```

## Development Workflow

### Quality Assurance

The project has strict quality requirements. All code must pass:

1. **Ruff**: Import sorting, linting, and formatting
2. **Flake8**: Additional linting rules
3. **MyPy**: Type checking with strict settings
4. **Pyright**: Secondary type checker
5. **Ty**: Additional type checking
6. **Coverage**: Unit tests with 90% coverage minimum

### Running QA Checks

To run all quality checks locally:

```bash
# Ruff checks
ruff check --select I .  # Import sorting
ruff check .             # Linting
ruff format --check .    # Format checking

# Flake8
flake8 .

# Type checking
mypy .
pyright .
ty check . --error-on-warning

# Tests with coverage
coverage run -m unittest discover .
coverage report --fail-under=90
```

### Git Hooks

The project uses git hooks in `.githooks/`. To enable them:

```bash
git config core.hooksPath .githooks
```

The pre-commit hook runs all QA checks automatically.

## Important Considerations

### Type Safety

- The project has very strict type checking enabled
- All functions must have type annotations
- Some test files have special overrides (see pyproject.toml)
- Compatible with multiple type checkers (mypy, pyright, ty)

### Python Version Compatibility

- Code must work on Python 3.9 through 3.13
- CI runs tests on all supported versions
- Avoid using features only available in newer Python versions

### Code Style

- Use ruff for formatting (configured in pyproject.toml)
- Follow PEP 8 guidelines
- Keep imports sorted and organized
- Use double quotes for strings

### Testing

- Write comprehensive unit tests
- Maintain at least 90% code coverage
- Tests are in `tests/` subdirectories or `tests.py` files
- Use unittest framework

## CI/CD

The project uses GitHub Actions:

- **code_quality.yml**: Runs all QA checks
- **tests.yml**: Runs tests on Python 3.9-3.13
- **publish_package.yml**: Publishes to PyPI
- **update-uv-lockfile.yml**: Updates dependencies

## Common Tasks

### Adding a New Feature

1. Create/modify code with proper type annotations
2. Add comprehensive unit tests
3. Run all QA checks (use `/verify` command)
4. Ensure coverage remains above 90%
5. Update documentation if needed

### Fixing a Bug

1. Add a test that reproduces the bug
2. Fix the implementation
3. Verify all tests pass
4. Run all QA checks

### Updating Dependencies

```bash
uv sync
uv lock
```

## Claude Commands

Custom Claude commands are available in `.claude/commands/`:

- `/verify`: Run all quality checks before committing

## Hooks Configuration

The project uses Claude hooks for automation:

- **SessionStart**: Show git status and recent commits
- **PostToolUse**: Auto-format files after edits with ruff
- **Stop**: Run quick type check before ending session

## Key Files

- `pyproject.toml`: Project configuration, dependencies, and tool settings
- `CONTRIBUTING.md`: Contribution guidelines
- `.githooks/pre-commit`: Pre-commit validation script
- `README.md`: User-facing documentation
- `CHANGELOG.md`: Version history

## Notes for Claude

- Always run `/verify` before committing changes
- Pay special attention to type annotations
- Test coverage is critical - never reduce it below 90%
- The project supports multiple Python versions - avoid version-specific features
- When editing code, ruff will automatically format it via hooks
- The project uses multiple type checkers - code must satisfy all of them
