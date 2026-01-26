"""Type definitions and protocols for GraphQL tool generation."""

import abc
import typing as t

from pydantic import BaseModel, Field


class MutationInfo(BaseModel):
    """Information about a GraphQL mutation extracted from schema."""

    model_config = {"arbitrary_types_allowed": True}

    name: str = Field(description="The mutation name (e.g., 'createNotebook')")
    description: str = Field(description="The mutation description from schema")
    input_model: t.Type[BaseModel] = Field(
        description="Generated Pydantic model for input validation"
    )
    payload_model: t.Type[BaseModel] = Field(
        description="Generated Pydantic model for payload response"
    )
    payload_fields: t.List[str] = Field(
        description="Top-level fields to return from payload"
    )
    graphql_input_type_name: str = Field(
        description="Original GraphQL input type name"
    )


class ToolConfig(BaseModel):
    """Configuration for GraphQL tool generation."""

    graphql_endpoint: str = Field(description="GraphQL endpoint URL")
    ignore_patterns: t.List[str] = Field(
        default_factory=list,
        description="Regex patterns for ignoring mutations",
    )
    api_key: t.Optional[str] = Field(
        default=None,
        description="API key for authentication (will use MCP_OSO_API_KEY from MCPConfig)",
    )
    auth_header_name: str = Field(
        default="Authorization",
        description="Authentication header name",
    )


class MutationFilter(abc.ABC):
    """Abstract base class for filtering mutations based on patterns."""

    @abc.abstractmethod
    def should_ignore(self, mutation: MutationInfo) -> bool:
        """Check if mutation should be ignored.

        Args:
            mutation: Mutation information

        Returns:
            True if mutation should be ignored, False otherwise
        """
        ...
