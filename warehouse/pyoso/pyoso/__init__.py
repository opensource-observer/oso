# ruff: noqa: F401

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("pyoso")
except PackageNotFoundError:
    __version__ = "unknown"

from .client import Client
from .exceptions import HTTPError, OsoError
