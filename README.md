# Pipe Operator

`pipe_operator` allows you to use an elixir pipe-like syntax in python.
This module provides 2 vastly different implementations, each with its own pros and cons.

The **Pythonic** implementation, which is **entirely compatible with linters and type-checkers**,
but a bit more verbose than the original pipe operator:

```python
from pipe_operator.python_flow import Pipe, PipeArgs, PipeEnd, PipeStart, Tap, Then

result = (
    PipeStart("3")                        # starts the pipe
    >> Pipe(int)                          # function with 1-arg
    >> Pipe(my_func, 2000, z=10)          # function with multiple args
    >> Tap(print)                         # side effect
    >> Then(lambda x: x + 1)              # lambda
    >> Pipe(MyClass)                      # class
    >> Pipe(MyClass.my_classmethod)       # classmethod
    >> Tap(MyClass.my_method)             # side effect that can update the original object
    >> Pipe(MyClass.my_other_method)      # method
    >> Then[int, int](lambda x: x * 2)    # explicitly-typed lambda
    >> PipeArgs(my_other_func, 4, 5, 6)   # special case for functions with no positional/keyword parameters
    >> PipeEnd()                          # extract the value
)
```

And the **Elixir-like** implementation, whose syntax greatly resembles the original pipe operator,
but has major issues with linters and type-checkers.

```python
from pipe_operator.elixir_flow import elixir_pipe, tap, then

@elixir_pipe
def workflow(value):
    results = (
        value                           # raw value
        >> BasicClass                   # class call
        >> _.value                      # property (shortcut)
        >> BasicClass()                 # class call
        >> _.get_value_plus_arg(10)     # method call
        >> 10 + _ - 5                   # binary operation (shortcut)
        >> {_, 1, 2, 3}                 # object creation (shortcut)
        >> [x for x in _ if x > 4]      # comprehension (shortcut)
        >> (lambda x: x[0])             # lambda (shortcut)
        >> my_func(_)                   # function call
        >> tap(my_func)                 # side effect
        >> my_other_func(2, 3)          # function call with extra args
        >> then(lambda a: a + 1)        # then
        >> f"value is {_}"              # formatted string (shortcut)
    )
    return results

workflow(3)
```

## How to use

As simple as `pip install pipe_operator`.
Then either import the **pythonic** or the **elixir** implementations

```python
from pipe_operator.elixir_flow import elixir_pipe, tap, then
from pipe_operator.python_flow import Pipe, PipeArgs, PipeEnd, PipeStart, Tap, Then
```

## Pythonic implementation

### Overview

Table

### Limitations

**property:** Properties cannot be called directly. You must resort to the use of `Then(lambda x: x.my_property)`.
This will work just fine and ensure type-safety throughout the pipe.

**verbosity:** To make the implementation linter and type-checker compliant,
we had to implement various classes to be used in the pipe.

**functions without positional/keyword parameters:** While they are technically supported by the `Pipe` class,
your type-checker will not handle them properly, because the `Pipe` class expect the function to have
at least 1 positional/keyword parameter (ie the first one, passed down the pipe). To bypass this limitation,
you should use `PipeArgs` instead.

**pyright:** `pyright` seems to have trouble dealing with our `>>` in some specific cases. As such,
we advise you set `reportOperatorIssue = "none"` in your `pyright` config.

## Elixir-like implementation

### Overview

Table

### How it works

decorator allows you to use
No recursion
AST rewrite
See table
shortcuts / then

### Limitations

Lots of issues with type-checkers and linters

## Useful links

- [Want to contribute?](CONTRIBUTING.md)
- [See what's new!](CHANGELOG.md)
- Originally forked from [robinhilliard/pipes](https://github.com/robinhilliard/pipes)

###### Linters and quality

- ruff: `# ruff: noqa: F821`
- flake8: `# flake8: noqa: F821` ignore = W503, F821
- mypy: ignore `operator,call-arg,call-overload,name-defined` OU `name-defined` + @no_type_check
- pyright:
  - reportOperatorIssue = "none"
  - reportCallIssue = "none"
  - reportUndefinedVariable = "none"
