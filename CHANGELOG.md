# Changelog

## Legend

- 🚀 Features
- ✨ Improvements
- 🐞 Bugfixes
- 🔧 Others
- 💥 Breaking

## TBD

- 💥 [Python] Removed both `Then` and `PipeArgs` to reduce complexity, as it can easily be replaced with `Pipe`
- 🚀 [Python] Added `AsyncPipe` to handle (and wait for) async function calls from asyncio
- 🔧 [Python] `>>` logic is now handle in each pipeable's `__rrshift__` instead of `PipeStart.__rshift__`
- 🔧 [Python] Reworked project structure

## 1.1.0 - 2024-11-23

- 🚀 [Python] Added thread support with `ThreadPipe` and `ThreadWait`. See [README.md](README.md) for more details.
- ✨ [Python] Keep same `PipeStart` object throughout the pipe for improved performances
- ✨ [Python] Added the `PipeStart.history` attribute to keep track of all its values (only in debug mode)
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
