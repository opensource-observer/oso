import typing as t
from datetime import datetime

from metrics_tools.compute.types import ExportReference


class TimeOrderedStorageFile(t.Protocol):
    @property
    def stored_time(self) -> datetime: ...

    async def delete(self) -> None: ...

    @property
    def uri(
        self,
    ) -> str: ...  # URI to the file (full path plus correct protocol scheme)

    @property
    def full_path(self) -> str: ...  # Full path including any time prefixing

    @property
    def rel_path(self) -> str: ...  # Relative path not including any time prefixing

    @property
    def name(self) -> str: ...  # Name of the file


class TimeOrderedStorage(t.Protocol):
    def generate_path(self, stored_time: datetime, *joins: str) -> str: ...

    def iter_files(
        self,
        *,
        search_prefix: str = "",
        export_reference: t.Optional[ExportReference] = None,
        before: t.Optional[datetime] = None,
        after: t.Optional[datetime] = None
    ) -> t.AsyncIterable[TimeOrderedStorageFile]: ...
