from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("pyoso")
except PackageNotFoundError:
    __version__ = "unknown"

__all__ = ["client", "exceptions"]
