from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class DataIngestionRunRequest(_message.Message):
    __slots__ = ()
    RUN_ID_FIELD_NUMBER: _ClassVar[int]
    DATASET_ID_FIELD_NUMBER: _ClassVar[int]
    CONFIG_ID_FIELD_NUMBER: _ClassVar[int]
    run_id: bytes
    dataset_id: str
    config_id: bytes
    def __init__(self, run_id: _Optional[bytes] = ..., dataset_id: _Optional[str] = ..., config_id: _Optional[bytes] = ...) -> None: ...
