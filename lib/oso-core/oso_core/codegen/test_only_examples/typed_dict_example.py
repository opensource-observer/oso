import typing as t


class MyDict(t.TypedDict):
    x: int


class MyProtocol(t.Protocol):
    def get_dict(self) -> MyDict: ...
