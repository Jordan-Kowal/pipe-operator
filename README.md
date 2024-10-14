# Pipe Operator

Elixir's pipe operator in Python

- Callable with any number of args >= 1 (Func, Lambda, Class)
- Handle method/property calls with `_.property` or `_.method()`
- With or without parenthesis if 1 arg
  - Except for methods `_.x` (property) and `_.x()` (method)
- tap "side-effect" utils
- No `then` because this is basically a lambda call
- Decorator
  - works on func, method, or even class
  - Does not propagate
  - With or without parenthesis

## Linters and quality

- ruff: `# ruff: noqa: F821`
- flake8: `# flake8: noqa: F821` ignore = W503, F821
- mypy: ignore `operator,call-arg,call-overload,name-defined`

## How it works

- AST changes
- Operator -> Lambda

## Debug

debug=True
tap(print)
start_pdb() (tap(lambda x: pdb.set_trace()))
