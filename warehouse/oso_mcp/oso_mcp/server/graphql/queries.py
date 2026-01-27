"""Query parsing, extraction, and execution for GraphQL."""

import logging
import os
import typing as t
from graphlib import TopologicalSorter

from graphql import (
    DocumentNode,
    FieldNode,
    FragmentDefinitionNode,
    FragmentSpreadNode,
    GraphQLObjectType,
    GraphQLSchema,
    InlineFragmentNode,
    OperationDefinitionNode,
    OperationType,
    SelectionSetNode,
    parse,
    print_ast,
)
from pydantic import BaseModel, create_model

from .pydantic_generator import PydanticModelGenerator
from .types import AsyncGraphQLClient, QueryDocument, QueryInfo

logger = logging.getLogger(__name__)


class QueryDocumentParser:
    """Parse GraphQL query documents from .graphql files."""

    def __init__(self, directory_path: str):
        """Initialize the parser with a directory path.

        Args:
            directory_path: Directory containing .graphql files

        Raises:
            FileNotFoundError: If path doesn't exist
            ValueError: If path is not a directory
        """
        if not os.path.exists(directory_path):
            raise FileNotFoundError(f"Path not found: {directory_path}")

        if not os.path.isdir(directory_path):
            raise ValueError(f"Path is not a directory: {directory_path}")

        self.directory_path = directory_path

    def parse_all(self) -> t.List[QueryDocument]:
        """Parse all .graphql files in the directory.

        Returns:
            List of QueryDocument objects, one per file

        Raises:
            GraphQLSyntaxError: If any file contains invalid GraphQL syntax
        """
        documents = []
        for filename in os.listdir(self.directory_path):
            if filename.endswith(".graphql"):
                file_path = os.path.join(self.directory_path, filename)
                doc = self._parse_file(file_path)
                if doc:
                    documents.append(doc)

        return documents

    def _parse_file(self, file_path: str) -> t.Optional[QueryDocument]:
        """Parse a single .graphql file.

        Args:
            file_path: Path to .graphql file

        Returns:
            QueryDocument or None if file contains no queries

        Raises:
            GraphQLSyntaxError: If file contains invalid GraphQL syntax
        """
        with open(file_path, "r") as f:
            content = f.read()

        # Parse the GraphQL document
        document = parse(content)

        # Extract operations and fragments
        operations = self._extract_operations(document)
        fragments = self._extract_fragments(document)

        # Skip files with no query operations
        if not operations:
            return None

        return QueryDocument(
            operations=operations, fragments=fragments, file_path=file_path
        )

    def _extract_operations(
        self, document: DocumentNode
    ) -> t.List[OperationDefinitionNode]:
        """Extract query operations from document.

        Args:
            document: Parsed GraphQL document

        Returns:
            List of query operation nodes
        """
        operations = []
        for definition in document.definitions:
            if isinstance(definition, OperationDefinitionNode):
                # Only include query operations (not mutations or subscriptions)
                if definition.operation == OperationType.QUERY:
                    operations.append(definition)

        return operations

    def _extract_fragments(
        self, document: DocumentNode
    ) -> t.Dict[str, FragmentDefinitionNode]:
        """Extract fragment definitions from document.

        Args:
            document: Parsed GraphQL document

        Returns:
            Dictionary mapping fragment names to fragment nodes
        """
        fragments = {}
        for definition in document.definitions:
            if isinstance(definition, FragmentDefinitionNode):
                fragment_name = definition.name.value
                fragments[fragment_name] = definition

        return fragments


