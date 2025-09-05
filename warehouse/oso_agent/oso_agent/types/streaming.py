"""
Streaming types for OpenAI-compatible chat completions with thoughts.
"""

import asyncio
import typing as t
from datetime import datetime

from pydantic import BaseModel, Field


class Thought(BaseModel):
    """A single thought captured during workflow execution."""

    category: str = Field(
        description="Category of the thought (e.g., 'query_analysis', 'sql_generation')"
    )
    content: str = Field(description="The actual thought content")
    metadata: dict[str, t.Any] = Field(
        default_factory=dict, description="Additional metadata about the thought"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="When the thought was captured"
    )


class ThoughtsCollector:
    """Collector for capturing thoughts during workflow execution."""

    def __init__(self, session_id: str, max_size: int = 1000):
        self.session_id = session_id
        self.thoughts: asyncio.Queue[Thought] = asyncio.Queue(maxsize=max_size)

    async def add_thought(
        self, category: str, content: str, metadata: dict[str, t.Any] | None = None
    ) -> None:
        """Add a thought to the collector."""
        thought = Thought(category=category, content=content, metadata=metadata or {})
        await self.thoughts.put(thought)

    async def get_thoughts(self) -> list[Thought]:
        """Get and consume all collected thoughts."""
        thoughts = []
        while not self.thoughts.empty():
            try:
                thought = self.thoughts.get_nowait()
                thoughts.append(thought)
            except asyncio.QueueEmpty:
                break
        return thoughts

    async def clear(self) -> None:
        """Clear all thoughts."""
        while not self.thoughts.empty():
            try:
                self.thoughts.get_nowait()
            except asyncio.QueueEmpty:
                break


