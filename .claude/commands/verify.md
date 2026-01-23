---
description: Run all quality checks before commit
---

Run all quality assurance checks in the following order:

1. **Ruff** (imports, linting, formatting)
   - `ruff check --select I .`
   - `ruff check .`
   - `ruff format --check .`

2. **Flake8** (linting)
   - `flake8 .`

3. **MyPy** (type checking)
   - `mypy .`

4. **Pyright** (type checking)
   - `pyright .`

5. **Ty** (type checking)
   - `ty check . --error-on-warning`

6. **Coverage** (tests)
   - `coverage run -m unittest discover .`
   - `coverage report --fail-under=90`

Document the results of each check. If all checks pass successfully, confirm that the codebase is ready for commit. If any check fails, report which checks failed and provide details about the errors.
