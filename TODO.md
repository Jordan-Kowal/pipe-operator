# TODO

## Setup

- [x] Project setup (pyproject, uv, precommits)
- [x] Basic CI/CD (ruff/tests)

## Implementation

- [x] Pipe default workflow through AST
- [ ] Debug mode
  - [ ] Automatic print
  - [ ] Allow override of default func
  - [ ] Check implementation with `pdb`
- [x] `tap` actions
- [x] `then` actions (no then as this is literally a lambda call)
- [x] `lambda` actions
- [x] Work with class and methods
- [] Using _ substitution
  - [x] Kernel operators (`>> _ + 3`)
  - [x] Allow calling methods of object
  - [x] Allow calling attribute of object
  - [ ] Struct calls (tuple, list, dict, set, string)
- [x] Handle missing parenthesis (`print()` vs `print`)
- [ ] Allow parameter overrides: operator, placeholder, replacement
- [ ] `if` workflow
- [ ] `case` workflow
- [ ] Issues
  - [ ] Recompute line errors correctly (`ast.fix_missing_locations(tree)`)
  - [ ] Fix ruff and mypy issues

## Deployment

- [ ] PIPY setup (<https://github.com/scikit-learn/scikit-learn/blob/main/pyproject.toml>)
- [ ] CI/CD Deploy
- [ ] Readme
- [ ] Changelog
