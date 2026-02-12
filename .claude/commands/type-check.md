---
description: Run all type checkers
---

Run all four type checkers to validate type safety:

1. **MyPy** (strict type checking)
   - `mypy .`

2. **Pyright** (secondary type checker)
   - `pyright .`

3. **Ty** (additional type checking)
   - `ty check . --error-on-warning`

4. **Pyrefly** (additional type checking)
   - `pyrefly check .`

Report the results from each type checker. If any type checker reports errors, provide details about what failed and where.
