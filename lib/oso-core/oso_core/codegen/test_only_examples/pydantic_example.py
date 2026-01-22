import typing as t

from pydantic import BaseModel


class MyModel(BaseModel):
    x: int


class MyProtocol(t.Protocol):
    def get_model(self) -> MyModel: ...
