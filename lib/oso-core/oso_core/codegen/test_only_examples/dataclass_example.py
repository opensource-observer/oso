import typing as t
from dataclasses import dataclass


@dataclass
class MyData:
    x: int


class MyProtocol(t.Protocol):
    def get_data(self) -> MyData: ...
