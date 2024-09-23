import abc
import json
import typing as t

T = t.TypeVar("T", bound="State")


class ResourceManager[T](abc.ABC):
    def retrieve_state(self) -> T:
        raise NotImplementedError()

    def set_state(self, state: T):
        raise NotImplementedError()


class StateComparison:
    def __init__(self, is_changed: bool):
        self._is_changed = is_changed

    def is_changed(self):
        return self._is_changed


class State[S](abc.ABC):
    def __init__(self, state: S):
        self._state = state

    @property
    def value(self) -> S:
        return self._state

    @property
    def comparable_value(self) -> t.Any:
        return self.value

    def compare(self, other: "State[S]"):
        return other.comparable_value == self.comparable_value

    def to_json(self):
        return json.dumps(self.value)

    @classmethod
    def from_json(cls, val: str):
        return cls(json.loads(val))


def apply_metrics(state_storage: str = ""):
    # Load all of the metrics
    from sqlmesh.core.model import model

    from . import metrics_factories  # noqa

    registry = model.get_registry()

    for name, model_def in registry.items():
        model_def.model()