class QueryExtractor:
    """Extract query information from parsed GraphQL query documents."""

    def extract_queries(
        self,
        schema: GraphQLSchema,
        query_docs: t.List[QueryDocument],
        model_generator: PydanticModelGenerator,
    ) -> t.List[QueryInfo]:
        """Extract all queries and generate their Pydantic models.

        Args:
            schema: GraphQL schema for type lookup
            query_docs: List of parsed query documents
            model_generator: Pydantic model generator instance

        Returns:
            List of QueryInfo objects

        Raises:
            ValueError: If a query operation lacks a name or schema has no Query type
        """
        queries = []

        # Get the Query type from schema
        query_type = schema.query_type
        if not query_type:
            raise ValueError("Schema does not have a Query type defined")

        for doc in query_docs:
            # First, generate Pydantic models for all fragments in dependency order
            # This ensures fragment dependencies are processed before fragments that use them
            self._generate_fragment_models_in_order(doc, schema, model_generator)

            # Now process each query operation
            for operation in doc.operations:
                # Require named operations for tool generation
                if not operation.name:
                    raise ValueError(
                        f"Anonymous queries are not supported. "
                        f"All query operations must have names in file: {doc.file_path}"
                    )

                query_name = operation.name.value

                # Build query string (includes fragment spreads, not inlined)
                query_string = self._build_query_string(operation, doc)

                # Generate variable input model
                variable_definitions = list(operation.variable_definitions) or []
                if variable_definitions:
                    input_model = model_generator.generate_model_from_variables(
                        query_name, variable_definitions
                    )
                else:
                    # No variables - create empty model
                    input_model = create_model(f"{query_name}Variables")

                # Generate response model from selection set
                # This will use fragment models where fragment spreads occur
                payload_model = model_generator.generate_model_from_selection_set(
                    query_name,
                    operation.selection_set,
                    query_type,
                    schema,
                    max_depth=100,  # Unlimited depth for hand-written queries
                )

                # Create QueryInfo
                query_info = QueryInfo(
                    name=query_name,
                    description=None,  # TODO: Extract from comments if available
                    query_string=query_string,
                    variable_definitions=variable_definitions,
                    input_model=input_model,
                    payload_model=payload_model,
                    selection_set=operation.selection_set,
                )

                queries.append(query_info)

        return queries

    def _build_query_string(
        self, operation: OperationDefinitionNode, doc: QueryDocument
    ) -> str:
        """Build complete query string with inlined fragments.

        Args:
            operation: Query operation node
            doc: Query document containing fragments

        Returns:
            GraphQL query string with fragments inlined
        """
        # Inline fragments in the operation's selection set
        inlined_selection_set = self._inline_fragments_in_selection_set(
            operation.selection_set, doc.fragments
        )

        # Create a new operation node with the inlined selection set
        inlined_operation = OperationDefinitionNode(
            operation=operation.operation,
            name=operation.name,
            variable_definitions=operation.variable_definitions,
            directives=operation.directives,
            selection_set=inlined_selection_set,
        )

        # Print only the operation (fragments are now inlined)
        return print_ast(inlined_operation)

    def _generate_fragment_models_in_order(
        self,
        doc: QueryDocument,
        schema: GraphQLSchema,
        model_generator: PydanticModelGenerator,
    ) -> None:
        """Generate Pydantic models for fragments in topological dependency order.

        This ensures that when a fragment uses another fragment, the dependency
        is generated first.

        Args:
            doc: Query document containing fragments
            schema: GraphQL schema for type lookup
            model_generator: Pydantic model generator instance

        Raises:
            ValueError: If circular fragment dependencies are detected
        """
        # Build dependency graph for topological sorting
        dependencies: t.Dict[str, t.Set[str]] = {}
        for fragment_name, fragment in doc.fragments.items():
            deps = self._get_fragment_dependencies(fragment.selection_set)
            dependencies[fragment_name] = deps

        # Use TopologicalSorter to get the correct order
        ts = TopologicalSorter(dependencies)
        try:
            sorted_fragments = list(ts.static_order())
        except ValueError as e:
            raise ValueError(
                f"Circular fragment dependencies detected in {doc.file_path}: {e}"
            )

        # Generate models in topological order
        for fragment_name in sorted_fragments:
            fragment = doc.fragments[fragment_name]
            # Get the type this fragment is on
            type_condition = fragment.type_condition.name.value
            fragment_type = schema.type_map.get(type_condition)

            # Ensure the fragment type is a GraphQLObjectType
            if fragment_type and isinstance(fragment_type, GraphQLObjectType):
                model_generator.generate_model_from_selection_set(
                    fragment_name,
                    fragment.selection_set,
                    fragment_type,
                    schema,
                    max_depth=100,  # Unlimited depth for hand-written query fragments
                )

    def _get_fragment_dependencies(self, selection_set: SelectionSetNode) -> t.Set[str]:
        """Get set of fragment names that this selection set depends on.

        Args:
            selection_set: Selection set to analyze

        Returns:
            Set of fragment names used in this selection set
        """
        dependencies: t.Set[str] = set()

        for selection in selection_set.selections:
            if isinstance(selection, FragmentSpreadNode):
                # This selection uses a fragment
                dependencies.add(selection.name.value)
            elif isinstance(selection, (FieldNode, InlineFragmentNode)):
                # Recursively check nested selections for FieldNode and InlineFragmentNode
                if selection.selection_set:
                    nested_deps = self._get_fragment_dependencies(
                        selection.selection_set
                    )
                    dependencies.update(nested_deps)

        return dependencies

    def _inline_fragments_in_selection_set(
        self,
        selection_set: SelectionSetNode,
        fragments: t.Dict[str, FragmentDefinitionNode],
    ) -> SelectionSetNode:
        """Inline fragment spreads in a selection set.

        Recursively replaces fragment spreads (...FragmentName) with the actual
        field selections from the fragment definition.

        Args:
            selection_set: Selection set that may contain fragment spreads
            fragments: Dictionary mapping fragment names to their definitions

        Returns:
            New selection set with all fragment spreads replaced by inlined fields
        """
        inlined_selections = []

        for selection in selection_set.selections:
            if isinstance(selection, FragmentSpreadNode):
                # Look up the fragment definition
                fragment_name = selection.name.value
                if fragment_name in fragments:
                    fragment = fragments[fragment_name]
                    # Recursively inline fragments in the fragment's selection set
                    inlined_fragment_selections = (
                        self._inline_fragments_in_selection_set(
                            fragment.selection_set,
                            fragments,
                        )
                    )
                    # Add all selections from the fragment
                    inlined_selections.extend(inlined_fragment_selections.selections)
                else:
                    # If fragment not found, error
                    raise ValueError(
                        f"Fragment '{fragment_name}' not found for inlining."
                    )

            elif isinstance(selection, FieldNode):
                # If the field has a nested selection set, recursively inline it
                if selection.selection_set:
                    inlined_nested = self._inline_fragments_in_selection_set(
                        selection.selection_set,
                        fragments,
                    )
                    # Create a new FieldNode with the inlined selection set
                    inlined_field = FieldNode(
                        name=selection.name,
                        alias=selection.alias,
                        arguments=selection.arguments,
                        directives=selection.directives,
                        selection_set=inlined_nested,
                    )
                    inlined_selections.append(inlined_field)
                else:
                    # No selection set, just add the field as-is
                    inlined_selections.append(selection)

            elif isinstance(selection, InlineFragmentNode):
                # Recursively inline fragments in the inline fragment's selection set
                if selection.selection_set:
                    inlined_nested = self._inline_fragments_in_selection_set(
                        selection.selection_set,
                        fragments,
                    )
                    # Create a new InlineFragmentNode with the inlined selection set
                    inlined_inline_fragment = InlineFragmentNode(
                        type_condition=selection.type_condition,
                        directives=selection.directives,
                        selection_set=inlined_nested,
                    )
                    inlined_selections.append(inlined_inline_fragment)
                else:
                    inlined_selections.append(selection)

        # Create and return a new SelectionSetNode with the inlined selections
        return SelectionSetNode(selections=tuple(inlined_selections))


