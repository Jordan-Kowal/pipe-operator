# Contributing

## Setup

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

### Using git hooks

Git hooks are set in the [.githooks](.githooks) folder
_(as `.git/hooks` is not tracked in `.git`)_

Run the following command to tell `git` to look for hooks in this folder:

```shell
git config core.hooksPath .githooks
```

### CI/CD

We use GitHub actions to verify, build, and deploy the application. We currently have:

- [code_quality](.github/workflows/code_quality.yml): runs ruff, mypy, and coverage on Python 3.12
- [tests](.github/workflows/tests.yml): runs unit tests on multiple Python versions (from 3.8 to 3.12)
- [update_deps](.github/workflows/update_deps.yml): updates the dependencies (as `dependabot` does not support `uv` yet)
