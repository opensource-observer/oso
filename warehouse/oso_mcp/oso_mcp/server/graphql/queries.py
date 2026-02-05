"""Query parsing, extraction, and execution for GraphQL.

This module provides:
- QueryDocumentParser for parsing .graphql files
- QueryDocumentTraverser for walking QueryDocument with visitors
- QueryExtractor for extracting query information
- QueryExecutor for executing queries
"""

import json
import logging
import os
import typing as t
from graphlib import TopologicalSorter

from graphql import (
    DocumentNode,
    FieldNode,
    FragmentDefinitionNode,
    FragmentSpreadNode,
    GraphQLList,
    GraphQLNamedType,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLSchema,
    InlineFragmentNode,
    OperationDefinitionNode,
    OperationType,
    SelectionSetNode,
    parse,
    print_ast,
    type_from_ast,
)
from oso_mcp.server.graphql.schema_visitor import GraphQLSchemaTypeTraverser
from pydantic import BaseModel, Field

from .pydantic_generator import (
    PydanticModelBuildContext,
    PydanticModelVisitor,
    map_variable_scalar,
)
from .types import (
    AsyncGraphQLClient,
    QueryDocument,
    QueryDocumentField,
    QueryDocumentFragment,
    QueryDocumentFragmentSpread,
    QueryDocumentInlineFragment,
    QueryDocumentOperation,
    QueryDocumentSelection,
    QueryDocumentVariable,
    QueryDocumentVisitor,
    QueryInfo,
    SchemaType,
    TraverserProtocol,
    VisitorControl,
)

