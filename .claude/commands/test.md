---
description: Run unit tests with coverage
---

Run the unit tests with coverage reporting:

1. **Run Tests**
   - `coverage run -m unittest discover .`

2. **Show Coverage Report**
   - `coverage report --fail-under=90`

Report the test results and coverage percentage. If coverage is below 90%, highlight which files need additional test coverage.
