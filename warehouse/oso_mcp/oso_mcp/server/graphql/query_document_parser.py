"""Parser for building enriched QueryDocument from .graphql files.

This module provides the QueryDocumentParser which parses .graphql files
and builds enriched QueryDocument instances with schema type resolution.
"""

import os
import typing as t
from graphlib import TopologicalSorter

from graphql import (
    DocumentNode,
    FieldNode,
    FragmentDefinitionNode,
    FragmentSpreadNode,
    GraphQLInputObjectType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLSchema,
    InlineFragmentNode,
    OperationDefinitionNode,
    OperationType,
    SelectionSetNode,
    parse,
)

from .query_document import (
    QueryDocument,
    QueryDocumentField,
    QueryDocumentFragment,
    QueryDocumentFragmentSpread,
    QueryDocumentInlineFragment,
    QueryDocumentOperation,
    QueryDocumentSelection,
    QueryDocumentVariable,
    SchemaType,
)


class QueryDocumentParser:
    """Parses .graphql files into enriched QueryDocument with schema resolution.

    This parser reads GraphQL query files and builds a fully enriched
    QueryDocument where all AST nodes are linked to their corresponding
    schema types. Fragment spreads are resolved to their definitions,
    and type wrappers (NonNull, List) are unwrapped to is_required/is_list flags.
    """

    def __init__(self, schema: GraphQLSchema):
        """Initialize the parser with a GraphQL schema.

        Args:
            schema: GraphQL schema for type resolution
        """
        self._schema = schema

    def parse_file(self, file_path: str) -> t.Optional[QueryDocument]:
        """Parse a single .graphql file into QueryDocument.

        Args:
            file_path: Path to .graphql file

        Returns:
            QueryDocument or None if file contains no operations

        Raises:
            GraphQLSyntaxError: If file contains invalid GraphQL syntax
            FileNotFoundError: If file doesn't exist
        """
        with open(file_path, "r") as f:
            content = f.read()

        ast = parse(content)
        return self._build_document(ast, file_path)

    def parse_directory(self, directory_path: str) -> t.List[QueryDocument]:
        """Parse all .graphql files in directory.

        Args:
            directory_path: Directory containing .graphql files

        Returns:
            List of QueryDocument objects (only files with operations)

        Raises:
            FileNotFoundError: If directory doesn't exist
            ValueError: If path is not a directory
        """
        if not os.path.exists(directory_path):
            raise FileNotFoundError(f"Path not found: {directory_path}")

        if not os.path.isdir(directory_path):
            raise ValueError(f"Path is not a directory: {directory_path}")

        docs = []
        for filename in os.listdir(directory_path):
            if filename.endswith(".graphql"):
                file_path = os.path.join(directory_path, filename)
                doc = self.parse_file(file_path)
                if doc and doc.operations:
                    docs.append(doc)
        return docs

    def _build_document(
        self, ast: DocumentNode, file_path: str
    ) -> t.Optional[QueryDocument]:
        """Build enriched QueryDocument from parsed AST.

        Args:
            ast: Parsed GraphQL document AST
            file_path: Source file path

        Returns:
            QueryDocument or None if no operations found
        """
        # Extract raw AST nodes
        raw_operations = self._extract_raw_operations(ast)
        raw_fragments = self._extract_raw_fragments(ast)

        # Skip files with no operations
        if not raw_operations:
            return None

        # Build fragments first in topological order (dependencies before dependents)
        fragments = self._build_fragments(raw_fragments)

        # Build operations with fragment references
        operations = self._build_operations(raw_operations, fragments)

        return QueryDocument(
            file_path=file_path,
            operations=operations,
            fragments=fragments,
        )

    def _extract_raw_operations(
        self, ast: DocumentNode
    ) -> t.List[OperationDefinitionNode]:
        """Extract operation definition nodes from AST."""
        operations = []
        for definition in ast.definitions:
            if isinstance(definition, OperationDefinitionNode):
                # Include query, mutation, and subscription operations
                operations.append(definition)
        return operations

    def _extract_raw_fragments(
        self, ast: DocumentNode
    ) -> t.Dict[str, FragmentDefinitionNode]:
        """Extract fragment definition nodes from AST."""
        fragments = {}
        for definition in ast.definitions:
            if isinstance(definition, FragmentDefinitionNode):
                fragment_name = definition.name.value
                fragments[fragment_name] = definition
        return fragments

    def _build_fragments(
        self, raw_fragments: t.Dict[str, FragmentDefinitionNode]
    ) -> t.Dict[str, QueryDocumentFragment]:
        """Build enriched fragments in topological dependency order.

        Fragments that depend on other fragments are built after their
        dependencies. This ensures fragment spreads can be resolved.

        Args:
            raw_fragments: Dictionary of raw fragment AST nodes

        Returns:
            Dictionary of enriched QueryDocumentFragment objects

        Raises:
            ValueError: If circular fragment dependencies are detected
        """
        if not raw_fragments:
            return {}

        # Build dependency graph
        dependencies: t.Dict[str, t.Set[str]] = {}
        for fragment_name, fragment in raw_fragments.items():
            deps = self._get_fragment_dependencies(fragment.selection_set)
            # Only include dependencies that are in our fragment set
            dependencies[fragment_name] = deps & set(raw_fragments.keys())

        # Topological sort
        ts = TopologicalSorter(dependencies)
        try:
            sorted_names = list(ts.static_order())
        except ValueError as e:
            raise ValueError(f"Circular fragment dependencies detected: {e}")

        # Build fragments in order
        fragments: t.Dict[str, QueryDocumentFragment] = {}
        for fragment_name in sorted_names:
            raw_fragment = raw_fragments[fragment_name]

            # Resolve type condition
            type_condition_name = raw_fragment.type_condition.name.value
            type_condition = self._schema.type_map.get(type_condition_name)

            if not isinstance(type_condition, GraphQLObjectType):
                raise ValueError(
                    f"Fragment '{fragment_name}' type condition '{type_condition_name}' "
                    f"is not an object type"
                )

            # Build children (can reference already-built fragments)
            children = self._build_selections(
                raw_fragment.selection_set, type_condition, fragments
            )

            fragments[fragment_name] = QueryDocumentFragment(
                ast_node=raw_fragment,
                name=fragment_name,
                type_condition=type_condition,
                children=children,
            )

        return fragments

    def _get_fragment_dependencies(self, selection_set: SelectionSetNode) -> t.Set[str]:
        """Get set of fragment names that this selection set depends on."""
        dependencies: t.Set[str] = set()

        for selection in selection_set.selections:
            if isinstance(selection, FragmentSpreadNode):
                dependencies.add(selection.name.value)
            elif isinstance(selection, (FieldNode, InlineFragmentNode)):
                if selection.selection_set:
                    nested_deps = self._get_fragment_dependencies(
                        selection.selection_set
                    )
                    dependencies.update(nested_deps)

        return dependencies

    def _build_operations(
        self,
        raw_operations: t.List[OperationDefinitionNode],
        fragments: t.Dict[str, QueryDocumentFragment],
    ) -> t.List[QueryDocumentOperation]:
        """Build enriched operations with resolved root types."""
        operations = []

        for raw_op in raw_operations:
            # Determine root type based on operation type
            if raw_op.operation == OperationType.QUERY:
                root_type = self._schema.query_type
                op_type = "query"
            elif raw_op.operation == OperationType.MUTATION:
                root_type = self._schema.mutation_type
                op_type = "mutation"
            elif raw_op.operation == OperationType.SUBSCRIPTION:
                root_type = self._schema.subscription_type
                op_type = "subscription"
            else:
                continue

            if root_type is None:
                raise ValueError(
                    f"Schema does not have a {op_type.title()} type defined"
                )

            # Get operation name (may be None for anonymous operations)
            op_name = raw_op.name.value if raw_op.name else ""

            # Build variables
            variables = self._build_variables(raw_op)

            # Build children
            children = self._build_selections(
                raw_op.selection_set, root_type, fragments
            )

            operations.append(
                QueryDocumentOperation(
                    ast_node=raw_op,
                    name=op_name,
                    operation_type=op_type,
                    root_type=root_type,
                    variables=variables,
                    children=children,
                )
            )

        return operations

    def _build_variables(
        self, operation: OperationDefinitionNode
    ) -> t.List[QueryDocumentVariable]:
        """Build enriched variable definitions."""
        if not operation.variable_definitions:
            return []

        variables = []
        for var_def in operation.variable_definitions:
            var_name = var_def.variable.name.value

            # Unwrap type
            is_required, is_list, _ = self._unwrap_type(var_def.type)

            # Get default value if present
            default_value = None
            if var_def.default_value:
                # TODO: Parse default value properly
                default_value = var_def.default_value

            variables.append(
                QueryDocumentVariable(
                    ast_node=var_def,
                    name=var_name,
                    graphql_type=var_def.type,
                    is_required=is_required,
                    is_list=is_list,
                    default_value=default_value,
                )
            )

        return variables

    def _build_selections(
        self,
        selection_set: SelectionSetNode,
        parent_type: GraphQLObjectType,
        fragments: t.Dict[str, QueryDocumentFragment],
    ) -> t.List[QueryDocumentSelection]:
        """Build enriched selections from AST selection set.

        Args:
            selection_set: AST selection set
            parent_type: Parent GraphQL object type for field resolution
            fragments: Already-built fragments for spread resolution

        Returns:
            List of enriched selection objects
        """
        selections: t.List[QueryDocumentSelection] = []

        for selection in selection_set.selections:
            if isinstance(selection, FieldNode):
                selections.append(self._build_field(selection, parent_type, fragments))
            elif isinstance(selection, FragmentSpreadNode):
                selections.append(self._build_fragment_spread(selection, fragments))
            elif isinstance(selection, InlineFragmentNode):
                selections.append(
                    self._build_inline_fragment(selection, parent_type, fragments)
                )

        return selections

    def _build_field(
        self,
        node: FieldNode,
        parent_type: GraphQLObjectType,
        fragments: t.Dict[str, QueryDocumentFragment],
    ) -> QueryDocumentField:
        """Build enriched field with schema type resolution."""
        field_name = node.name.value

        # Handle __typename special field
        if field_name == "__typename":
            from graphql import GraphQLString

            return QueryDocumentField(
                ast_node=node,
                field_name=field_name,
                alias=node.alias.value if node.alias else None,
                schema_type=GraphQLString,
                is_required=True,
                is_list=False,
                children=[],
            )

        # Get field definition from parent type
        if field_name not in parent_type.fields:
            raise ValueError(
                f"Field '{field_name}' not found on type '{parent_type.name}'"
            )

        field_def = parent_type.fields[field_name]

        # Unwrap type to get base type and flags
        is_required, is_list, base_type = self._unwrap_type(field_def.type)

        # Build children if field has selection set and is object/input type
        children: t.List[QueryDocumentSelection] = []
        if node.selection_set:
            if isinstance(base_type, GraphQLObjectType):
                children = self._build_selections(
                    node.selection_set, base_type, fragments
                )
            elif isinstance(base_type, GraphQLInputObjectType):
                # Input types in output context - unusual but handle it
                pass

        return QueryDocumentField(
            ast_node=node,
            field_name=field_name,
            alias=node.alias.value if node.alias else None,
            schema_type=base_type,
            is_required=is_required,
            is_list=is_list,
            children=children,
        )

    def _build_fragment_spread(
        self,
        node: FragmentSpreadNode,
        fragments: t.Dict[str, QueryDocumentFragment],
    ) -> QueryDocumentFragmentSpread:
        """Build enriched fragment spread with resolved reference."""
        fragment_name = node.name.value

        if fragment_name not in fragments:
            raise ValueError(f"Fragment '{fragment_name}' not found")

        return QueryDocumentFragmentSpread(
            ast_node=node,
            fragment_name=fragment_name,
            fragment=fragments[fragment_name],
        )

    def _build_inline_fragment(
        self,
        node: InlineFragmentNode,
        parent_type: GraphQLObjectType,
        fragments: t.Dict[str, QueryDocumentFragment],
    ) -> QueryDocumentInlineFragment:
        """Build enriched inline fragment with resolved type condition."""
        # Resolve type condition (may be None for typeless inline fragments)
        type_condition: t.Optional[GraphQLObjectType] = None
        if node.type_condition:
            type_name = node.type_condition.name.value
            resolved_type = self._schema.type_map.get(type_name)
            if isinstance(resolved_type, GraphQLObjectType):
                type_condition = resolved_type

        # Use type condition or parent type for child resolution
        child_parent = type_condition if type_condition else parent_type

        # Build children
        children: t.List[QueryDocumentSelection] = []
        if node.selection_set:
            children = self._build_selections(
                node.selection_set, child_parent, fragments
            )

        return QueryDocumentInlineFragment(
            ast_node=node,
            type_condition=type_condition,
            children=children,
        )

    def _unwrap_type(self, gql_type: t.Any) -> t.Tuple[bool, bool, SchemaType]:
        """Unwrap GraphQL type to get base type and flags.

        Args:
            gql_type: GraphQL type (possibly wrapped in NonNull/List)

        Returns:
            Tuple of (is_required, is_list, base_type)
        """
        is_required = False
        is_list = False

        # Unwrap NonNull
        if isinstance(gql_type, GraphQLNonNull):
            is_required = True
            gql_type = gql_type.of_type

        # Unwrap List
        if isinstance(gql_type, GraphQLList):
            is_list = True
            inner_type = gql_type.of_type
            # Handle NonNull inside List
            if isinstance(inner_type, GraphQLNonNull):
                inner_type = inner_type.of_type
            gql_type = inner_type

        return is_required, is_list, gql_type
