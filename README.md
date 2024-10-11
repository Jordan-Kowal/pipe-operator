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

## How it works

- AST changes
- Operator -> Lambda
