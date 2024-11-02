# ✨ Pipe Operator ✨

![Code quality](https://github.com/Jordan-Kowal/pipe-operator/actions/workflows/code_quality.yml/badge.svg?branch=main)
![Tests](https://github.com/Jordan-Kowal/pipe-operator/actions/workflows/tests.yml/badge.svg?branch=main)
![Build](https://github.com/Jordan-Kowal/pipe-operator/actions/workflows/publish_package.yml/badge.svg?event=release)
![Coverage](https://badgen.net/badge/coverage/%3E90%25/pink)
![Tag](https://badgen.net/badge/tag/1.0.3/orange)
![Python](https://badgen.net/badge/python/3.9%20|%203.10%20|%203.11%20|%203.12|%203.13)
![Licence](https://badgen.net/badge/licence/MIT)

- [✨ Pipe Operator ✨](#-pipe-operator-)
  - [⚡ Quick start](#-quick-start)
  - [📕 Overview](#-overview)
  - [🐍 Pythonic implementation](#-pythonic-implementation)
    - [Available classes](#available-classes)
    - [Limitations](#limitations)
  - [🍹 Elixir-like implementation](#-elixir-like-implementation)
    - [Overview](#overview)
    - [Operations and shortcuts](#operations-and-shortcuts)
    - [How it works](#how-it-works)
    - [Linters and type-checkers issues](#linters-and-type-checkers-issues)
    - [Performances](#performances)
  - [🔗 Useful links](#-useful-links)

`pipe_operator` allows you to use an elixir pipe-like syntax in python.
This module provides 2 vastly different implementations, each with its own pros and cons.

## ⚡ Quick start

As simple as `pip install pipe_operator`.
Then either import the 🐍 **pythonic classes** or the 🍹 **elixir functions**

```python
# Pythonic classes
from pipe_operator import Pipe, PipeArgs, PipeEnd, PipeStart, Tap, Then
# Elixir functions
from pipe_operator import elixir_pipe, tap, then
```

## 📕 Overview

You can use the 🐍 **pythonic** implementation, which is **entirely compatible with linters and type-checkers**,
but a bit more verbose than the original pipe operator:

```python
from pipe_operator import Pipe, PipeArgs, PipeEnd, PipeStart, Tap, Then

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

Or the 🍹 **elixir-like** implementation, whose syntax greatly resembles the original pipe operator,
but has major issues with linters and type-checkers.

```python
from pipe_operator import elixir_pipe, tap, then

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

## 🐍 Pythonic implementation

### Available classes

In the 🐍 **pythonic implementation**, we expose the following classes:

| Class       | Description                                                           | Examples                                  |
| ----------- | --------------------------------------------------------------------- | ----------------------------------------- |
| `PipeStart` | The start of the pipe                                                 | `PipeStart("3")`                          |
| `Pipe`      | Used to call almost any functions or classes, or methods              | `Pipe(int)`, `Pipe(my_func, 2000, z=10)`  |
| `PipeArgs`  | Same as `Pipe` but for function with no positional/keyword parameters | `PipeArgs(func, 1, 2)`                    |
| `Then`      | Same as `Pipe`, but for 1-arg lambda functions                        | `Then(lambda x: x.attribute)`             |
| `Tap`       | Used to trigger a side effect (meaning it returns the original value) | `Tap(print)`, `Tap(lambda x: x.method())` |
| `PipeEnd`   | The end of the pipe, to extract the raw final result                  | `PipeEnd()`                               |

### Limitations

**property:** Properties cannot be called directly. You must resort to the use of `Then(lambda x: x.my_property)`.
This will work just fine and ensure type-safety throughout the pipe.

**functions without positional/keyword parameters:** While they are technically supported by the `Pipe` class,
your type-checker will not handle them properly, because the `Pipe` class expect the function to have
at least 1 positional/keyword parameter (ie the first one, passed down the pipe). To bypass this limitation,
you should use `PipeArgs` instead.

**pyright:** `pyright` seems to have trouble dealing with our `>>` in some specific cases. As such,
we advise you set `reportOperatorIssue = "none"` in your `pyright` config.

## 🍹 Elixir-like implementation

### Overview

In the 🍹 **elixir-like implementation**, we expose 3 functions:

- `elixir_pipe`: a decorator that enables the use of "pipe" in our function
- `tap`: a function to trigger a side-effect and return the original value
- `then`: (optional) the proper way to pass lambdas into the pipe

The `elixir_pipe` decorator can take arguments allowing you to customize

```python
# Those are the default args
@elixir_pipe(placeholder="_", lambda_var="_pipe_x", operator=">>", debug=False)
def my_function()
    ...
```

- `placeholder`: The expected variable used in shortcut like `_.property`
- `lambda_var`: The variable named used internally when we generate lambda function. You'll likely never change this
- `operator`: The operator used in the pipe
- `debug`: If true, will print the output after each pipe operation

### Operations and shortcuts

Initially, all operations can be supported through the base operations,
with `lambdas` allowing you to perform any other operations. To make lambda usage cleaner,
you can write them into `then` calls as well.

| Operation                 | Input                    | Output                 |
| ------------------------- | ------------------------ | ---------------------- |
| function calls            | `a >> b(...)`            | `b(a, ...)`            |
| class calls               | `a >> B(...)`            | `B(a, ...)`            |
| calls without parenthesis | `a >> b`                 | `b(a)`                 |
| lambda calls              | `a >> (lambda x: x + 4)` | `(lambda x: x + 4)(a)` |

However, we've also added shortcuts, based on the `placeholder` argument, allowing you
to skip the lambda declaration and directly perform the following operations:

| Operation                   | Input                            | Output                                     |
| --------------------------- | -------------------------------- | ------------------------------------------ |
| method calls                | `a >> _.method(...)`             | `a.method(...)`                            |
| property calls              | `a >> _.property`                | `a.property`                               |
| binary operators            | `a >> _ + 3`                     | `(lambda Z: Z + 3)(a)`                     |
| f-strings                   | `a >> f"{_}"`                    | `(lambda Z: f"{Z}")(a)`                    |
| list/set/... creations      | `a >> [_, 1, 2]`                 | `(lambda Z: [Z, 1, 2])(a)`                 |
| list/set/... comprehensions | `a >> [x + _ for x in range(_)]` | `(lambda Z: [x + Z for x in range(Z)])(a)` |

### How it works

Here's quick rundown of how it works. Feel free to inspect the source code or the tests.
Once you've decorated your function and run the code:

- We pull the AST from the original function
- We remove our own decorator, to avoid recursion and impacting other functions
- We then rewrite the AST, following a specific set of rules (as shown in the table below)
- And finally we execute the re-written AST

Eventually, `a >> b(...) >> c(...)` becomes `c(b(a, ...), ...)`.

### Linters and type-checkers issues

Sadly, this implementation comes short when dealing with linters (like `ruff` or `flake8`)
and type-checkers (like `mypy` or `pyright`). Because these are static code analyzers, they inspect
the original code, and not your AST-modified version. To bypass the errors, you'll need to disable
the following:

- `mypy`: Either ignore `operator,call-arg,call-overload,name-defined`, or ignore just `name-defined` and use the `@no_type_check` decorator
- `pyright`: Set `reportOperatorIssue`, `reportCallIssue`, `reportUndefinedVariable` to `none`
- `ruff`: Disable the `F821` error
- `flake8`: Disable the `F821` error

### Performances

In terms of performances, this implementation should add very little overhead.
The decorator and AST rewrite are run **only once at compile time**, and while it does
generate a few extra lambda functions, it also removes the need for intermediate
variables.

## 🔗 Useful links

- [Want to contribute?](CONTRIBUTING.md)
- [See what's new!](CHANGELOG.md)
- Originally forked from [robinhilliard/pipes](https://github.com/robinhilliard/pipes)
