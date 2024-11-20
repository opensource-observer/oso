import typing as t
import os


def ensure_int(var: str, default: t.Optional[int] = None):
    """Ensures an environment variables is an integer"""
    value = os.environ.get(var, default)
    assert value
    return int
