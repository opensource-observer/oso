"""Query parsing, extraction, and execution for GraphQL."""

import logging
import typing as t

from graphql import (
    FieldNode,
    FragmentSpreadNode,
    GraphQLSchema,
    InlineFragmentNode,
    OperationDefinitionNode,
    SelectionSetNode,
    print_ast,
)
from pydantic import BaseModel, create_model

from .pydantic_generator import PydanticModelGenerator, PydanticModelVisitor
from .query_document import QueryDocument, QueryDocumentOperation
from .query_document_visitor import QueryDocumentTraverser
from .types import AsyncGraphQLClient, QueryInfo

logger = logging.getLogger(__name__)


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
            query_docs: List of parsed query documents (enriched format)
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
            # First, generate Pydantic models for all fragments in the document
            # Fragments are already in dependency order from the parser
            self._generate_fragment_models(doc, model_generator)

            # Now process each query operation
            for operation in doc.operations:
                # Require named operations for tool generation
                if not operation.name:
                    raise ValueError(
                        f"Anonymous queries are not supported. "
                        f"All query operations must have names in file: {doc.file_path}"
                    )

                query_name = operation.name

                # Build query string with inlined fragments
                query_string = self._build_query_string(operation, doc)

                # Generate variable input model
                variable_definitions = [v.ast_node for v in operation.variables]
                if variable_definitions:
                    input_model = model_generator.generate_model_from_variables(
                        query_name, variable_definitions
                    )
                else:
                    # No variables - create empty model
                    input_model = create_model(f"{query_name}Variables")

                # Generate response model using the traverser and visitor
                payload_model = self._generate_payload_model(operation, query_name, doc)

                # Create QueryInfo
                query_info = QueryInfo(
                    name=query_name,
                    description=None,  # TODO: Extract from comments if available
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
        """Generate Pydantic models for all fragments in the document.

        Args:
            doc: Query document containing fragments
            model_generator: Pydantic model generator instance
        """
        for fragment_name, fragment in doc.fragments.items():
            # Use the visitor/traverser pattern to generate fragment model
            visitor = PydanticModelVisitor(
                model_name=f"{fragment_name}Response",
                parent_type=fragment.type_condition,
                max_depth=100,
                use_context_prefix=True,
                ignore_unknown_types=model_generator._ignore_unknown_types,
            )
            traverser = QueryDocumentTraverser(visitor, expand_fragments=True)
            traverser.traverse_fragment(fragment)

            # Store the generated model in model_generator's registry for later use
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
        """Generate Pydantic model for operation response.

        Uses the QueryDocumentTraverser with PydanticModelVisitor to generate
        the model based on the operation's selection set.

        Args:
            operation: Operation to generate model for
            query_name: Name of the query (for model naming)
            doc: Query document (for fragment lookup)

        Returns:
            Generated Pydantic model class
        """
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
        """Build complete query string with inlined fragments.

        Args:
            operation: Query operation
            doc: Query document containing fragments

        Returns:
            GraphQL query string with fragments inlined
        """
        # Get raw fragment definitions for inlining
        raw_fragments = {name: frag.ast_node for name, frag in doc.fragments.items()}

        # Inline fragments in the operation's selection set
        inlined_selection_set = self._inline_fragments_in_selection_set(
            operation.ast_node.selection_set, raw_fragments
        )

        # Create a new operation node with the inlined selection set
        inlined_operation = OperationDefinitionNode(
            operation=operation.ast_node.operation,
            name=operation.ast_node.name,
            variable_definitions=operation.ast_node.variable_definitions,
            directives=operation.ast_node.directives,
            selection_set=inlined_selection_set,
        )

        # Print only the operation (fragments are now inlined)
        return print_ast(inlined_operation)

    def _inline_fragments_in_selection_set(
        self,
        selection_set: SelectionSetNode,
        fragments: t.Dict[str, t.Any],
    ) -> SelectionSetNode:
        """Inline fragment spreads in a selection set.

        Recursively replaces fragment spreads (...FragmentName) with the actual
        field selections from the fragment definition.

        Args:
            selection_set: Selection set that may contain fragment spreads
            fragments: Dictionary mapping fragment names to their AST definitions

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
        variables_dict = variables.model_dump(exclude_none=True)

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
