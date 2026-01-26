"""Type definitions and protocols for GraphQL tool generation."""

import abc
import typing as t

import httpx
from graphql import FragmentDefinitionNode, OperationDefinitionNode, SelectionSetNode
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
    graphql_input_type_name: str = Field(description="Original GraphQL input type name")


class QueryDocument(BaseModel):
    """Represents a parsed GraphQL document containing queries and fragments."""

    model_config = {"arbitrary_types_allowed": True}

    operations: t.List[OperationDefinitionNode] = Field(
        description="All query operations found in the document"
    )
    fragments: t.Dict[str, FragmentDefinitionNode] = Field(
        description="Fragment definitions by name"
    )
    file_path: str = Field(description="Source file path for debugging")


class QueryInfo(BaseModel):
    """Information about a GraphQL query extracted from client files."""

    model_config = {"arbitrary_types_allowed": True}

    name: str = Field(description="The query operation name")
    description: t.Optional[str] = Field(
        default=None, description="Query description from comments"
    )
    query_string: str = Field(
        description="The full query string with inlined fragments"
    )
    variable_definitions: t.List[t.Any] = Field(
        description="Variable definitions from query (VariableDefinitionNode)"
    )
    input_model: t.Type[BaseModel] = Field(
        description="Generated Pydantic model for variables"
    )
    payload_model: t.Type[BaseModel] = Field(
        description="Generated Pydantic model for response"
    )
    selection_set: SelectionSetNode = Field(description="The fields being selected")


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


HttpClientFactory = t.Callable[[], httpx.AsyncClient]


class AutogenMutationsConfig(BaseModel):
    """Configuration for tool generation from GraphQL mutations."""

    model_config = {"arbitrary_types_allowed": True}

    graphql_endpoint: str = Field(description="GraphQL endpoint URL")
    filters: t.List[MutationFilter] = Field(
        default_factory=list,
        description="Mutation filters to ignore certain mutations",
    )
    auth_header_name: str = Field(
        default="Authorization",
        description="Authentication header name",
    )
    http_client_factory: HttpClientFactory = Field(
        default=lambda: httpx.AsyncClient(),
        description="Optional factory function that returns an httpx.AsyncClient instance for dependency injection/testing",
    )