logger = logging.getLogger(__name__)


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
        """Build enriched QueryDocument from parsed AST."""
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
        """Build enriched fragments in topological dependency order."""
        if not raw_fragments:
            return {}

        # Build dependency graph
        dependencies: t.Dict[str, t.Set[str]] = {}
        for fragment_name, fragment in raw_fragments.items():
            deps = self._get_fragment_dependencies(fragment.selection_set)
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
                type_condition_name=type_condition_name,
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
            var_type = type_from_ast(self._schema, var_def.type)
            is_required, is_list, graphql_type = self._unwrap_type(var_type)

            default_value = None
            if var_def.default_value:
                default_value = var_def.default_value

            assert graphql_type is not None, (
                f"Unable to resolve type for variable '${var_name}'"
            )
            logger.debug(
                f"GraphQL Type for variable '${var_name}': {graphql_type} {type(graphql_type)}"
            )
            assert isinstance(graphql_type, GraphQLNamedType), (
                f"Variable '${var_name}' type is not a named type"
            )

            variables.append(
                QueryDocumentVariable(
                    ast_node=var_def,
                    name=var_name,
                    graphql_type=graphql_type,
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
        """Build enriched selections from AST selection set."""
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
        is_required, is_list, base_type = self._unwrap_type(field_def.type)

        # Build children if field has selection set and is object type
        children: t.List[QueryDocumentSelection] = []
        if node.selection_set:
            if isinstance(base_type, GraphQLObjectType):
                children = self._build_selections(
                    node.selection_set, base_type, fragments
                )

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
        type_condition: t.Optional[GraphQLObjectType] = None
        if node.type_condition:
            type_name = node.type_condition.name.value
            resolved_type = self._schema.type_map.get(type_name)
            if isinstance(resolved_type, GraphQLObjectType):
                type_condition = resolved_type

        child_parent = type_condition if type_condition else parent_type

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
        """Unwrap GraphQL type to get base type and flags."""
        is_required = False
        is_list = False

        if isinstance(gql_type, GraphQLNonNull):
            is_required = True
            gql_type = gql_type.of_type

        if isinstance(gql_type, GraphQLList):
            is_list = True
            inner_type = gql_type.of_type
            if isinstance(inner_type, GraphQLNonNull):
                inner_type = inner_type.of_type
            gql_type = inner_type

        return is_required, is_list, gql_type


class QueryDocumentTraverser(TraverserProtocol):
    """Traverses QueryDocument and calls GraphQLSchemaTypeVisitor methods.

    This traverser enables reusing PydanticModelVisitor (or any other
    GraphQLSchemaTypeVisitor implementation) for both:
    - GraphQLSchemaTypeTraverser (schema introspection, all fields)
    - QueryDocumentTraverser (query document, only selected fields)

    Example:
        visitor = PydanticModelVisitor(
            model_name="",  # Unused - create context manually for custom names
            parent_type=query_type,
            max_depth=100,
            use_context_prefix=True,
        )
        # For custom model names, create initial context before traversal
        ctx = PydanticModelBuildContext(
            model_name="GetUserResponse",
            parent_type=query_type,
            depth=0,
            context_prefix="GetUserResponse",
        )
        visitor._context_stack.append(ctx)
        traverser = QueryDocumentTraverser(visitor)
        traverser.traverse_operation(operation)
        model = visitor._type_registry["GetUserResponse"]
    """

    def __init__(
        self,
        visitor: QueryDocumentVisitor,
        schema: GraphQLSchema,
        expand_fragments: bool = True,
    ):
        """Initialize the traverser.

        Args:
            visitor: Visitor that will receive callbacks during traversal
            expand_fragments: If True, traverse into fragment spreads.
        """
        self._visitor = visitor
        self._expand_fragments = expand_fragments
        self._schema = schema
        self._visited_fragments: t.Set[str] = set()

    def walk(self, graphql_type: QueryDocument | SchemaType) -> None:
        """Traverse all operations and fragments in the document.

        Args:
            document: QueryDocument to traverse
        """
        assert isinstance(graphql_type, QueryDocument), (
            "QueryDocumentTraverser requires QueryDocument to walk"
        )
        document = graphql_type

        fragments_definitions: t.Dict[str, FragmentDefinitionNode] = {
            name: fragment.ast_node for name, fragment in document.fragments.items()
        }

        # Traverse fragments first in topographical order
        for fragment_name, fragment in document.fragments.items():
            control = self._traverse_fragment(fragment, fragments_definitions)
            if control == VisitorControl.STOP:
                return None

        for operation in document.operations:
            control = self._traverse_operation(operation, fragments_definitions)
            if control == VisitorControl.STOP:
                return None
        return None

    def _traverse_operation(
        self,
        operation: QueryDocumentOperation,
        fragments: t.Dict[str, FragmentDefinitionNode],
    ) -> VisitorControl:
        """Traverse a single operation."""
        logger.debug(f"Traversing operation: {operation.name}")
        self._visited_fragments = set()

        # Enter the root object type
        control = self._visitor.handle_enter_operation(
            operation=operation,
        )
        if control == VisitorControl.STOP:
            return VisitorControl.STOP
        if control == VisitorControl.SKIP:
            return VisitorControl.CONTINUE

        # Traverse the variables
        control = self._traverse_variables(operation)

        if control == VisitorControl.STOP:
            return VisitorControl.STOP

        # Delegate to the GraphQLSchemaTypeTraverser for field traversal
        # Skip root hooks so the Query/Mutation type fields are added directly
        # to the operation context instead of creating a nested Query/Mutation object
        traverser = GraphQLSchemaTypeTraverser(
            self._visitor,
            schema=self._schema,
            selection_set=operation.ast_node.selection_set,
            fragments=fragments,
        )
        logger.debug(
            f"Delegating to GraphQLSchemaTypeTraverser for operation: {operation.name}"
        )
        schema_start = self._schema.query_type
        if operation.operation_type == "mutation":
            schema_start = self._schema.mutation_type
        assert schema_start is not None, (
            f"Schema does not have a {operation.operation_type.title()} type defined"
        )
        control = traverser.visit(schema_start, field_name="", skip_root_hooks=True)

        # Leave the root object type
        return self._visitor.handle_leave_operation(
            operation=operation,
        )

    def _traverse_variables(self, operation: QueryDocumentOperation) -> VisitorControl:
        """Traverse variable definitions."""
        logger.debug(f"Traversing variables for operation: {operation.name}")
        control = self._visitor.handle_enter_variables(operation)
        if control == VisitorControl.STOP:
            return VisitorControl.STOP
        if control == VisitorControl.SKIP:
            return VisitorControl.CONTINUE
        control = self._traverse_variable_definitions(operation)
        if control == VisitorControl.STOP:
            return VisitorControl.STOP
        return self._visitor.handle_leave_variables(operation)

    def _traverse_variable_definitions(
        self, operation: QueryDocumentOperation
    ) -> VisitorControl:
        """Traverse variable definitions."""
        for variable in operation.variables:
            control = self._visitor.handle_enter_variable_definition(
                operation, variable
            )
            if control == VisitorControl.STOP:
                return VisitorControl.STOP
            if control == VisitorControl.SKIP:
                continue
            control = self._visitor.handle_leave_variable_definition(
                operation, variable
            )
            if control == VisitorControl.STOP:
                return VisitorControl.STOP
        return VisitorControl.CONTINUE

    def _traverse_fragment(
        self,
        fragment: QueryDocumentFragment,
        fragments: t.Dict[str, FragmentDefinitionNode],
    ) -> VisitorControl:
        """Traverse a fragment definition."""
        self._visited_fragments = set()

        control = self._visitor.handle_enter_fragment(
            fragment=fragment,
        )
        if control == VisitorControl.STOP:
            return VisitorControl.STOP
        if control == VisitorControl.SKIP:
            return VisitorControl.CONTINUE

        traverser = GraphQLSchemaTypeTraverser(
            self._visitor,
            schema=self._schema,
            selection_set=fragment.ast_node.selection_set,
            fragments=fragments,
        )
        logger.debug(
            f"Delegating to GraphQLSchemaTypeTraverser for fragment: {fragment.name} on type {fragment.type_condition_name}"
        )
        schema_start = fragment.type_condition
        assert schema_start is not None, (
            f"Schema does not have a {schema_start} type defined"
        )
        control = traverser.visit(schema_start, field_name="", skip_root_hooks=True)

        return self._visitor.handle_leave_fragment(
            fragment=fragment,
        )

    def _visit_field(self, field: QueryDocumentField) -> VisitorControl:
        """Visit a field - dispatches to appropriate visitor method based on type."""
        schema_type = field.schema_type
        field.ast_node.selection_set

        logger.debug(
            f"Delegating field visit to GraphQLSchemaTypeTraverser for field: {field.field_name} of type {schema_type}"
        )
        traverser = GraphQLSchemaTypeTraverser(
            self._visitor,
            schema=self._schema,
            selection_set=field.ast_node.selection_set,
        )
        return traverser.visit(schema_type, field.field_name)


class QueryCollectorVisitor(PydanticModelVisitor):
    """Collects QueryInfo from parsed GraphQL query documents.

    This class inherits from PydanticModelVisitor to leverage inherited
    hooks for building Pydantic models during QueryDocument traversal.
    Similar pattern to MutationCollectorVisitor.

    Example:
        parser = QueryDocumentParser(schema)
        query_docs = parser.parse_directory(client_schema_path)

        visitor = QueryCollectorVisitor(schema)
        traverser = QueryDocumentTraverser(visitor)
        traverser.walk(query_doc)
        queries = visitor.queries
    """

    def __init__(
        self,
        schema: GraphQLSchema,
        document: QueryDocument,
        ignore_unknown_types: bool = False,
    ):
        """Initialize the query collector visitor.

        Args:
            schema: GraphQL schema for type resolution
            ignore_unknown_types: If True, map unknown types to Any instead of raising error
        """
        query_type = schema.query_type
        if not query_type:
            raise ValueError("Schema does not have a Query type defined")

        # Initialize parent visitor with query-specific settings
        super().__init__(
            max_depth=100,  # Queries need deeper traversal than mutations
            use_context_prefix=True,  # Prefix nested types with operation name
            ignore_unknown_types=ignore_unknown_types,
        )
        self._schema = schema
        self._queries: t.List[QueryInfo] = []
        self._document = document
        # _type_registry is inherited from PydanticModelVisitor

    @property
    def queries(self) -> t.List[QueryInfo]:
        """Get the collected queries."""
        return self._queries

    def handle_enter_operation(
        self, operation: QueryDocumentOperation
    ) -> VisitorControl:
        """Handle entering an operation definition."""

        logger.debug(f"Starting operation: {operation.name}")
        self.start_model_context(operation.name)
        return VisitorControl.CONTINUE

    def handle_leave_operation(
        self, operation: QueryDocumentOperation
    ) -> VisitorControl:
        """Handle leaving an operation definition."""
        # Pop the root context and materialize the model
        logger.debug(f"Finishing operation: {operation.name}")
        operation_name = self.finish_context()
        payload_model = self.get_type(operation_name)

        # Build query string with inlined fragments
        query_string = self._build_query_string(operation, self._document)

        assert isinstance(payload_model, type), (
            "Payload model must be a Pydantic model class"
        )
        assert issubclass(payload_model, BaseModel), (
            "Payload model must be a subclass of BaseModel"
        )

        input_model = self.get_type(f"{operation.name}Variables")
        assert isinstance(input_model, type), "Input model must be a class"
        assert issubclass(input_model, BaseModel), (
            "Input model must be a subclass of BaseModel"
        )

        # Create and collect QueryInfo
        query_info = QueryInfo(
            name=operation.name,
            description=None,
            query_string=query_string,
            input_model=input_model,
            payload_model=payload_model,
            selection_set=operation.ast_node.selection_set,
        )
        self._queries.append(query_info)

        return VisitorControl.CONTINUE

    def handle_enter_variables(
        self,
        operation: QueryDocumentOperation,
    ) -> VisitorControl:
        """Handle entering a variable definition."""
        # Generate variable model (uses static method, not traversal)

        self.start_model_context(f"{operation.name}Variables", no_prefix=True)
        logger.debug(f"Starting variable model context: {operation.name}Variables")

        return VisitorControl.CONTINUE

    def handle_leave_variables(
        self,
        operation: QueryDocumentOperation,
    ) -> VisitorControl:
        finished_model = self.finish_context()
        logger.debug(f"Finished variable model: {finished_model}")
        return VisitorControl.CONTINUE

    def handle_enter_variable_definition(
        self,
        operation: QueryDocumentOperation,
        variable: QueryDocumentVariable,
    ) -> VisitorControl:
        """Handle entering a variable definition."""
        logger.debug(
            f"Processing variable definition: {variable.name} of type {variable.graphql_type} (required={variable.is_required}, list={variable.is_list})"
        )

        # Add field to current context for this variable
        var_name = variable.name
        var_type = variable.graphql_type
        is_required = variable.is_required
        is_list = variable.is_list
        current_context = self.require_model_context("add variable definition")

        logger.debug(f"Context name {current_context.type_name}")
        # TODO we need to handle input object types here as well

        python_type = map_variable_scalar(var_type.name)
        field_info = Field()
        if is_list:
            python_type = t.List[python_type]
        if not is_required:
            python_type = t.Optional[python_type]
            field_info = Field(default=None)

        current_context.add_field(
            field_name=var_name,
            python_type=python_type,
            field_info=field_info,
        )

        logger.debug(f"Added variable field: {var_name} with type {python_type}")
        return VisitorControl.CONTINUE

    def handle_leave_variable_definition(
        self,
        operation: QueryDocumentOperation,
        variable: QueryDocumentVariable,
    ) -> VisitorControl:
        """Handle leaving a variable definition."""
        return VisitorControl.CONTINUE

    def handle_enter_fragment(self, fragment: QueryDocumentFragment) -> VisitorControl:
        """Handle entering a fragment definition."""
        model_name = f"{fragment.name}Response"
        ctx = PydanticModelBuildContext(
            type_name=model_name,
            depth=0,
        )
        self._context_stack.append(ctx)
        return VisitorControl.CONTINUE

    def handle_leave_fragment(self, fragment: QueryDocumentFragment) -> VisitorControl:
        """Handle leaving a fragment definition."""
        return VisitorControl.CONTINUE

    def _build_query_string(
        self, operation: QueryDocumentOperation, doc: QueryDocument
    ) -> str:
        """Build complete query string with inlined fragments."""
        raw_fragments = {name: frag.ast_node for name, frag in doc.fragments.items()}

        inlined_selection_set = self._inline_fragments_in_selection_set(
            operation.ast_node.selection_set, raw_fragments
        )

        inlined_operation = OperationDefinitionNode(
            operation=operation.ast_node.operation,
            name=operation.ast_node.name,
            variable_definitions=operation.ast_node.variable_definitions,
            directives=operation.ast_node.directives,
            selection_set=inlined_selection_set,
        )

        return print_ast(inlined_operation)

    def _inline_fragments_in_selection_set(
        self,
        selection_set: SelectionSetNode,
        fragments: t.Dict[str, t.Any],
    ) -> SelectionSetNode:
        """Inline fragment spreads in a selection set."""
        inlined_selections = []

        for selection in selection_set.selections:
            if isinstance(selection, FragmentSpreadNode):
                fragment_name = selection.name.value
                if fragment_name in fragments:
                    fragment = fragments[fragment_name]
                    inlined_fragment_selections = (
                        self._inline_fragments_in_selection_set(
                            fragment.selection_set,
                            fragments,
                        )
                    )
                    inlined_selections.extend(inlined_fragment_selections.selections)
                else:
                    raise ValueError(
                        f"Fragment '{fragment_name}' not found for inlining."
                    )

            elif isinstance(selection, FieldNode):
                if selection.selection_set:
                    inlined_nested = self._inline_fragments_in_selection_set(
                        selection.selection_set,
                        fragments,
                    )
                    inlined_field = FieldNode(
                        name=selection.name,
                        alias=selection.alias,
                        arguments=selection.arguments,
                        directives=selection.directives,
                        selection_set=inlined_nested,
                    )
                    inlined_selections.append(inlined_field)
                else:
                    inlined_selections.append(selection)

            elif isinstance(selection, InlineFragmentNode):
                if selection.selection_set:
                    inlined_nested = self._inline_fragments_in_selection_set(
                        selection.selection_set,
                        fragments,
                    )
                    inlined_inline_fragment = InlineFragmentNode(
                        type_condition=selection.type_condition,
                        directives=selection.directives,
                        selection_set=inlined_nested,
                    )
                    inlined_selections.append(inlined_inline_fragment)
                else:
                    inlined_selections.append(selection)

        return SelectionSetNode(selections=tuple(inlined_selections))


class QueryExecutor:
    """Execute GraphQL queries via HTTP."""

    def __init__(
        self,
        endpoint: str,
        query_info: QueryInfo,
        graphql_client: AsyncGraphQLClient,
    ):
        """Initialize the query executor."""
        self.endpoint = endpoint
        self.query_info = query_info
        self.graphql_client = graphql_client

    async def execute_query(
        self,
        variables: BaseModel,
    ) -> BaseModel:
        """Execute query."""
        logger.debug(f"Executing query {self.query_info.name} at {self.endpoint}")

        variables_dict = variables.model_dump(exclude_none=True)

        logger.debug(
            f"Sending request payload: {self.query_info.query_string} with variables {variables_dict}"
        )
        result = await self.graphql_client.execute(
            operation_name=self.query_info.name,
            query=self.query_info.query_string,
            variables=variables_dict,
        )
        logger.debug(f"Received response: {result}")

        if "errors" in result:
            error_messages = [err.get("message", str(err)) for err in result["errors"]]
            raise Exception(f"GraphQL errors: {', '.join(error_messages)}")

        data = result.get("data", {})

        logger.debug(f"Response data: {json.dumps(data, indent=2)}")
        logger.debug(
            "Payload model json schema: %s",
            json.dumps(self.query_info.payload_model.model_json_schema(), indent=2),
        )

        return self.query_info.payload_model.model_validate(data)
