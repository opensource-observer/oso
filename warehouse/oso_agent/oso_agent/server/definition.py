import typing as t

from fastapi import FastAPI
from llama_index.core.llms import ChatMessage
from pydantic import BaseModel, Field, SecretStr

from ..util.config import AgentConfig, agent_config_dict


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


class ToolsRequest(BaseModel):
    """Request to proxy one of the agent's tool"""

    tool: str
    params: list[t.Any]


class BotConfig(AgentConfig):
    """Configuration for the bot."""

    model_config = agent_config_dict()

    discord_bot_token: SecretStr = Field(
        default=SecretStr(""),
        description="API key for the Arize Phoenix API"
    )

    discord_channel_id: SecretStr = Field(
        default=SecretStr(""),
        description="Channel ID that the bot should respond in"
    )

class AgentServerConfig(AgentConfig):
    """Configuration for the agent and its components."""

    model_config = agent_config_dict()

    port: int = Field(
        default=8000, description="Port for the server to run on"
    )

    host: str = Field(
        default="127.0.0.1",
        description="Host for the server to run on",
    )

    enable_discord_bot: bool = Field(
        default=False,
        description="Enable the Discord bot for the agent",
    )


AppLifespan = t.Callable[[FastAPI], t.Any]

ConfigType = t.TypeVar("ConfigType")

AppLifespanFactory = t.Callable[[ConfigType], AppLifespan]
