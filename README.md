# ✨ Pipe Operator ✨

![Code quality](https://github.com/Jordan-Kowal/pipe-operator/actions/workflows/code_quality.yml/badge.svg?branch=main)
![Tests](https://github.com/Jordan-Kowal/pipe-operator/actions/workflows/tests.yml/badge.svg?branch=main)
![Build](https://github.com/Jordan-Kowal/pipe-operator/actions/workflows/publish_package.yml/badge.svg?event=release)
![Coverage](https://badgen.net/badge/coverage/%3E90%25/pink)
![Tag](https://badgen.net/badge/tag/2.0.0/orange)
![Python](https://badgen.net/badge/python/3.9%20|%203.10%20|%203.11%20|%203.12|%203.13)
![Licence](https://badgen.net/badge/licence/MIT)

- [✨ Pipe Operator ✨](#-pipe-operator-)
  - [⚡ Quick start](#-quick-start)
  - [📕 Overview](#-overview)
  - [🐍 Pythonic implementation](#-pythonic-implementation)
    - [Available imports](#available-imports)
    - [Limitations](#limitations)
  - [🍹 Elixir-like implementation](#-elixir-like-implementation)
    - [Overview](#overview)
    - [Operations and shortcuts](#operations-and-shortcuts)
    - [How it works](#how-it-works)
    - [Linters and type-checkers issues](#linters-and-type-checkers-issues)
    - [Performances](#performances)
  - [🔗 Useful links](#-useful-links)
  - [⏳ Stats](#-stats)

`pipe_operator` allows you to use an elixir pipe-like syntax in python.
This module provides 2 vastly different implementations, each with its own pros and cons.

## ⚡ Quick start

As simple as `pip install pipe_operator`.
Then either import the 🐍 **pythonic version** or the 🍹 **elixir version**

```python
# Pythonic imports
from pipe_operator.python_flow import end, pipe, start, tap, task, then, wait
# Elixir imports
from pipe_operator.elixir_flow import elixir_pipe, tap, then
```

## 📕 Overview

You can use the 🐍 **pythonic** implementation, which is **entirely compatible with linters and type-checkers**,
but a bit more verbose than the original pipe operator:

```python
from pipe_operator.python_flow import end, pipe, start, tap, task, then, wait

result = (
    start("3")                              # start
    >> pipe(do_something)                   # function
    >> then[str, int](lambda x: int(x))     # typed lambda
    >> pipe(do_something_async)             # async function
    >> task("t1", lambda _: print("hello")) # lambda task
    >> pipe(do_something_else, 30, z=10)    # function with args/kwargs
    >> task("t2", do_something_async)       # async task
    >> wait(["t1"])                         # wait for a specific task
    >> pipe(BasicClass)                     # class
    >> pipe(BasicClass.my_classmethode)     # classmethod
    >> tap(BasicClass.my_method)            # (side effect) method
    >> pipe(BasicClass.other_method, 5)     # method with arg
    >> tap(lambda x: print(x))              # lambda (side-effect)
    >> wait()                               # wait for all remaining tasks
    >> end()                                # end
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

### Available imports

In the 🐍 **pythonic implementation**, we expose the following items:

| Import  | Description                                                           | Examples                                      |
| --------| --------------------------------------------------------------------- | --------------------------------------------- |
| `start` | The start of the pipe                                                 | `start("3")`                                  |
| `pipe`  | To call almost any functions, classes, or methods (except lambdas)    | `pipe(int)`, `pipe(do_something, 2000, z=10)` |
| `then`  | To call 1-arg lambda functions (like elixir)                          | `then[int, str](lambda x: str(x))`            |
| `tap`   | To perform side-effects and return the original value (like elixir)   | `tap(do_something)`                           |
| `task`  | To perform non-blocking function calls (in a thread)                  | `task("t1", do_something, arg1)`              |
| `wait`  | To wait for specific tasks to complete                                | `wait(["id1"])`, `wait()`                     |
| `end`   | The end of the pipe, to extract the raw final result                  | `end()`                                       |

### Limitations

**property:** Class instance properties cannot be called through `pipe`. You must use `then` with a lambda instead.
For example: `then[MyClass, int](lambda x: x.value)`

**functions without positional/keyword parameters:** Functions like `do_something(*args)` are supported though
the type-checker will complain. Use a single `# type: ignore` comment instead.

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

## ⏳ Stats

![Alt](https://repobeats.axiom.co/api/embed/4f71a7872457e4196720a7ca1b72ddfa25051420.svg "Repobeats analytics image")
