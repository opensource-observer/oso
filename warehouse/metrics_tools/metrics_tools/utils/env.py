import os
import typing as t


def required_var[T](var: str, default: t.Optional[T] = None):
    value = os.environ.get(var, default)
    assert value, f"{var} is required"
    return value


def required_int(var: str, default: t.Optional[int] = None):
    """Ensures an environment variables is an integer"""
    return int(required_var(var, default))


def required_str(var: str, default: t.Optional[str] = None):
    return required_var(var, default)


def required_bool(var: str, default: t.Optional[bool] = None):
    resolved = required_var(var, str(default))
    if isinstance(resolved, bool):
        return resolved
    else:
        return var.lower() in ["true", "1"]


def ensure_var[T](var: str, default: T, converter: t.Callable[[str], T]):
    try:
        value = os.environ[var]
        return converter(value)
    except KeyError:
        return default


def ensure_str(var: str, default: str):
    return ensure_var(var, default, str)


def coalesce_str(var: t.List[str], default: str):
    for v in var:
        if v in os.environ:
            return os.environ[v]
    return default


def ensure_int(var: str, default: int):
    return ensure_var(var, default, int)


def ensure_bool(var: str, default: bool = False):
    return ensure_var(var, default, lambda a: a.lower() in ["true", "1"])
