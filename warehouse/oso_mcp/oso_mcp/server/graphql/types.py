"""Type definitions and protocols for GraphQL tool generation."""

import abc
import typing as t

from graphql import SelectionSetNode
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


class AsyncGraphQLClient(abc.ABC):
    @abc.abstractmethod
    async def execute(
        self,
        query: str,
        operation_name: str,
        variables: dict[str, t.Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> t.Any:
        """Execute a GraphQL query or mutation.

        Args:
            query: GraphQL query or mutation string
            operation_name: Name of the operation to execute
            variables: Optional variables for the operation
            headers: Additional HTTP headers
        Returns:
            The parsed JSON response
        """
        ...


GraphQLClientFactory = t.Callable[[], t.AsyncContextManager[AsyncGraphQLClient]]
