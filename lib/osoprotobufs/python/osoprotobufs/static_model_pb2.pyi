from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class StaticModelRunRequest(_message.Message):
    __slots__ = ()
    RUN_ID_FIELD_NUMBER: _ClassVar[int]
    DATASET_ID_FIELD_NUMBER: _ClassVar[int]
    MODEL_IDS_FIELD_NUMBER: _ClassVar[int]
    run_id: bytes
    dataset_id: str
    model_ids: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, run_id: _Optional[bytes] = ..., dataset_id: _Optional[str] = ..., model_ids: _Optional[_Iterable[str]] = ...) -> None: ...
