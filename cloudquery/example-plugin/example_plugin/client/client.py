from typing import TypeAlias
from dataclasses import dataclass, field

Row: TypeAlias = tuple[str, str, dict]

DEFAULT_CONCURRENCY = 100
DEFAULT_QUEUE_SIZE = 10000


class FakeClient:
    def __init__(self):
        pass

    def load_rows(self) -> list[Row]:
        return [
            [
                "id1",
                "foo",
                {
                    "owner": "foo",
                    "somerandom": "thing",
                },
            ],
            [
                "id2",
                "bar",
                {
                    "owner": "bar",
                    "somerandom": "thing",
                },
            ],
        ]


@dataclass
class Spec:
    access_token: str
    size: int = field(default=10)
    concurrency: int = field(default=DEFAULT_CONCURRENCY)
    queue_size: int = field(default=DEFAULT_QUEUE_SIZE)

    def validate(self):
        if self.access_token is None:
            raise Exception("access_token must be provided")


class Client:
    def __init__(self, spec: Spec) -> None:
        self._spec = spec
        self._client = FakeClient()

    def id(self):
        return "example client"

    @property
    def client(self) -> FakeClient:
        return self._client
