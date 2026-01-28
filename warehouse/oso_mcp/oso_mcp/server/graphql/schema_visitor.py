"""Visitor pattern for traversing GraphQL schema types.

This module provides a traverser and visitor interface for GraphQL schema types.
The traverser handles all tree-walking logic, while visitors implement handlers
to process each type encountered during traversal.
"""

import typing as t
from enum import Enum

from graphql import (
    FieldNode,
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
    SelectionSetNode,
)


class VisitorControl(Enum):
    """Control flow for visitor traversal.

    Returned from handle_* methods to control traversal behavior.
    """

    CONTINUE = "continue"  # Continue visiting normally
    SKIP = "skip"  # Skip children of this node (but continue with siblings)
    STOP = "stop"  # Stop all visiting immediately


class GraphQLSchemaTraverser:
    """Traverses GraphQL schema types and calls visitor methods.

    This class handles all the mechanics of walking the GraphQL type tree:
    - Unwrapping NonNull/List wrappers
    - Filtering fields based on selection sets
    - Expanding fragment spreads
    - Recursively visiting nested types
    - Respecting VisitorControl flow

    The traverser is stateless between visits - just give it a visitor and call visit().
    """

    def __init__(
        self,
        visitor: "GraphQLSchemaVisitor",
        selection_set: t.Optional[SelectionSetNode] = None,
        schema: t.Optional[GraphQLSchema] = None,
        fragments: t.Optional[t.Dict[str, t.Any]] = None,
    ):
        """Initialize traverser with a visitor and traversal configuration.

        Args:
            visitor: Visitor instance that will process types during traversal
            selection_set: Optional SelectionSet to filter fields (None = all fields)
            schema: GraphQL schema (required when selection_set is provided)
            fragments: Optional dict of fragment definitions by name (for resolving fragment spreads)
        """
        self._visitor = visitor
        self._selection_set = selection_set
        self._schema = schema
        self._fragments = fragments or {}

    def visit(
        self,
        gql_type: t.Any,
        field_name: str = "",
    ) -> VisitorControl:
        """Visit a GraphQL type and recursively visit its nested types.

        This method handles all traversal logic.

        Args:
            gql_type: GraphQL type to visit (can be wrapped in NonNull/List)
            field_name: Name of the field being visited (empty string for root)

        Returns:
            VisitorControl indicating how traversal ended
        """

        # Unwrap wrappers (NonNull, List) to get base type
        is_required = False
        is_list = False
        base_type = gql_type

        # Unwrap NonNull wrapper
        if isinstance(gql_type, GraphQLNonNull):
            is_required = True
            base_type = gql_type.of_type

        # Unwrap List wrapper
        if isinstance(base_type, GraphQLList):
            is_list = True
            # Get the inner type (might be NonNull too)
            inner_type = base_type.of_type
            if isinstance(inner_type, GraphQLNonNull):
                base_type = inner_type.of_type
            else:
                base_type = inner_type

        # Dispatch to appropriate handler based on base type
        if isinstance(base_type, GraphQLScalarType):
            return self._visitor.handle_scalar(
                field_name, base_type, is_required, is_list
            )
        elif isinstance(base_type, GraphQLEnumType):
            return self._visitor.handle_enum(
                field_name, base_type, is_required, is_list
            )
        elif isinstance(base_type, GraphQLObjectType):
            return self._visit_object(field_name, base_type, is_required, is_list)
        elif isinstance(base_type, GraphQLInputObjectType):
            return self._visit_input_object(field_name, base_type, is_required, is_list)
        elif isinstance(base_type, GraphQLUnionType):
            return self._visitor.handle_union(
                field_name, base_type, is_required, is_list
            )
        else:
            return self._visitor.handle_unknown(
                field_name, base_type, is_required, is_list
            )

    def _extract_selected_fields(
        self, selection_set: SelectionSetNode
    ) -> t.Dict[str, t.Optional[SelectionSetNode]]:
        """Extract field names and their nested selection sets from a SelectionSet.

        Handles FieldNode, FragmentSpreadNode, and InlineFragmentNode.

        Args:
            selection_set: Selection set to extract from

        Returns:
            Dict mapping field names to their nested selection sets (None if no nested selection)
        """
        fields: t.Dict[str, t.Optional[SelectionSetNode]] = {}

        for selection in selection_set.selections:
            if isinstance(selection, FieldNode):
                field_name = selection.name.value
                # Store the nested selection set (if any) for this field
                fields[field_name] = selection.selection_set
            elif isinstance(selection, FragmentSpreadNode):
                # Expand fragment spread by looking up the fragment definition
                fragment_name = selection.name.value
                if fragment_name in self._fragments:
                    fragment_def = self._fragments[fragment_name]
                    # Recursively extract fields from the fragment's selection set
                    fragment_fields = self._extract_selected_fields(
                        fragment_def.selection_set
                    )
                    # Merge fragment fields into our result
                    fields.update(fragment_fields)
            elif isinstance(selection, InlineFragmentNode):
                # Inline fragments have a selection set directly
                if selection.selection_set:
                    inline_fields = self._extract_selected_fields(
                        selection.selection_set
                    )
                    fields.update(inline_fields)

        return fields

    def _visit_object(
        self,
        field_name: str,
        object_type: GraphQLObjectType,
        is_required: bool,
        is_list: bool,
    ) -> VisitorControl:
        """Visit an object type (internal - handles traversal)."""
        # Call enter hook
        control = self._visitor.handle_enter_object(
            field_name, object_type, is_required, is_list
        )
        if control == VisitorControl.STOP:
            return VisitorControl.STOP
        elif control == VisitorControl.SKIP:
            # Skip this object's fields but continue with siblings
            return VisitorControl.CONTINUE

        # Determine which fields to visit based on selection_set
        if self._selection_set is not None:
            # Extract fields and their nested selection sets
            selected_fields = self._extract_selected_fields(self._selection_set)
            fields_to_visit = [
                (name, field, selected_fields.get(name))
                for name, field in object_type.fields.items()
                if name in selected_fields
            ]
        else:
            # Visit all fields with no selection set filtering
            fields_to_visit = [
                (name, field, None) for name, field in object_type.fields.items()
            ]

        # Traverse each field
        for child_field_name, field, nested_selection_set in fields_to_visit:
            # Visit the field's type recursively
            # Save and update selection_set for this field's nested selections
            prev_selection_set = self._selection_set
            self._selection_set = nested_selection_set

            control = self.visit(field.type, field_name=child_field_name)

            self._selection_set = prev_selection_set

            if control == VisitorControl.STOP:
                return VisitorControl.STOP

        # Call leave hook
        control = self._visitor.handle_leave_object(
            field_name, object_type, is_required, is_list
        )
        return control

    def _visit_input_object(
        self,
        field_name: str,
        input_type: GraphQLInputObjectType,
        is_required: bool,
        is_list: bool,
    ) -> VisitorControl:
        """Visit an input object type (internal - handles traversal)."""
        # Call enter hook
        control = self._visitor.handle_enter_input_object(
            field_name, input_type, is_required, is_list
        )
        if control == VisitorControl.STOP:
            return VisitorControl.STOP
        elif control == VisitorControl.SKIP:
            return VisitorControl.CONTINUE

        # Traverse each field (input objects don't use selection sets)
        for child_field_name, field in input_type.fields.items():
            control = self.visit(field.type, field_name=child_field_name)
            if control == VisitorControl.STOP:
                return VisitorControl.STOP

        # Call leave hook
        control = self._visitor.handle_leave_input_object(
            field_name, input_type, is_required, is_list
        )
        return control


class GraphQLSchemaVisitor:
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

    def handle_union(
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