class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible chat completion request."""

    model: str = Field(description="Model name")
    messages: list[dict[str, str]] = Field(
        description="List of messages in the conversation"
    )
    temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="Sampling temperature"
    )
    max_tokens: int | None = Field(
        default=None, gt=0, description="Maximum tokens to generate"
    )
    top_p: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Nucleus sampling parameter"
    )
    frequency_penalty: float | None = Field(
        default=None, ge=-2.0, le=2.0, description="Frequency penalty"
    )
    presence_penalty: float | None = Field(
        default=None, ge=-2.0, le=2.0, description="Presence penalty"
    )
    stop: list[str] | str | None = Field(default=None, description="Stop sequences")
    user: str | None = Field(default=None, description="User identifier")
    thought: bool = Field(
        default=False, description="Whether to include thoughts in the response"
    )


class ChatCompletionChunk(BaseModel):
    """OpenAI-compatible streaming chunk."""

    id: str = Field(description="Unique identifier for the completion")
    object: str = Field(default="chat.completion.chunk", description="Object type")
    created: int = Field(description="Unix timestamp of creation")
    model: str = Field(description="Model used for completion")
    choices: list[dict[str, t.Any]] = Field(description="List of completion choices")


class ChatCompletionResponse(BaseModel):
    """OpenAI-compatible non-streaming response."""

    id: str = Field(description="Unique identifier for the completion")
    object: str = Field(default="chat.completion", description="Object type")
    created: int = Field(description="Unix timestamp of creation")
    model: str = Field(description="Model used for completion")
    choices: list[dict[str, t.Any]] = Field(description="List of completion choices")
    usage: dict[str, int] | None = Field(
        default=None, description="Token usage information"
    )


class TextFormat(BaseModel):
    """Text format configuration for responses."""

    type: str = Field(
        default="text", description="Format type, always 'text' for plain text"
    )


class TextConfig(BaseModel):
    """Configuration for text responses."""

    format: TextFormat = Field(
        default_factory=TextFormat, description="Text format configuration"
    )


class UsageDetails(BaseModel):
    """Token usage breakdown details."""

    cached_tokens: int = Field(default=0, description="Number of cached tokens")
    reasoning_tokens: int = Field(default=0, description="Number of reasoning tokens")


class Usage(BaseModel):
    """Token usage information."""

    input_tokens: int = Field(description="Number of input tokens")
    output_tokens: int = Field(description="Number of output tokens")
    total_tokens: int = Field(description="Total number of tokens")
    input_tokens_details: UsageDetails = Field(
        default_factory=UsageDetails, description="Input token details"
    )
    output_tokens_details: UsageDetails = Field(
        default_factory=UsageDetails, description="Output token details"
    )


class ResponseError(BaseModel):
    """Error object for failed responses."""

    type: str = Field(description="Error type")
    code: str | None = Field(default=None, description="Error code")
    message: str = Field(description="Error message")
    param: str | None = Field(
        default=None, description="Parameter that caused the error"
    )


class IncompleteDetails(BaseModel):
    """Details about why a response is incomplete."""

    reason: str = Field(description="Reason for incompleteness")


class OutputTextContent(BaseModel):
    """Output text content item."""

    type: str = Field(default="output_text", description="Content type")
    text: str = Field(description="The generated text")
    annotations: list[dict[str, t.Any]] = Field(
        default_factory=list, description="Text annotations"
    )


class OutputMessage(BaseModel):
    """Output message from the model."""

    id: str = Field(description="Message ID")
    type: str = Field(default="message", description="Output type")
    status: str = Field(description="Message status")
    role: str = Field(default="assistant", description="Message role")
    content: list[OutputTextContent] = Field(description="Message content")


class ReasoningConfig(BaseModel):
    """Configuration for reasoning models."""

    effort: str | None = Field(default=None, description="Reasoning effort level")
    summary: str | None = Field(default=None, description="Reasoning summary")


class ResponsesRequest(BaseModel):
    """OpenAI Responses API request model."""

    model: str = Field(description="Model ID to use for generation")
    input: str | list[t.Any] | None = Field(
        default=None, description="Input text or structured data"
    )
    instructions: str | None = Field(default=None, description="System instructions")
    max_output_tokens: int | None = Field(
        default=None, description="Maximum output tokens"
    )
    temperature: float | None = Field(
        default=1.0, ge=0.0, le=2.0, description="Sampling temperature"
    )
    top_p: float | None = Field(
        default=1.0, ge=0.0, le=1.0, description="Nucleus sampling parameter"
    )
    stream: bool = Field(default=False, description="Whether to stream the response")
    store: bool = Field(default=True, description="Whether to store the response")
    metadata: dict[str, str] | None = Field(
        default=None, description="Metadata key-value pairs"
    )
    text: TextConfig | None = Field(
        default_factory=TextConfig, description="Text configuration"
    )
    reasoning: ReasoningConfig | None = Field(
        default=None, description="Reasoning configuration"
    )
    tools: list[dict[str, t.Any]] = Field(
        default_factory=list, description="Available tools"
    )
    tool_choice: str | dict[str, t.Any] | None = Field(
        default="auto", description="Tool selection strategy"
    )
    parallel_tool_calls: bool = Field(
        default=True, description="Allow parallel tool calls"
    )
    previous_response_id: str | None = Field(
        default=None, description="Previous response ID for multi-turn"
    )
    truncation: str = Field(default="disabled", description="Truncation strategy")
    max_tool_calls: int | None = Field(default=None, description="Maximum tool calls")
    safety_identifier: str | None = Field(default=None, description="Safety identifier")
    prompt_cache_key: str | None = Field(default=None, description="Cache key")
    user: str | None = Field(default=None, description="User identifier")


class ResponsesResponse(BaseModel):
    """OpenAI Responses API response model."""

    id: str = Field(description="Response ID")
    object: str = Field(default="response", description="Object type")
    created_at: int = Field(description="Creation timestamp")
    status: str = Field(description="Response status")
    model: str = Field(description="Model used")
    output: list[OutputMessage] = Field(description="Generated output")
    error: ResponseError | None = Field(default=None, description="Error if failed")
    incomplete_details: IncompleteDetails | None = Field(
        default=None, description="Incomplete details"
    )
    instructions: str | None = Field(default=None, description="Instructions used")
    max_output_tokens: int | None = Field(default=None, description="Max output tokens")
    temperature: float | None = Field(default=None, description="Temperature used")
    top_p: float | None = Field(default=None, description="Top-p used")
    text: TextConfig | None = Field(default=None, description="Text configuration")
    reasoning: ReasoningConfig | None = Field(
        default=None, description="Reasoning configuration"
    )
    tools: list[dict[str, t.Any]] = Field(
        default_factory=list, description="Tools used"
    )
    tool_choice: str | dict[str, t.Any] | None = Field(
        default=None, description="Tool choice strategy"
    )
    parallel_tool_calls: bool = Field(
        default=True, description="Parallel tool calls setting"
    )
    previous_response_id: str | None = Field(
        default=None, description="Previous response ID"
    )
    truncation: str = Field(default="disabled", description="Truncation strategy")
    max_tool_calls: int | None = Field(default=None, description="Maximum tool calls")
    store: bool = Field(default=True, description="Store setting")
    usage: Usage | None = Field(default=None, description="Token usage")
    metadata: dict[str, str] | None = Field(default=None, description="Metadata")
    user: str | None = Field(default=None, description="User identifier")
    safety_identifier: str | None = Field(default=None, description="Safety identifier")
    prompt_cache_key: str | None = Field(default=None, description="Cache key")
