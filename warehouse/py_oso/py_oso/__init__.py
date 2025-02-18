from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("py_oso")
except PackageNotFoundError:
    __version__ = "unknown"

__all__ = ["client"]
