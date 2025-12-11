from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class QueryRunRequest(_message.Message):
    __slots__ = ()
    RUN_ID_FIELD_NUMBER: _ClassVar[int]
    QUERY_FIELD_NUMBER: _ClassVar[int]
    JWT_FIELD_NUMBER: _ClassVar[int]
    METADATA_JSON_FIELD_NUMBER: _ClassVar[int]
    run_id: bytes
    query: str
    jwt: str
    metadata_json: str
    def __init__(self, run_id: _Optional[bytes] = ..., query: _Optional[str] = ..., jwt: _Optional[str] = ..., metadata_json: _Optional[str] = ...) -> None: ...
