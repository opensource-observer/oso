"""Type definitions and protocols for GraphQL tool generation."""

from __future__ import annotations

import abc
import typing as t
from dataclasses import dataclass, field
from enum import Enum

from graphql import (
    FieldNode,
    FragmentDefinitionNode,
    FragmentSpreadNode,
    GraphQLEnumType,
    GraphQLField,
    GraphQLInputObjectType,
    GraphQLNamedType,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLUnionType,
    InlineFragmentNode,
    OperationDefinitionNode,
    SelectionSetNode,
    VariableDefinitionNode,
)
from pydantic import BaseModel, Field

# Type alias for the unwrapped base schema type
SchemaType = t.Union[
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLEnumType,
    GraphQLUnionType,
    GraphQLInputObjectType,
]


@dataclass
class QueryDocumentField:
    """A field in a query/fragment selection, enriched with schema type info.

    This represents a FieldNode from the AST combined with resolved type
    information from the schema. The schema_type is the unwrapped base type
    (NonNull and List wrappers are represented via is_required and is_list).
    """

    ast_node: FieldNode
    field_name: str
    alias: t.Optional[str]
    schema_type: SchemaType
    is_required: bool
    is_list: bool
    children: t.List[QueryDocumentSelection] = field(default_factory=list)


@dataclass
class QueryDocumentFragmentSpread:
    """A fragment spread reference, resolved to its definition.

    This represents a FragmentSpreadNode (...FragmentName) with a direct
    reference to the resolved QueryDocumentFragment.
    """

    ast_node: FragmentSpreadNode
    fragment_name: str
    fragment: QueryDocumentFragment


@dataclass
class QueryDocumentInlineFragment:
    """An inline fragment with resolved type condition.

    This represents an InlineFragmentNode (... on TypeName { ... }) with
    the type condition resolved to the actual GraphQL object type.
    """

    ast_node: InlineFragmentNode
    type_condition: t.Optional[GraphQLObjectType]
    children: t.List[QueryDocumentSelection] = field(default_factory=list)


# Union of all selection types that can appear in a selection set
QueryDocumentSelection = t.Union[
    QueryDocumentField,
    QueryDocumentFragmentSpread,
    QueryDocumentInlineFragment,
]


@dataclass
class QueryDocumentVariable:
    """A variable definition with resolved type info.

    This represents a VariableDefinitionNode ($varName: Type) with the
    type information extracted and unwrapped.
    """

    ast_node: VariableDefinitionNode
    name: str
    graphql_type: GraphQLNamedType  # The original wrapped type for reference
    is_required: bool
    is_list: bool
    default_value: t.Optional[t.Any] = None


@dataclass
class QueryDocumentOperation:
    """A query/mutation/subscription operation.

    This represents an OperationDefinitionNode with resolved root type
    from the schema (Query, Mutation, or Subscription type).
    """

    ast_node: OperationDefinitionNode
    name: str
    operation_type: str  # 'query', 'mutation', 'subscription'
    root_type: GraphQLObjectType
    variables: t.List[QueryDocumentVariable] = field(default_factory=list)
    children: t.List[QueryDocumentSelection] = field(default_factory=list)


@dataclass
class QueryDocumentFragment:
    """A fragment definition with resolved type condition.

    This represents a FragmentDefinitionNode (fragment Name on Type { ... })
    with the type condition resolved to the actual GraphQL object type.
    """

    ast_node: FragmentDefinitionNode
    name: str
    type_condition_name: str
    type_condition: GraphQLObjectType
    children: t.List[QueryDocumentSelection] = field(default_factory=list)
    dependencies: t.Set[str] = field(default_factory=set)


