"""Parse client-side GraphQL documents containing queries and fragments."""

import os
import typing as t

from graphql import (
    DocumentNode,
    FragmentDefinitionNode,
    OperationDefinitionNode,
    OperationType,
    parse,
)

from .types import QueryDocument


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
