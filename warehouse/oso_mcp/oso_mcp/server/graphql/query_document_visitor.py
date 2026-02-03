"""Traverser for walking QueryDocument and calling visitor methods.

This module provides the QueryDocumentTraverser which traverses an enriched
QueryDocument and calls methods on a GraphQLSchemaTypeVisitor. This enables
reusing the same visitor (like PydanticModelVisitor) for both schema-based
traversal and query document traversal.
"""

import typing as t

from graphql import (
    GraphQLEnumType,
    GraphQLInputObjectType,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLUnionType,
)

from .query_document import (
    QueryDocument,
    QueryDocumentField,
    QueryDocumentFragment,
    QueryDocumentFragmentSpread,
    QueryDocumentInlineFragment,
    QueryDocumentOperation,
    QueryDocumentSelection,
)
from .schema_visitor import GraphQLSchemaTypeVisitor, VisitorControl


class QueryDocumentTraverser:
    """Traverses QueryDocument and calls GraphQLSchemaTypeVisitor methods.

    This traverser enables reusing PydanticModelVisitor (or any other
    GraphQLSchemaTypeVisitor implementation) for both:
    - GraphQLSchemaTypeTraverser (schema introspection, all fields)
    - QueryDocumentTraverser (query document, only selected fields)

    The traverser walks the enriched QueryDocument tree and calls the
    appropriate visitor methods (handle_scalar, handle_enter_object, etc.)
    based on each field's schema type.

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
                              If False, skip fragment content.
        """
        self._visitor = visitor
        self._expand_fragments = expand_fragments
        self._visited_fragments: t.Set[str] = set()

    def traverse(self, document: QueryDocument) -> VisitorControl:
        """Traverse all operations in the document.

        Args:
            document: Enriched QueryDocument to traverse

        Returns:
            VisitorControl indicating how traversal ended
        """
        for operation in document.operations:
            control = self.traverse_operation(operation)
            if control == VisitorControl.STOP:
                return VisitorControl.STOP
        return VisitorControl.CONTINUE

    def traverse_operation(self, operation: QueryDocumentOperation) -> VisitorControl:
        """Traverse a single operation.

        Calls handle_enter_object for the root type (Query/Mutation/Subscription),
        then visits all selected fields, then calls handle_leave_object.

        Args:
            operation: Operation to traverse

        Returns:
            VisitorControl indicating how traversal ended
        """
        # Reset visited fragments for each operation
        self._visited_fragments = set()

        # Enter the root object type (Query, Mutation, etc.)
        control = self._visitor.handle_enter_object(
            field_name="",  # Root has no field name
            object_type=operation.root_type,
            is_required=True,
            is_list=False,
        )
        if control == VisitorControl.STOP:
            return VisitorControl.STOP
        if control == VisitorControl.SKIP:
            return VisitorControl.CONTINUE

        # Visit children (the selected fields)
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
        """Traverse a fragment definition.

        Calls handle_enter_object for the type condition, then visits
        all selected fields, then calls handle_leave_object.

        Args:
            fragment: Fragment to traverse

        Returns:
            VisitorControl indicating how traversal ended
        """
        # Reset visited fragments
        self._visited_fragments = set()

        # Enter the fragment's type condition
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

        # Visit children
        for child in fragment.children:
            control = self._visit_selection(child)
            if control == VisitorControl.STOP:
                return VisitorControl.STOP

        # Leave the fragment's type condition
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
            # Enter object
            control = self._visitor.handle_enter_object(
                field.field_name, schema_type, field.is_required, field.is_list
            )
            if control == VisitorControl.STOP:
                return VisitorControl.STOP
            if control == VisitorControl.SKIP:
                return VisitorControl.CONTINUE

            # Visit children
            for child in field.children:
                control = self._visit_selection(child)
                if control == VisitorControl.STOP:
                    return VisitorControl.STOP

            # Leave object
            return self._visitor.handle_leave_object(
                field.field_name, schema_type, field.is_required, field.is_list
            )
        elif isinstance(schema_type, GraphQLUnionType):
            return self._visitor.handle_union(
                field.field_name, schema_type, field.is_required, field.is_list
            )
        elif isinstance(schema_type, GraphQLInputObjectType):
            # Input objects in output context (rare)
            control = self._visitor.handle_enter_input_object(
                field.field_name, schema_type, field.is_required, field.is_list
            )
            if control == VisitorControl.STOP:
                return VisitorControl.STOP
            if control == VisitorControl.SKIP:
                return VisitorControl.CONTINUE

            # Input objects don't have children in query context
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
        """Visit a fragment spread by traversing into the referenced fragment.

        If expand_fragments is False, this is a no-op.
        Tracks visited fragments to prevent infinite recursion from cycles.
        """
        if not self._expand_fragments:
            return VisitorControl.CONTINUE

        # Prevent infinite recursion
        if spread.fragment_name in self._visited_fragments:
            return VisitorControl.CONTINUE

        self._visited_fragments.add(spread.fragment_name)

        # Visit the fragment's children directly (don't call enter/leave
        # on the fragment's type condition since we're already inside
        # a compatible type context)
        for child in spread.fragment.children:
            control = self._visit_selection(child)
            if control == VisitorControl.STOP:
                return VisitorControl.STOP

        return VisitorControl.CONTINUE

    def _visit_inline_fragment(
        self, inline: QueryDocumentInlineFragment
    ) -> VisitorControl:
        """Visit an inline fragment's children.

        Note: Inline fragments don't trigger enter/leave object hooks
        since they're type refinements within an existing object context.
        """
        for child in inline.children:
            control = self._visit_selection(child)
            if control == VisitorControl.STOP:
                return VisitorControl.STOP
        return VisitorControl.CONTINUE
