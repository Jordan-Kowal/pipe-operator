# Contributing

## Setup

To get started, follow these steps:

```shell
pip install uv
uv sync
. .venv/bin/activate
```

## QA

### Using git hooks

Git hooks are set in the [.githooks](.githooks) folder
_(as `.git/hooks` is not tracked in `.git`)_

Run the following command to tell `git` to look for hooks in this folder:

```shell
git config core.hooksPath .githooks
```

### CI/CD

We use GitHub actions to verify, build, and deploy the application. We currently have:

- [qa](.github/workflows/qa.yml): runs ruff, mypy, and tests
