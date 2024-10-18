# Pipe Operator

## Python

Attribute with Then
_sum(*args) issue, either PipeArgs or Pipe + # type: ignore

- pyright: reportOperatorIssue = "none"

## Elixir

shortcuts instead of lambdas
then optional but available

### How it works

- AST changes
- Operator -> Lambda

### Linters and quality

- ruff: `# ruff: noqa: F821`
- flake8: `# flake8: noqa: F821` ignore = W503, F821
- mypy: ignore `operator,call-arg,call-overload,name-defined` OU `name-defined` + @no_type_check
- pyright:
  - reportOperatorIssue = "none"
  - reportCallIssue = "none"
  - reportUndefinedVariable = "none"
