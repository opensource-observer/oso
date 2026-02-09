import typing as t

from pydantic import BaseModel


def is_pydantic_model_class(obj: t.Any) -> t.TypeGuard[t.Type[BaseModel]]:
    """Check if the given object is a Pydantic model."""
    if not isinstance(obj, type):
        return False
    return issubclass(obj, BaseModel)
