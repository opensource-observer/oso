"""Query parsing, extraction, and execution for GraphQL.

This module provides:
- QueryDocumentParser for parsing .graphql files
- QueryDocumentTraverser for walking QueryDocument with visitors
- QueryExtractor for extracting query information
- QueryExecutor for executing queries
"""

import logging
import os
import typing as t
from graphlib import TopologicalSorter

from graphql import (
    DocumentNode,
    FieldNode,
    FragmentDefinitionNode,
    FragmentSpreadNode,
    GraphQLEnumType,
    GraphQLInputObjectType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLSchema,
    GraphQLUnionType,
    InlineFragmentNode,
    OperationDefinitionNode,
    OperationType,
    SelectionSetNode,
    parse,
    print_ast,
)
from pydantic import BaseModel, create_model

from .pydantic_generator import PydanticModelGenerator, PydanticModelVisitor
from .schema_visitor import GraphQLSchemaTypeVisitor, VisitorControl
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
    QueryInfo,
    SchemaType,
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
            is_required, is_list, _ = self._unwrap_type(var_def.type)

            default_value = None
            if var_def.default_value:
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


# =============================================================================
# QueryDocumentTraverser
# =============================================================================


class QueryDocumentTraverser:
    """Traverses QueryDocument and calls GraphQLSchemaTypeVisitor methods.

    This traverser enables reusing PydanticModelVisitor (or any other
    GraphQLSchemaTypeVisitor implementation) for both:
    - GraphQLSchemaTypeTraverser (schema introspection, all fields)
    - QueryDocumentTraverser (query document, only selected fields)

    Example:
        visitor = PydanticModelVisitor(
            model_name="GetUserResponse",
            parent_type=query_type,
            max_depth=100,
            use_context_prefix=True,
        )
        traverser = QueryDocumentTraverser(visitor)
        traverser.traverse_operation(operation)
        model = visitor._type_registry["GetUserResponse"]
    """

    def __init__(
        self,
        visitor: GraphQLSchemaTypeVisitor,
        expand_fragments: bool = True,
    ):
        """Initialize the traverser.

        Args:
            visitor: Visitor that will receive callbacks during traversal
            expand_fragments: If True, traverse into fragment spreads.
        """
        self._visitor = visitor
        self._expand_fragments = expand_fragments
        self._visited_fragments: t.Set[str] = set()

    def traverse(self, document: QueryDocument) -> VisitorControl:
        """Traverse all operations in the document."""
        for operation in document.operations:
            control = self.traverse_operation(operation)
            if control == VisitorControl.STOP:
                return VisitorControl.STOP
        return VisitorControl.CONTINUE

    def traverse_operation(self, operation: QueryDocumentOperation) -> VisitorControl:
        """Traverse a single operation."""
        self._visited_fragments = set()

        # Enter the root object type
        control = self._visitor.handle_enter_object(
            field_name="",
            object_type=operation.root_type,
            is_required=True,
            is_list=False,
        )
        if control == VisitorControl.STOP:
            return VisitorControl.STOP
        if control == VisitorControl.SKIP:
            return VisitorControl.CONTINUE

        # Visit children
        for child in operation.children:
            control = self._visit_selection(child)
            if control == VisitorControl.STOP:
                return VisitorControl.STOP

        # Leave the root object type
        return self._visitor.handle_leave_object(
            field_name="",
            object_type=operation.root_type,
            is_required=True,
            is_list=False,
        )

    def traverse_fragment(self, fragment: QueryDocumentFragment) -> VisitorControl:
        """Traverse a fragment definition."""
        self._visited_fragments = set()

        control = self._visitor.handle_enter_object(
            field_name="",
            object_type=fragment.type_condition,
            is_required=True,
            is_list=False,
        )
        if control == VisitorControl.STOP:
            return VisitorControl.STOP
        if control == VisitorControl.SKIP:
            return VisitorControl.CONTINUE

        for child in fragment.children:
            control = self._visit_selection(child)
            if control == VisitorControl.STOP:
                return VisitorControl.STOP

        return self._visitor.handle_leave_object(
            field_name="",
            object_type=fragment.type_condition,
            is_required=True,
            is_list=False,
        )

    def _visit_selection(self, selection: QueryDocumentSelection) -> VisitorControl:
        """Dispatch to appropriate visit method based on selection type."""
        if isinstance(selection, QueryDocumentField):
            return self._visit_field(selection)
        elif isinstance(selection, QueryDocumentFragmentSpread):
            return self._visit_fragment_spread(selection)
        elif isinstance(selection, QueryDocumentInlineFragment):
            return self._visit_inline_fragment(selection)
        return VisitorControl.CONTINUE

    def _visit_field(self, field: QueryDocumentField) -> VisitorControl:
        """Visit a field - dispatches to appropriate visitor method based on type."""
        schema_type = field.schema_type

        if isinstance(schema_type, GraphQLScalarType):
            return self._visitor.handle_scalar(
                field.field_name, schema_type, field.is_required, field.is_list
            )
        elif isinstance(schema_type, GraphQLEnumType):
            return self._visitor.handle_enum(
                field.field_name, schema_type, field.is_required, field.is_list
            )
        elif isinstance(schema_type, GraphQLObjectType):
            control = self._visitor.handle_enter_object(
                field.field_name, schema_type, field.is_required, field.is_list
            )
            if control == VisitorControl.STOP:
                return VisitorControl.STOP
            if control == VisitorControl.SKIP:
                return VisitorControl.CONTINUE

            for child in field.children:
                control = self._visit_selection(child)
                if control == VisitorControl.STOP:
                    return VisitorControl.STOP

            return self._visitor.handle_leave_object(
                field.field_name, schema_type, field.is_required, field.is_list
            )
        elif isinstance(schema_type, GraphQLUnionType):
            return self._visitor.handle_union(
                field.field_name, schema_type, field.is_required, field.is_list
            )
        elif isinstance(schema_type, GraphQLInputObjectType):
            control = self._visitor.handle_enter_input_object(
                field.field_name, schema_type, field.is_required, field.is_list
            )
            if control == VisitorControl.STOP:
                return VisitorControl.STOP
            if control == VisitorControl.SKIP:
                return VisitorControl.CONTINUE
            return self._visitor.handle_leave_input_object(
                field.field_name, schema_type, field.is_required, field.is_list
            )
        else:
            return self._visitor.handle_unknown(
                field.field_name, schema_type, field.is_required, field.is_list
            )

    def _visit_fragment_spread(
        self, spread: QueryDocumentFragmentSpread
    ) -> VisitorControl:
        """Visit a fragment spread by traversing into the referenced fragment."""
        if not self._expand_fragments:
            return VisitorControl.CONTINUE

        if spread.fragment_name in self._visited_fragments:
            return VisitorControl.CONTINUE

        self._visited_fragments.add(spread.fragment_name)

        for child in spread.fragment.children:
            control = self._visit_selection(child)
            if control == VisitorControl.STOP:
                return VisitorControl.STOP

        return VisitorControl.CONTINUE

    def _visit_inline_fragment(
        self, inline: QueryDocumentInlineFragment
    ) -> VisitorControl:
        """Visit an inline fragment's children."""
        for child in inline.children:
            control = self._visit_selection(child)
            if control == VisitorControl.STOP:
                return VisitorControl.STOP
        return VisitorControl.CONTINUE


