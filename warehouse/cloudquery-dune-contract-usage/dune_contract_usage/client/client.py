from typing import TypeAlias, Generator
from dataclasses import dataclass, field
from ..load_csvs import load_csvs_in_folder, DuneContractUsage

Row: TypeAlias = tuple[str, str, dict]

DEFAULT_CONCURRENCY = 10
DEFAULT_QUEUE_SIZE = 10


@dataclass
class Spec:
    csv_folder_path: str
    size: int = field(default=10)
    concurrency: int = field(default=DEFAULT_CONCURRENCY)
    queue_size: int = field(default=DEFAULT_QUEUE_SIZE)

    def validate(self):
        if self.csv_folder_path is None:
            raise Exception("csv_folder_path must be provided")


class LoadDuneCSVClient:
    def __init__(self, spec: Spec):
        self._csv_folder_path = spec.csv_folder_path

    def load_rows(self) -> Generator[DuneContractUsage, None, None]:
        return load_csvs_in_folder(self._csv_folder_path)


class Client:
    def __init__(self, spec: Spec) -> None:
        self._spec = spec
        self._client = LoadDuneCSVClient(spec)

    def id(self):
        return "dummy client"

    @property
    def client(self) -> LoadDuneCSVClient:
        return self._client
