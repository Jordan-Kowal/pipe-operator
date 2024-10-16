# TODO

## AST Implementation

- [x] Pipe default workflow through AST
  - [x] `tap` actions
  - [x] `then` actions (no then as this is literally a lambda call)
  - [x] `lambda` actions
  - [x] Work with class and methods
  - [x] Handle missing parenthesis (`print()` vs `print`)
- [x] Using _ substitution
  - [x] Kernel operators (`>> _ + 3`)
  - [x] Allow calling methods of object
  - [x] Allow calling attribute of object
  - [x] F-strings
  - [x] Struct calls (tuple, list, dict, set)
  - [x] Comprehensions (gen, list, dict, set)
- [x] Allow parameter overrides:
  - [x] Allow decorator call without parenthesis
  - [x] operator
  - [x] placeholder
  - [x] replacement
- [x] Debug mode
  - [x] Automatic print
  - [x] Check implementation with `pdb`
- [ ] Issues
  - [ ] Recompute line errors numbers correctly
  - [x] Investigate issues with `mypy`
  - [x] Investigate issues with `ruff`
  - [x] Investigate issues with `flake8`
- [x] Update docstrings

## Python implementation

- [x] Handle functions
- [x] Handle lambdas
- [ ] Handle class
- [ ] Handle methods
- [ ] Handle property
- [ ] Get result easily at the end
- [ ] Add `tap` action
- [x] Add `debug` mode
- [ ] Add `start pdb` mode
- [ ] Allow override of operator
- [x] Handle typing correctly
- [ ] Update docstrings

## Shared

- [x] QA
  - [x] Format test inputs
  - [x] Add coverage
  - [x] Add dependency updates through github action
  - [x] Run tests on multiple python versions

## Deployment

- [ ] Maybe rename modules
- [ ] Project and PIPY setup (<https://github.com/scikit-learn/scikit-learn/blob/main/pyproject.toml>)
- [ ] CI/CD Deploy
- [ ] Update README.md and add tags
- [ ] Changelog

## Later

- [ ] Replace custom workflow with `dependabot` when `uv` gets supported
