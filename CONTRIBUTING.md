# Contributing

## Setup

We use `uv` as our package manager.
To get started, follow these steps:

```shell
pip install uv
uv sync
. .venv/bin/activate
```

## QA

### Tests

Tests are run using either `unittest` or `coverage`.

With `unittest`:

```shell
python -m unittest discover .
```

With `coverage`:

```shell
coverage run -m unittest discover .
coverage report --fail-under=90
coverage html
```

In the CI, tests are run on multiple Python versions (from 3.9 to 3.12)
to ensure compatibility on each version.

### Using git hooks

Git hooks are set in the [.githooks](.githooks) folder
_(as `.git/hooks` is not tracked in `.git`)_

Run the following command to tell `git` to look for hooks in this folder:

```shell
git config core.hooksPath .githooks
```

### Linters

In both the CI and githooks, we use both `ruff` and `flake8`.
This is mostly to ensure and test how both linters react to the pipe syntax
and better document in the [README.md](README.md)] the required setups.

The same goes for `mypy`.

### CI/CD

We use GitHub actions to verify, build, and deploy the application. We currently have:

- [code_quality](.github/workflows/code_quality.yml): runs `ruff`, `flake8`, `mypy`, and `coverage` on Python 3.12
- [tests](.github/workflows/tests.yml): runs unittests on multiple Python versions (from 3.9 to 3.12)
- [update_deps](.github/workflows/update_deps.yml): updates the dependencies (as `dependabot` does not support `uv` yet)
