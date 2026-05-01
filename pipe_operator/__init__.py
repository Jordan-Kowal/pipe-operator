from importlib.metadata import PackageNotFoundError, version

from . import elixir_flow, python_flow

try:
    __version__ = version("pipe_operator")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"

__all__ = [
    "__version__",
    "elixir_flow",
    "python_flow",
]