class QueryExtractor:
    """Extract query information from parsed GraphQL query documents."""

    def extract_queries(
        self,
        schema: GraphQLSchema,
        query_docs: t.List[QueryDocument],
        model_generator: PydanticModelGenerator,
    ) -> t.List[QueryInfo]:
        """Extract all queries and generate their Pydantic models."""
        queries = []

        query_type = schema.query_type
        if not query_type:
            raise ValueError("Schema does not have a Query type defined")

        for doc in query_docs:
            self._generate_fragment_models(doc, model_generator)

            for operation in doc.operations:
                if not operation.name:
                    raise ValueError(
                        f"Anonymous queries are not supported. "
                        f"All query operations must have names in file: {doc.file_path}"
                    )

                query_name = operation.name
                query_string = self._build_query_string(operation, doc)

                variable_definitions = [v.ast_node for v in operation.variables]
                if variable_definitions:
                    input_model = model_generator.generate_model_from_variables(
                        query_name, variable_definitions
                    )
                else:
                    input_model = create_model(f"{query_name}Variables")

                payload_model = self._generate_payload_model(operation, query_name, doc)

                query_info = QueryInfo(
                    name=query_name,
                    description=None,
                    query_string=query_string,
                    variable_definitions=variable_definitions,
                    input_model=input_model,
                    payload_model=payload_model,
                    selection_set=operation.ast_node.selection_set,
                )

                queries.append(query_info)

        return queries

    def _generate_fragment_models(
        self,
        doc: QueryDocument,
        model_generator: PydanticModelGenerator,
    ) -> None:
        """Generate Pydantic models for all fragments in the document."""
        for fragment_name, fragment in doc.fragments.items():
            visitor = PydanticModelVisitor(
                model_name=f"{fragment_name}Response",
                parent_type=fragment.type_condition,
                max_depth=100,
                use_context_prefix=True,
                ignore_unknown_types=model_generator._ignore_unknown_types,
            )
            traverser = QueryDocumentTraverser(visitor, expand_fragments=True)
            traverser.traverse_fragment(fragment)

            if f"{fragment_name}Response" in visitor._type_registry:
                model_generator._type_registry[f"{fragment_name}Response"] = (
                    visitor._type_registry[f"{fragment_name}Response"]
                )

    def _generate_payload_model(
        self,
        operation: QueryDocumentOperation,
        query_name: str,
        doc: QueryDocument,
    ) -> t.Type[BaseModel]:
        """Generate Pydantic model for operation response."""
        model_name = f"{query_name}Response"

        visitor = PydanticModelVisitor(
            model_name=model_name,
            parent_type=operation.root_type,
            max_depth=100,
            use_context_prefix=True,
            ignore_unknown_types=False,
        )
        traverser = QueryDocumentTraverser(visitor, expand_fragments=True)
        traverser.traverse_operation(operation)

        return visitor._type_registry[model_name]  # type: ignore

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

        return self.query_info.payload_model.model_validate(data)