@dataclass
class QueryDocument:
    """Parsed GraphQL document with all types resolved from schema.

    This is the enriched representation of a .graphql file that contains:
    - Operations (queries, mutations, subscriptions) with resolved root types
    - Fragments with resolved type conditions
    - All fields with their schema types resolved and unwrapped
    """

    file_path: str
    operations: t.List[QueryDocumentOperation] = field(default_factory=list)
    fragments: t.Dict[str, QueryDocumentFragment] = field(default_factory=dict)


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


class VisitorControl(Enum):
    """Control flow for visitor traversal.

    Returned from handle_* methods to control traversal behavior.
    """

    CONTINUE = "continue"  # Continue visiting normally
    SKIP = "skip"  # Skip children of this node (but continue with siblings)
    STOP = "stop"  # Stop all visiting immediately


class GraphQLSchemaTypeVisitor(t.Protocol):
    """Interface for visiting GraphQL schema types during traversal.

    Subclasses implement handle_* methods to process each type.
    All handle_* methods return VisitorControl to control traversal flow.

    This class defines only the visitor interface - use GraphQLSchemaTraverser
    for the actual tree traversal.

    Example usage:
        class MyVisitor(GraphQLSchemaVisitor):
            def handle_enter_object(self, field_name, object_type, is_required, is_list):
                print(f"Entering {field_name}: {object_type.name}")
                return VisitorControl.CONTINUE

        visitor = MyVisitor()
        traverser = GraphQLSchemaTraverser(visitor, selection_set=..., schema=...)
        traverser.visit(some_graphql_type, field_name="root")
    """

    def handle_scalar(
        self,
        field_name: str,
        scalar_type: GraphQLScalarType,
        is_required: bool,
        is_list: bool,
    ) -> VisitorControl:
        """Handle a scalar type (String, Int, Boolean, etc.).

        Args:
            field_name: Name of the field with this type
            scalar_type: The scalar type
            is_required: Whether wrapped in GraphQLNonNull
            is_list: Whether wrapped in GraphQLList

        Returns:
            VisitorControl to control traversal flow
        """
        return VisitorControl.CONTINUE

    def handle_enum(
        self,
        field_name: str,
        enum_type: GraphQLEnumType,
        is_required: bool,
        is_list: bool,
    ) -> VisitorControl:
        """Handle an enum type.

        Args:
            field_name: Name of the field with this type
            enum_type: The enum type
            is_required: Whether wrapped in GraphQLNonNull
            is_list: Whether wrapped in GraphQLList

        Returns:
            VisitorControl to control traversal flow
        """
        return VisitorControl.CONTINUE

    def handle_enter_object(
        self,
        field_name: str,
        object_type: GraphQLObjectType,
        is_required: bool,
        is_list: bool,
    ) -> VisitorControl:
        """Called when entering an object type (before visiting fields).

        Args:
            field_name: Name of the field with this type
            object_type: The object type
            is_required: Whether wrapped in GraphQLNonNull
            is_list: Whether wrapped in GraphQLList

        Returns:
            CONTINUE to traverse fields, SKIP to skip children, STOP to halt
        """
        return VisitorControl.CONTINUE

    def handle_leave_object(
        self,
        field_name: str,
        object_type: GraphQLObjectType,
        is_required: bool,
        is_list: bool,
    ) -> VisitorControl:
        """Called when leaving an object type (after visiting all fields).

        Args:
            field_name: Name of the field with this type
            object_type: The object type
            is_required: Whether wrapped in GraphQLNonNull
            is_list: Whether wrapped in GraphQLList

        Returns:
            VisitorControl to control traversal flow
        """
        return VisitorControl.CONTINUE

    def handle_enter_input_object(
        self,
        field_name: str,
        input_type: GraphQLInputObjectType,
        is_required: bool,
        is_list: bool,
    ) -> VisitorControl:
        """Called when entering an input object type (before visiting fields).

        Args:
            field_name: Name of the field with this type
            input_type: The input object type
            is_required: Whether wrapped in GraphQLNonNull
            is_list: Whether wrapped in GraphQLList

        Returns:
            CONTINUE to traverse fields, SKIP to skip children, STOP to halt
        """
        return VisitorControl.CONTINUE

    def handle_leave_input_object(
        self,
        field_name: str,
        input_type: GraphQLInputObjectType,
        is_required: bool,
        is_list: bool,
    ) -> VisitorControl:
        """Called when leaving an input object type (after visiting all fields).

        Args:
            field_name: Name of the field with this type
            input_type: The input object type
            is_required: Whether wrapped in GraphQLNonNull
            is_list: Whether wrapped in GraphQLList

        Returns:
            VisitorControl to control traversal flow
        """
        return VisitorControl.CONTINUE

    def handle_enter_union(
        self,
        field_name: str,
        union_type: GraphQLUnionType,
        is_required: bool,
        is_list: bool,
    ) -> VisitorControl:
        """Handle a union type.

        Args:
            field_name: Name of the field with this type
            union_type: The union type
            is_required: Whether wrapped in GraphQLNonNull
            is_list: Whether wrapped in GraphQLList

        Returns:
            VisitorControl to control traversal flow
        """
        return VisitorControl.CONTINUE

    def handle_leave_union(
        self,
        field_name: str,
        union_type: GraphQLUnionType,
        is_required: bool,
        is_list: bool,
    ) -> VisitorControl:
        """Called when leaving a union type.

        Args:
            field_name: Name of the field with this type
            union_type: The union type
            is_required: Whether wrapped in GraphQLNonNull
            is_list: Whether wrapped in GraphQLList

        Returns:
            VisitorControl to control traversal flow
        """
        return VisitorControl.CONTINUE

    def handle_unknown(
        self,
        field_name: str,
        gql_type: t.Any,
        is_required: bool,
        is_list: bool,
    ) -> VisitorControl:
        """Handle an unknown or unsupported type.

        Args:
            field_name: Name of the field with this type
            gql_type: The unknown type
            is_required: Whether wrapped in GraphQLNonNull
            is_list: Whether wrapped in GraphQLList

        Returns:
            VisitorControl to control traversal flow
        """
        return VisitorControl.CONTINUE

    # Mutation field hooks (enter/leave pair)

    def handle_enter_mutation_field(
        self,
        field_name: str,
        field_def: GraphQLField,
        input_type: t.Optional[GraphQLInputObjectType],
        return_type: t.Any,
    ) -> VisitorControl:
        """Called when entering a mutation field during schema traversal.

        This hook is called for each field on the schema's Mutation type,
        providing access to the full field definition including arguments.

        Args:
            field_name: Name of the mutation (e.g., "createUser")
            field_def: Full field definition with description, directives, args
            input_type: The input argument type (extracted and unwrapped from 'input' arg),
                       or None if no 'input' argument exists
            return_type: The mutation's return/payload type (unwrapped)

        Returns:
            CONTINUE to traverse the return type's fields
            SKIP to skip traversing the return type (leave hook still called)
            STOP to halt traversal entirely
        """
        return VisitorControl.CONTINUE

    def handle_leave_mutation_field(
        self,
        field_name: str,
        field_def: GraphQLField,
        input_type: t.Optional[GraphQLInputObjectType],
        return_type: t.Any,
    ) -> VisitorControl:
        """Called when leaving a mutation field after visiting its return type.

        Args:
            field_name: Name of the mutation
            field_def: Full field definition
            input_type: The input argument type, or None
            return_type: The mutation's return/payload type (unwrapped)

        Returns:
            VisitorControl to control traversal flow
        """
        return VisitorControl.CONTINUE

    # Query field hooks (enter/leave pair)

    def handle_enter_query_field(
        self,
        field_name: str,
        field_def: GraphQLField,
        return_type: t.Any,
    ) -> VisitorControl:
        """Called when entering a query field during schema traversal.

        This hook is called for each field on the schema's Query type,
        providing access to the full field definition including arguments.

        Args:
            field_name: Name of the query (e.g., "getUser")
            field_def: Full field definition with description, directives, args
            return_type: The query's return type (unwrapped)

        Returns:
            CONTINUE to traverse the return type's fields
            SKIP to skip traversing the return type (leave hook still called)
            STOP to halt traversal entirely
        """
        return VisitorControl.CONTINUE

    def handle_leave_query_field(
        self,
        field_name: str,
        field_def: GraphQLField,
        return_type: t.Any,
    ) -> VisitorControl:
        """Called when leaving a query field after visiting its return type.

        Args:
            field_name: Name of the query
            field_def: Full field definition
            return_type: The query's return type (unwrapped)

        Returns:
            VisitorControl to control traversal flow
        """
        return VisitorControl.CONTINUE


