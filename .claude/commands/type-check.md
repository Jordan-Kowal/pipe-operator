---
description: Run all type checkers
---

Run all three type checkers to validate type safety:

1. **MyPy** (strict type checking)
   - `mypy .`

2. **Pyright** (secondary type checker)
   - `pyright .`

3. **Ty** (additional type checking)
   - `ty check . --error-on-warning`

Report the results from each type checker. If any type checker reports errors, provide details about what failed and where.