class QueryExecutor:
    """Execute GraphQL queries via HTTP.

    Each executor instance is specific to a single query.
    """

    def __init__(
        self,
        endpoint: str,
        query_info: QueryInfo,
        graphql_client: AsyncGraphQLClient,
    ):
        """Initialize the query executor.

        Args:
            endpoint: GraphQL endpoint URL
            query_info: Query information
            graphql_client: Async GraphQL client (caller can configure authentication)
        """
        self.endpoint = endpoint
        self.query_info = query_info
        self.graphql_client = graphql_client

    async def execute_query(
        self,
        variables: BaseModel,
    ) -> BaseModel:
        """Execute query.

        Args:
            variables: Pydantic model instance with validated variable data

        Returns:
            Pydantic model instance with response data

        Raises:
            httpx.HTTPError: If HTTP request fails
            Exception: If GraphQL returns errors
        """
        logger.debug(f"Executing query {self.query_info.name} at {self.endpoint}")

        # Convert Pydantic model to dict for variables
        variables_dict = variables.model_dump()

        # Make HTTP request
        logger.debug(
            f"Sending request payload: {self.query_info.query_string} with variables {variables_dict}"
        )
        result = await self.graphql_client.execute(
            operation_name=self.query_info.name,
            query=self.query_info.query_string,
            variables=variables_dict,
            # self.endpoint, json=payload, headers=headers
        )
        logger.debug(f"Received response: {result}")

        # Check for GraphQL errors
        if "errors" in result:
            error_messages = [err.get("message", str(err)) for err in result["errors"]]
            raise Exception(f"GraphQL errors: {', '.join(error_messages)}")

        # Get query data
        data = result.get("data", {})

        # Convert to Pydantic model
        return self.query_info.payload_model.model_validate(data)
