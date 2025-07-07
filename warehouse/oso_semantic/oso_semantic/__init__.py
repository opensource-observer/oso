# ruff: noqa: F401 F403

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("pyoso")
except PackageNotFoundError:
    __version__ = "unknown"

from .definition import *
from .errors import InvalidAttributeReferenceError
from .query import QueryBuilder
from .register import register_oso_models
