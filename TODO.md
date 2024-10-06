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
- [ ] Using _ substitution
  - [ ] Kernel operators (`>> _ + 3`)
  - [ ] Allow calling methods of object
  - [ ] Allow calling attribute of object (like a lambda/then)
  - [ ] Should work with `tap`
- [x] Handle missing parenthesis (`print()` vs `print`)
- [ ] `if` workflow
- [ ] `case` workflow
- [ ] Debugger/code info update/fix
- [ ] Fix typing issue

## Deployment

- [ ] PIPY setup (<https://github.com/scikit-learn/scikit-learn/blob/main/pyproject.toml>)
- [ ] CI/CD Deploy
- [ ] Readme
- [ ] Changelog
