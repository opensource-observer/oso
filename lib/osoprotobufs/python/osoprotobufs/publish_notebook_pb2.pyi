from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class PublishNotebookRunRequest(_message.Message):
    __slots__ = ()
    RUN_ID_FIELD_NUMBER: _ClassVar[int]
    NOTEBOOK_ID_FIELD_NUMBER: _ClassVar[int]
    OSO_API_KEY_FIELD_NUMBER: _ClassVar[int]
    run_id: bytes
    notebook_id: str
    oso_api_key: str
    def __init__(self, run_id: _Optional[bytes] = ..., notebook_id: _Optional[str] = ..., oso_api_key: _Optional[str] = ...) -> None: ...
