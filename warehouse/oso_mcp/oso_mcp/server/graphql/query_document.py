"""Query document types with schema type resolution.

This module defines the enriched QueryDocument representation that links
GraphQL AST nodes to their corresponding schema types. This replaces the
previous raw AST-based QueryDocument.
"""

from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

from graphql import (
    FieldNode,
    FragmentDefinitionNode,
    FragmentSpreadNode,
    GraphQLEnumType,
    GraphQLInputObjectType,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLUnionType,
    InlineFragmentNode,
    OperationDefinitionNode,
    VariableDefinitionNode,
)

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
    graphql_type: t.Any  # The original wrapped type for reference
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
    type_condition: GraphQLObjectType
    children: t.List[QueryDocumentSelection] = field(default_factory=list)


@dataclass
class QueryDocument:
    """Parsed GraphQL document with all types resolved from schema.

    This is the enriched representation of a .graphql file that contains:
    - Operations (queries, mutations, subscriptions) with resolved root types
    - Fragments with resolved type conditions
    - All fields with their schema types resolved and unwrapped

    This replaces the previous QueryDocument that held raw AST nodes.
    """

    file_path: str
    operations: t.List[QueryDocumentOperation] = field(default_factory=list)
    fragments: t.Dict[str, QueryDocumentFragment] = field(default_factory=dict)
