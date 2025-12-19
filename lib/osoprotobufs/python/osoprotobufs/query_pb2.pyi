from typing import ClassVar as _ClassVar
from typing import Optional as _Optional

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message

DESCRIPTOR: _descriptor.FileDescriptor

class QueryRunRequest(_message.Message):
    __slots__ = ()
    RUN_ID_FIELD_NUMBER: _ClassVar[int]
    QUERY_FIELD_NUMBER: _ClassVar[int]
    USER_FIELD_NUMBER: _ClassVar[int]
    METADATA_JSON_FIELD_NUMBER: _ClassVar[int]
    run_id: bytes
    query: str
    user: str
    metadata_json: str
    def __init__(
        self,
        run_id: _Optional[bytes] = ...,
        query: _Optional[str] = ...,
        user: _Optional[str] = ...,
        metadata_json: _Optional[str] = ...,
    ) -> None: ...