class QueryDocumentVisitor(GraphQLSchemaTypeVisitor, t.Protocol):
    def handle_enter_operation(
        self,
        operation: QueryDocumentOperation,
    ) -> VisitorControl:
        """Called when entering a query document operation.

        Args:
            operation: The query document operation being entered

        Returns:
            VisitorControl to control traversal flow
        """
        return VisitorControl.CONTINUE

    def handle_leave_operation(
        self,
        operation: QueryDocumentOperation,
    ) -> VisitorControl:
        """Called when leaving a query document operation.

        Args:
            operation: The query document operation being left

        Returns:
            VisitorControl to control traversal flow
        """
        return VisitorControl.CONTINUE

    def handle_enter_fragment(
        self,
        fragment: QueryDocumentFragment,
    ) -> VisitorControl:
        """Called when entering a query document fragment.

        Args:
            fragment: The query document fragment being entered

        Returns:
            VisitorControl to control traversal flow
        """
        return VisitorControl.CONTINUE

    def handle_leave_fragment(
        self,
        fragment: QueryDocumentFragment,
    ) -> VisitorControl:
        """Called when leaving a query document fragment.

        Args:
            fragment: The query document fragment being left

        Returns:
            VisitorControl to control traversal flow
        """
        return VisitorControl.CONTINUE

    def handle_enter_variables(
        self,
        operation: QueryDocumentOperation,
    ) -> VisitorControl:
        """Called when entering a query document's variables section (before all variables).

        Args:
            operation: The query document operation being entered

        Returns:
            VisitorControl to control traversal flow
        """
        return VisitorControl.CONTINUE

    def handle_leave_variables(
        self,
        operation: QueryDocumentOperation,
    ) -> VisitorControl:
        """Called when leaving a query document's variables section (after all variables).

        Args:
            operation: The query document operation being left

        Returns:
            VisitorControl to control traversal flow
        """
        return VisitorControl.CONTINUE

    def handle_enter_variable_definition(
        self,
        operation: QueryDocumentOperation,
        variable: QueryDocumentVariable,
    ) -> VisitorControl:
        """Called when entering a single variable definition.

        Args:
            operation: The query document operation
            variable: The variable definition being entered

        Returns:
            VisitorControl to control traversal flow
        """
        return VisitorControl.CONTINUE

    def handle_leave_variable_definition(
        self,
        operation: QueryDocumentOperation,
        variable: QueryDocumentVariable,
    ) -> VisitorControl:
        """Called when leaving a single variable definition.

        Args:
            operation: The query document operation
            variable: The variable definition being left

        Returns:
            VisitorControl to control traversal flow
        """
        return VisitorControl.CONTINUE


class TraverserProtocol(t.Protocol):
    """Protocol for GraphQL schema traversers."""

    def walk(
        self,
        graphql_type: QueryDocument | SchemaType,
    ) -> None:
        """Walk a GraphQL type starting from the given field name.

        Args:
            graphql_type: The GraphQL type to visit
        """
        ...


GraphQLClientFactory = t.Callable[[], t.AsyncContextManager[AsyncGraphQLClient]]
