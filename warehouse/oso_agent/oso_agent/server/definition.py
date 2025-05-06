import typing as t

from fastapi import FastAPI
from llama_index.core.llms import ChatMessage
from pydantic import BaseModel, Field

from ..agent.config import AgentConfig
from ..utils.config import agent_config_dict


class ChatRequestMessageTextPart(BaseModel):
    type: t.Literal["text"]
    text: str

class ChatRequestMessageStepStartPart(BaseModel):
    type: t.Literal["step-start"]

ChatRequestMessagePart = t.Union[
    ChatRequestMessageTextPart,
    ChatRequestMessageStepStartPart,
]

class ChatRequestMessage(BaseModel):
    """Historical message for the agent."""

    role: t.Literal["user", "assistant"]
    content: str
    parts: list[t.Annotated[ChatRequestMessagePart, Field(discriminator="type")]] = Field(
        default_factory=lambda: []
    )

class ChatRequest(BaseModel):
    """Request to chat with the agent."""

    id: str

    # The chat history
    messages: list[ChatRequestMessage]

    @property
    def current_message(self) -> ChatRequestMessage:
        """Get the current message in the chat history."""
        print(f"LenMessage={len(self.messages)}")
        if len(self.messages) < 1:
            raise ValueError("No messages in chat history")
        return self.messages[-1]

    def to_llama_index_chat_history(self) -> t.List[ChatMessage]:
        """Convert to LlamaIndex chat history."""
        return [
            ChatMessage(
                role=message.role,
                content=message.content,
            )
            for message in self.messages
        ]

class AgentServerConfig(AgentConfig):
    """Configuration for the agent and its components."""

    model_config = agent_config_dict()

    port: int = Field(
        default=8000, description="Port for the server to run on"
    )

    host: str = Field(
        default="127.0.1",
        description="Host for the server to run on",
    )

AppLifespan = t.Callable[[FastAPI], t.Any]

ConfigType = t.TypeVar("ConfigType")

AppLifespanFactory = t.Callable[[ConfigType], AppLifespan]