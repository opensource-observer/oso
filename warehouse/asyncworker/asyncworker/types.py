import abc
import typing as t

from google.protobuf.json_format import Parse
from google.protobuf.message import Message
from oso_core.resources import ResourcesContext, ResourcesRegistry

T = t.TypeVar("T", bound=Message)


class AsyncMessageQueueHandler(abc.ABC, t.Generic[T]):
    topic: str
    message_type: t.Type[T]

    @abc.abstractmethod
    async def handle_message(
        self, *, resources: ResourcesContext, message: T, **kwargs
    ) -> None: ...

    def new_message(self) -> T:
        """A method to create a new message instance"""
        return self.message_type()

    def parse_binary_message(self, data: bytes) -> T:
        """A method to parse binary encoded messages"""
        destination = self.new_message()
        destination.ParseFromString(data)
        return destination

    def parse_json_message(self, data: bytes | str) -> T:
        """A method to parse JSON encoded messages"""
        destination = self.new_message()
        Parse(data, destination)
        return destination


class MessageQueueHandlerRegistry:
    def __init__(self) -> None:
        self._listeners: dict[str, AsyncMessageQueueHandler] = {}

    def register(self, listener: AsyncMessageQueueHandler) -> None:
        if listener.topic not in self._listeners:
            self._listeners[listener.topic] = listener
        else:
            raise ValueError(f"Listener for topic {listener.topic} already registered")

    def get_handler(self, topic: str) -> AsyncMessageQueueHandler | None:
        return self._listeners.get(topic)


class GenericMessageQueueService(abc.ABC):
    def __init__(
        self, resources: ResourcesRegistry, registry: MessageQueueHandlerRegistry
    ) -> None:
        self.registry = registry
        self.resources = resources

    def get_queue_listener(self, topic: str) -> AsyncMessageQueueHandler:
        listener = self.registry.get_handler(topic)
        if not listener:
            raise ValueError(f"No listener registered for topic {topic}")
        return listener

    @abc.abstractmethod
    async def run_loop(self, queue: str) -> None:
        """A method that runs an endless loop listening to the given queue"""
        ...
