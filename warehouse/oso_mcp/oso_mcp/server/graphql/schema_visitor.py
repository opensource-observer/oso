"""Visitor pattern for traversing GraphQL schema types.

This module provides a traverser and visitor interface for GraphQL schema types.
The traverser handles all tree-walking logic, while visitors implement handlers
to process each type encountered during traversal.
"""

import logging
import typing as t

from graphql import (
    FieldNode,
    FragmentDefinitionNode,
    FragmentSpreadNode,
    GraphQLEnumType,
    GraphQLField,
    GraphQLInputField,
    GraphQLInputObjectType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLSchema,
    GraphQLType,
    GraphQLUnionType,
    InlineFragmentNode,
    SelectionSetNode,
)

from .types import GraphQLSchemaTypeVisitor, VisitorControl

logger = logging.getLogger(__name__)


class GraphQLSchemaTypeTraverser:
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
        visitor: "GraphQLSchemaTypeVisitor",
        schema: GraphQLSchema,
        selection_set: t.Optional[SelectionSetNode] = None,
        fragments: t.Optional[t.Dict[str, FragmentDefinitionNode]] = None,
    ):
        """Initialize traverser with a visitor and traversal configuration.

        Args:
            visitor: Visitor instance that will process types during traversal
            selection_set: Optional SelectionSet to filter fields (None = all fields)
            schema: GraphQL schema (required when selection_set is provided,
                   and for mutation/query field detection)
            fragments: Optional dict of fragment definitions by name (for resolving fragment spreads)
        """
        self._visitor = visitor
        self._selection_set = selection_set
        self._schema = schema
        self._fragments = fragments or {}

        # Track root type names for mutation/query field detection
        self._mutation_type_name: t.Optional[str] = None
        self._query_type_name: t.Optional[str] = None
        if schema.mutation_type:
            self._mutation_type_name = schema.mutation_type.name
        if schema.query_type:
            self._query_type_name = schema.query_type.name

    def visit(
        self,
        gql_type: GraphQLType,
        field_name: str = "",
        skip_root_hooks: bool = False,
        override_description: str | None = None,
    ) -> VisitorControl:
        """Visit a GraphQL type and recursively visit its nested types.

        This method handles all traversal logic.

        Args:
            gql_type: GraphQL type to visit (can be wrapped in NonNull/List)
            field_name: Name of the field being visited (empty string for root)
            skip_root_hooks: If True, skip enter/leave object hooks for this visit

        Returns:
            VisitorControl indicating how traversal ended
        """

        # Unwrap wrappers (NonNull, List) to get base type
        is_required = False
        is_list = False
        base_type = gql_type

        description = getattr(base_type, "description", None)
        if override_description is not None:
            description = override_description

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
                field_name, base_type, is_required, is_list, description
            )
        elif isinstance(base_type, GraphQLEnumType):
            return self._visitor.handle_enum(
                field_name, base_type, is_required, is_list, description
            )
        elif isinstance(base_type, GraphQLObjectType):
            return self._visit_object(
                field_name,
                base_type,
                is_required,
                is_list,
                skip_root_hooks,
                description,
            )
        elif isinstance(base_type, GraphQLInputObjectType):
            logger.debug("Visiting input object type: %s", base_type.name)
            return self._visit_input_object(field_name, base_type, is_required, is_list)
        elif isinstance(base_type, GraphQLInputField):
            return self._visit_input_field(field_name, base_type, is_required, is_list)
        elif isinstance(base_type, GraphQLUnionType):
            return self._visit_union(
                field_name, base_type, is_required, is_list, description
            )
        else:
            return self._visitor.handle_unknown(
                field_name, base_type, is_required, is_list
            )

    def _visit_union(
        self,
        field_name: str,
        union_type: GraphQLUnionType,
        is_required: bool,
        is_list: bool,
        description: str | None,
    ) -> VisitorControl:
        control = self._visitor.handle_enter_union(
            field_name, union_type, is_required, is_list, description
        )
        if control == VisitorControl.STOP:
            return VisitorControl.STOP
        elif control == VisitorControl.SKIP:
            return VisitorControl.CONTINUE

        # Build a map of inline fragment selection sets by type name
        inline_fragments_by_type: t.Dict[str, SelectionSetNode] = {}
        if self._selection_set:
            for selection in self._selection_set.selections:
                if isinstance(selection, InlineFragmentNode):
                    if selection.type_condition:
                        type_name = selection.type_condition.name.value
                        inline_fragments_by_type[type_name] = selection.selection_set

        # Visit each possible type in the union with its corresponding inline fragment selection set
        for possible_type in union_type.types:
            # Save current selection set
            prev_selection_set = self._selection_set

            # Use the inline fragment's selection set if available
            type_name = possible_type.name
            if type_name in inline_fragments_by_type:
                self._selection_set = inline_fragments_by_type[type_name]

            control = self.visit(
                possible_type,
                field_name=field_name,
            )

            # Restore previous selection set
            self._selection_set = prev_selection_set

            if control == VisitorControl.STOP:
                return VisitorControl.STOP

        control = self._visitor.handle_leave_union(
            field_name, union_type, is_required, is_list, description
        )
        return control

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
        skip_hooks: bool = False,
        description: str | None = None,
    ) -> VisitorControl:
        """Visit an object type (internal - handles traversal)."""
        # Call enter hook (skip if requested)
        if not skip_hooks:
            logger.debug(f"Visiting object: {object_type.name}")
            control = self._visitor.handle_enter_object(
                field_name, object_type, is_required, is_list, description
            )
            if control == VisitorControl.STOP:
                return VisitorControl.STOP
            elif control == VisitorControl.SKIP:
                # Skip this object's fields but continue with siblings
                return VisitorControl.CONTINUE

        logger.debug(
            f"Processing fields for object {object_type.name} with selection set: {self._selection_set}"
        )

        # Check if this is a mutation or query root type
        is_mutation_type = object_type.name == self._mutation_type_name
        is_query_type = object_type.name == self._query_type_name

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

        logger.debug(
            f"Visiting object {object_type.name} with fields: {[name for name, _, _ in fields_to_visit]}"
        )

        # Traverse each field
        for child_field_name, field_def, nested_selection_set in fields_to_visit:
            # Check if this is a mutation or query field and use special handlers
            if is_mutation_type:
                control = self._visit_mutation_field(child_field_name, field_def)
            elif is_query_type:
                control = self._visit_query_field(
                    child_field_name, field_def, nested_selection_set
                )
            else:
                # Regular field traversal
                # Save and update selection_set for this field's nested selections
                prev_selection_set = self._selection_set
                self._selection_set = nested_selection_set

                control = self.visit(field_def.type, field_name=child_field_name)

                self._selection_set = prev_selection_set

            if control == VisitorControl.STOP:
                return VisitorControl.STOP

        # Call leave hook (skip if requested)
        if not skip_hooks:
            control = self._visitor.handle_leave_object(
                field_name, object_type, is_required, is_list, description
            )
            return control

        return VisitorControl.CONTINUE

    def _unwrap_type(self, gql_type: t.Any) -> t.Any:
        """Unwrap NonNull and List wrappers to get the base type."""
        if isinstance(gql_type, GraphQLNonNull):
            gql_type = gql_type.of_type
        if isinstance(gql_type, GraphQLList):
            inner_type = gql_type.of_type
            if isinstance(inner_type, GraphQLNonNull):
                gql_type = inner_type.of_type
            else:
                gql_type = inner_type
        return gql_type

    def _visit_mutation_field(
        self,
        field_name: str,
        field_def: GraphQLField,
    ) -> VisitorControl:
        """Visit a mutation field with enter/leave hooks."""
        # Extract and unwrap input types from args

        # Unwrap return type
        return_type = self._unwrap_type(field_def.type)

        description = field_def.description

        # Enter mutation field
        control = self._visitor.handle_enter_mutation_field(
            field_name,
            field_def,
            return_type,
            description=description,
        )
        if control == VisitorControl.STOP:
            return VisitorControl.STOP
        if control == VisitorControl.SKIP:
            return VisitorControl.CONTINUE

        # Enter the arguments
        control = self._visitor.handle_enter_mutation_arguments(
            mutation_name=field_name,
        )
        if control == VisitorControl.STOP:
            return VisitorControl.STOP

        return_description = getattr(return_type, "description", None)

        # Visit each argument
        for arg_name, arg_def in field_def.args.items():
            arg_type = arg_def.type
            logger.debug(
                f"Visiting argument {arg_name} of type {arg_type} for mutation {field_name} with description: {arg_def.description}"
            )
            control = self.visit(
                arg_type,
                field_name=arg_name,
                # We need to override the description here because the argument
                # definition's description is lost when we visit its type (since
                # it's not a field/enum/object itself). Additionally, the
                # default description used by the graphql parser is highly
                # verbose and will not be useful for tool generation.
                override_description=arg_def.description or "",
            )
            if control == VisitorControl.STOP:
                return VisitorControl.STOP
        control = self._visitor.handle_leave_mutation_arguments(
            mutation_name=field_name,
        )
        if control == VisitorControl.STOP:
            return VisitorControl.STOP

        control = self._visitor.handle_enter_mutation_return_type(
            mutation_name=field_name, return_type=return_type
        )
        if control == VisitorControl.STOP:
            return VisitorControl.STOP

        # Visit return type as an object (allows visitor to build payload model via inherited hooks)
        if isinstance(return_type, GraphQLObjectType):
            logger.debug(
                f"Visiting mutation return type for {field_name}: {return_type.name}"
            )
            control = self._visit_object(
                field_name=field_name,
                object_type=return_type,
                is_required=True,
                is_list=False,
                description=return_description,
            )
            if control == VisitorControl.STOP:
                return VisitorControl.STOP

        control = self._visitor.handle_leave_mutation_return_type(
            mutation_name=field_name, return_type=return_type
        )
        if control == VisitorControl.STOP:
            return VisitorControl.STOP

        # Leave mutation field
        return self._visitor.handle_leave_mutation_field(
            field_name,
            field_def,
            return_type,
            description=description,
        )

    def _visit_query_field(
        self,
        field_name: str,
        field_def: GraphQLField,
        nested_selection_set: t.Optional[SelectionSetNode] = None,
    ) -> VisitorControl:
        """Visit a query field with enter/leave hooks."""
        # Enter query field
        control = self._visitor.handle_enter_query_field(
            field_name,
            field_def,
            field_def.type,
            getattr(field_def.type, "description", None),
        )
        if control == VisitorControl.STOP:
            return VisitorControl.STOP
        if control == VisitorControl.SKIP:
            # Still call leave hook even when skipping
            return self._visitor.handle_leave_query_field(
                field_name,
                field_def,
                field_def.type,
                getattr(field_def.type, "description", None),
            )

        # Save and update selection_set for this field's nested selections
        prev_selection_set = self._selection_set
        self._selection_set = nested_selection_set

        # Visit return type as a field (this will handle adding it to the parent context)
        control = self.visit(field_def.type, field_name=field_name)

        # Restore previous selection_set
        self._selection_set = prev_selection_set

        if control == VisitorControl.STOP:
            return VisitorControl.STOP

        # Leave query field
        return self._visitor.handle_leave_query_field(
            field_name,
            field_def,
            field_def.type,
            getattr(field_def.type, "description", None),
        )

    def _visit_input_object(
        self,
        field_name: str,
        input_type: GraphQLInputObjectType,
        is_required: bool,
        is_list: bool,
        description: str | None = None,
    ) -> VisitorControl:
        """Visit an input object type (internal - handles traversal)."""
        # Call enter hook
        control = self._visitor.handle_enter_input_object(
            field_name, input_type, is_required, is_list, description
        )
        if control == VisitorControl.STOP:
            return VisitorControl.STOP
        elif control == VisitorControl.SKIP:
            return VisitorControl.CONTINUE

        # Traverse each field (input objects don't use selection sets)
        for child_field_name, field in input_type.fields.items():
            control = self.visit(field, field_name=child_field_name)
            if control == VisitorControl.STOP:
                return VisitorControl.STOP

        # Call leave hook
        control = self._visitor.handle_leave_input_object(
            field_name, input_type, is_required, is_list, description
        )
        return control

    def _visit_input_field(
        self,
        field_name: str,
        field_type: GraphQLInputField,
        is_required: bool,
        is_list: bool,
    ) -> VisitorControl:
        """Visit an input field (internal - handles traversal)."""

        logger.debug(f"Visiting input field: {field_name}")

        # Unwrap wrappers (NonNull, List) to get base type
        is_required = False
        is_list = False
        base_type = field_type.type

        description = getattr(field_type, "description", None)

        logger.debug(f"Field description: {description}")

        # Unwrap NonNull wrapper
        if isinstance(base_type, GraphQLNonNull):
            is_required = True
            base_type = base_type.of_type

        # Unwrap List wrapper
        if isinstance(base_type, GraphQLList):
            is_list = True
            # Get the inner type (might be NonNull too)
            inner_type = base_type.of_type
            if isinstance(inner_type, GraphQLNonNull):
                base_type = inner_type.of_type
            else:
                base_type = inner_type

        match base_type:
            case GraphQLScalarType():
                return self._visitor.handle_scalar(
                    field_name,
                    base_type,
                    is_required,
                    is_list,
                    description,
                )
            case GraphQLEnumType():
                return self._visitor.handle_enum(
                    field_name,
                    base_type,
                    is_required,
                    is_list,
                    description,
                )
            case GraphQLInputObjectType():
                return self._visit_input_object(
                    field_name,
                    base_type,
                    is_required,
                    is_list,
                    description,
                )
            case _:
                return self._visitor.handle_unknown(
                    field_name, base_type, is_required, is_list
                )
