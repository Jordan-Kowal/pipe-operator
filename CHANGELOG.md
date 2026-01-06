# Changelog

## Legend

- 🚀 Features
- ✨ Improvements
- 🐞 Bugfixes
- 🔧 Others
- 💥 Breaking

## 2.0.2 - 2026-01-06

- 🔧 Added `CODEOWNERS` file and removed reviewers from dependabot
- 🔧 Added `ty` type-checker in the config and the CI
- 🔧 Fallback to `update-uv-lockfile` action for monthly dependency updates

## 2.0.1 - 2025-04-18

- 🔧 Removed `update_deps` action
- 🔧 Added `dependabot` config for `uv` deps updates
- 🔧 Updated CI to use python 3.13
- 🔧 Upgraded deps

## 2.0.0 - 2025-01-11

### 💥 Breaking changes: imports

Two major changes have been introduced:

- Imports are no longer at the top level but are now nested their respective modules
- For the 🐍 python implementation, the available imports have changed

```python
from pipe_operator.elixir_flow import elixir_pipe, tap, then
from pipe_operator.python_flow import end, pipe, start, tap, task, then, wait
```

If you were using the python implementation before, the migration is quite simple. Here is the mapping:

| Before       | After   |
| ------------ | ------- |
| `PipeStart`  | `start` |
| `Pipe`       | `pipe`  |
| `PipeArgs`   | `pipe`  |
| `Tap`        | `tap`   |
| `Then`       | `then`  |
| `ThreadPipe` | `task`  |
| `ThreadWait` | `wait`  |
| `PipeEnd`    | `end`   |

### 🚀 New feature: async function support

The 🐍 python implementation now support **async functions** from `asyncio`.
When using `pipe`, `tap`, or `task`, you can freely pass an async or sync function as the first argument.
As for `then`, it only supports single-arg lambda function.

### 🔧 Other changes

- ✨ [Python] Exported classes with aliases (ie `PipeStart` is exported as `start`) for improved readability
- 🔧 [Python] Updated documentation (docstrings and [README.md](./README.md))
- 🔧 [Python] `>>` logic is now handle in each pipeable's `__rrshift__` instead of `PipeObject.__rshift__`
- 🔧 [Python] Greatly improved typing annotations (using `@overload`, `@override`, `TypeAlias`, `TypeGuard`, ...)

## 1.1.0 - 2024-11-23

- 🚀 [Python] Added thread support with `ThreadPipe` and `ThreadWait`. See [README.md](README.md) for more details.
- ✨ [Python] Keep same `PipeObject` object throughout the pipe for improved performances
- ✨ [Python] Added the `PipeObject.history` attribute to keep track of all its values (only in debug mode)
- 🔧 [Python] Split logic into smaller modules: [base.py](pipe_operator/python_flow/base.py), [extras.py](pipe_operator/python_flow/extras.py), [threads.py](pipe_operator/python_flow/threads.py)

## 1.0.4 - 2024-11-22

- ✨ [Python] Added `__slots__` to classes for improved performances
- ✨ [Python] Added custom `PipeError` exception class for better error handling
- 🐞 [Elixir] Fixed error message for the `then` function

## 1.0.3 - 2024-11-02

- ✨ Official support for Python `3.13`
- 🔧 Fixed typo in project description
- 🔧 Fixed typo in GitHub action step names and added comments
- 🔧 Added missing GitHub action in [CHANGELOG.md](CHANGELOG.md)
- 🔧 Updated [README.md](README.md) with a **Performances** block
- 🔧 Updated [CONTRIBUTING.md](CONTRIBUTING.md) documentation
- 🔧 Moved `coverage` config into [pyproject.toml](pyproject.toml)

## 1.0.2 - 2024-10-25

- ✨ Classes and functions can now be imported directly, without going through submodules
- 🔧 Fixed [README.md](README.md) "Build" badge to use the **release** events

## 1.0.1 - 2024-10-25

- 🔧 Updated [CHANGELOG.md](CHANGELOG.md) design
- 🔧 Updated [README.md](README.md) content
- 🔧 Updated dev dependencies

## 1.0.0 - 2024-10-25

✨ Official release of the `pipe_operator` library ✨
