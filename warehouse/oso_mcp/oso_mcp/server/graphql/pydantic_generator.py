"""Pydantic model generator for GraphQL types."""

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
    SelectionSetNode,
    VariableDefinitionNode,
)
from pydantic import BaseModel, Field, create_model


class UnsetNested(BaseModel):
    """Marker for unset nested fields in Pydantic models."""

    pass


class PydanticModelGenerator:
    """Dynamically generate Pydantic models from GraphQL types."""

    def __init__(self):
        """Initialize the model generator with a type registry."""
        self._type_registry: dict[str, t.Type[BaseModel] | Enum] = {}

    def generate_input_model(
        self, input_type: GraphQLInputObjectType
    ) -> t.Type[BaseModel]:
        """Create Pydantic model from GraphQL input type.

        Args:
            input_type: GraphQL input object type

        Returns:
            Dynamically created Pydantic model class
        """
        type_name = input_type.name

        # Return registered type if available
        if type_name in self._type_registry:
            return self._type_registry[type_name]  # type: ignore

        fields = {}
        for field_name, field in input_type.fields.items():
            # When generating input models, max depth is ignored due to
            # potentially required nested inputs
            field_result = self._create_pydantic_field(
                field_name, field.type, max_depth=1, context_prefix=type_name
            )
            # Skip fields that return None (exceeded max_depth)
            if field_result is None:
                continue
            python_type, field_info = field_result
            fields[field_name] = (python_type, field_info)

        # Create the model
        model = create_model(type_name, **fields)
        self._type_registry[type_name] = model
        return model

    def generate_payload_model(
        self, payload_type: GraphQLObjectType, max_depth: int = 2
    ) -> t.Type[BaseModel]:
        """Create Pydantic model from GraphQL payload type.

        Args:
            payload_type: GraphQL object type for mutation payload

        Returns:
            Dynamically created Pydantic model class
        """
        return self._get_or_create_model(
            payload_type, max_depth=max_depth, context_prefix=""
        )

    def _get_or_create_model(
        self, gql_type: GraphQLObjectType, max_depth: int, context_prefix
    ) -> t.Type[BaseModel]:
        """Recursively create or get Pydantic model for GraphQL object type."""
        type_name = f"{context_prefix}{gql_type.name}"

        # Return registered type if available
        if type_name in self._type_registry:
            return self._type_registry[type_name]  # type: ignore

        fields = {}
        for field_name, field in gql_type.fields.items():
            field_result = self._create_pydantic_field(
                field_name,
                field.type,
                max_depth=max_depth - 1,
                context_prefix=type_name,
            )
            # Skip fields that return None (exceeded max_depth)
            if field_result is None:
                continue
            python_type, field_info = field_result
            fields[field_name] = (python_type, field_info)

        # Create the model
        model = create_model(type_name, **fields)
        self._type_registry[type_name] = model
        return model

    def generate_enum(self, enum_type: GraphQLEnumType) -> Enum:
        """Create Python Enum from GraphQL enum type.

        Args:
            enum_type: GraphQL enum type

        Returns:
            Dynamically created Enum class
        """
        type_name = enum_type.name

        # Return registered enum if available
        if type_name in self._type_registry:
            return self._type_registry[type_name]  # type: ignore

        # Create enum members
        enum_members = {name: value for name, value in enum_type.values.items()}

        # Create the enum
        enum_klass = Enum(type_name, enum_members)
        self._type_registry[type_name] = enum_klass
        return enum_klass

    def _create_pydantic_field(
        self, name: str, gql_type: t.Any, max_depth: int, context_prefix: str
    ) -> tuple[t.Any, t.Any] | None:
        """Create Pydantic field definition from GraphQL type.

        Args:
            name: Field name
            gql_type: GraphQL type
            max_depth: Maximum depth for nested types
            context_prefix: Prefix for type names

        Returns:
            Tuple of (python_type, field_info) or None if field should be excluded
        """
        # Unwrap NonNull and List wrappers
        is_required = isinstance(gql_type, GraphQLNonNull)
        if is_required:
            gql_type = gql_type.of_type

        is_list = isinstance(gql_type, GraphQLList)
        if is_list:
            inner_type = gql_type.of_type
            # Handle list of non-null items
            if isinstance(inner_type, GraphQLNonNull):
                inner_type = inner_type.of_type
            inner_python_type = self._map_graphql_type_to_python(
                name,
                inner_type,
                max_depth=max_depth,
                context_prefix=f"{context_prefix}Item",
            )
            if isinstance(inner_python_type, UnsetNested):
                # Skip fields with nested types beyond max_depth
                return None
            python_type = list[inner_python_type]
        else:
            python_type = self._map_graphql_type_to_python(
                name, gql_type, max_depth=max_depth, context_prefix=context_prefix
            )

        if isinstance(python_type, UnsetNested):
            # Skip fields with nested types beyond max_depth
            return None

        # Make optional if not required
        if not is_required:
            python_type = t.Optional[python_type]
            field_info = Field(default=None)
        else:
            field_info = Field()

        return python_type, field_info

    def _map_graphql_type_to_python(
        self, name: str, field_type: t.Any, max_depth: int, context_prefix: str
    ) -> t.Any:
        """Convert GraphQL type to Python type annotation.

        Args:
            field_type: GraphQL type

        Returns:
            Python type
        """
        if isinstance(field_type, GraphQLScalarType):
            scalar_name = field_type.name
            scalar_map = {
                "String": str,
                "Int": int,
                "Float": float,
                "Boolean": bool,
                "ID": str,
                "JSON": t.Any,
                "DateTime": str,  # ISO 8601 format
            }
            return scalar_map.get(scalar_name, t.Any)

        if isinstance(field_type, GraphQLEnumType):
            # Generate and return enum type
            return self.generate_enum(field_type)

        if isinstance(field_type, GraphQLInputObjectType):
            # Recursively generate model for nested input types
            return self.generate_input_model(field_type)

        if isinstance(field_type, GraphQLObjectType):
            # Recursively generate model for nested object types
            if max_depth > 0:
                return self._get_or_create_model(
                    field_type, max_depth=max_depth, context_prefix=context_prefix
                )
            return UnsetNested()

        # Default to Any for unknown types
        return t.Any

    def generate_model_from_variables(
        self, operation_name: str, variable_definitions: t.List[VariableDefinitionNode]
    ) -> t.Type[BaseModel]:
        """Generate Pydantic model from query variable definitions.

        Args:
            operation_name: Name of the query operation (for model naming)
            variable_definitions: List of variable definition nodes from query

        Returns:
            Dynamically created Pydantic model class for variables
        """
        type_name = f"{operation_name}Variables"

        # Return registered type if available
        if type_name in self._type_registry:
            return self._type_registry[type_name]  # type: ignore

        fields = {}
        for var_def in variable_definitions:
            var_name = var_def.variable.name.value
            var_type = var_def.type

            # Parse the variable type to determine Python type and required status
            is_required = False
            if isinstance(var_type, GraphQLNonNull):
                is_required = True
                var_type = var_type.of_type

            # Handle list types
            if isinstance(var_type, GraphQLList):
                inner_type = var_type.of_type
                # Handle list of non-null items
                if isinstance(inner_type, GraphQLNonNull):
                    inner_type = inner_type.of_type
                # Get inner type name
                inner_type_name = (
                    inner_type.name if hasattr(inner_type, "name") else str(inner_type)
                )
                python_type = list[self._map_scalar_name_to_python(inner_type_name)]
            else:
                type_name_str = getattr(var_type, "name", str(var_type))
                python_type = self._map_scalar_name_to_python(type_name_str)

            # Make optional if not required
            if not is_required:
                python_type = t.Optional[python_type]
                field_info = Field(default=None)
            else:
                field_info = Field()

            fields[var_name] = (python_type, field_info)

        # Create the model
        model = create_model(f"{operation_name}Variables", **fields)
        self._type_registry[f"{operation_name}Variables"] = model
        return model

    def _map_scalar_name_to_python(self, scalar_name: str) -> t.Any:
        """Map GraphQL scalar type name to Python type.

        Args:
            scalar_name: GraphQL scalar type name

        Returns:
            Python type
        """
        scalar_map = {
            "String": str,
            "Int": int,
            "Float": float,
            "Boolean": bool,
            "ID": str,
            "JSON": t.Any,
            "DateTime": str,
        }
        return scalar_map.get(scalar_name, t.Any)

    def generate_model_from_selection_set(
        self,
        operation_name: str,
        selection_set: SelectionSetNode,
        parent_type: GraphQLObjectType,
        schema: GraphQLSchema,
        max_depth: int = 2,
    ) -> t.Type[BaseModel]:
        """Generate Pydantic model from GraphQL selection set.

        Args:
            operation_name: Name of the query operation (for model naming)
            selection_set: Selection set from query
            parent_type: The GraphQL type being selected from
            schema: GraphQL schema for type lookup
            max_depth: Maximum nesting depth for object types

        Returns:
            Dynamically created Pydantic model class for response
        """
        type_name = f"{operation_name}Response"

        # Return registered type if available
        if type_name in self._type_registry:
            return self._type_registry[type_name]  # type: ignore

        fields = self._build_fields_from_selection_set(
            selection_set, parent_type, schema, max_depth, context_prefix=type_name
        )

        # Create the model
        model = create_model(type_name, **fields)  # type: ignore # pyright: ignore
        self._type_registry[type_name] = model
        return model

    def _build_fields_from_selection_set(
        self,
        selection_set: SelectionSetNode,
        parent_type: GraphQLObjectType,
        schema: GraphQLSchema,
        max_depth: int,
        context_prefix: str,
    ) -> dict[str, tuple[t.Any, t.Any]]:
        """Recursively build Pydantic field definitions from selection set.

        Args:
            selection_set: Selection set node
            parent_type: Parent GraphQL type
            schema: GraphQL schema
            max_depth: Maximum nesting depth
            context_prefix: Prefix for nested type names

        Returns:
            Dictionary of field definitions
        """
        fields = {}

        for selection in selection_set.selections:
            if isinstance(selection, FragmentSpreadNode):
                # Handle fragment spreads - include fields from the fragment model
                fragment_name = selection.name.value
                fragment_model_name = f"{fragment_name}Response"

                # Look up the fragment model in the registry
                if fragment_model_name in self._type_registry:
                    fragment_model = self._type_registry[fragment_model_name]
                    # Ensure it's a BaseModel (not an Enum)
                    if isinstance(fragment_model, type) and issubclass(
                        fragment_model, BaseModel
                    ):
                        # Spread the fragment's fields into this model
                        for (
                            field_name,
                            field_info,
                        ) in fragment_model.model_fields.items():
                            # Copy the field definition from the fragment model
                            fields[field_name] = (field_info.annotation, Field())
                # If fragment model not found, skip (it should have been generated earlier)

            elif isinstance(selection, FieldNode):
                field_name = selection.name.value

                # Get field definition from parent type
                if field_name not in parent_type.fields:
                    continue

                field_def = parent_type.fields[field_name]
                field_type = field_def.type

                # Unwrap NonNull
                is_required = isinstance(field_type, GraphQLNonNull)
                if is_required:
                    field_type = field_type.of_type

                # Unwrap List
                is_list = isinstance(field_type, GraphQLList)
                if is_list:
                    inner_type = field_type.of_type
                    if isinstance(inner_type, GraphQLNonNull):
                        inner_type = inner_type.of_type
                    field_type = inner_type

                # Determine Python type
                if isinstance(field_type, GraphQLObjectType):
                    # Nested object - recursively build model if we have selection set
                    if selection.selection_set and max_depth > 0:
                        nested_type_name = f"{context_prefix}{field_type.name}"
                        if nested_type_name in self._type_registry:
                            python_type = self._type_registry[nested_type_name]
                        else:
                            nested_fields = self._build_fields_from_selection_set(
                                selection.selection_set,
                                field_type,
                                schema,
                                max_depth - 1,
                                nested_type_name,
                            )
                            # Sadly pylance nor mypy like the dynamic nature of
                            # create_model here.
                            python_type = create_model(
                                nested_type_name,
                                **nested_fields,  # type: ignore
                            )
                            self._type_registry[nested_type_name] = python_type
                    else:
                        # No selection set or max depth reached, skip
                        continue
                elif isinstance(field_type, GraphQLEnumType):
                    python_type = self.generate_enum(field_type)
                elif isinstance(field_type, GraphQLScalarType):
                    python_type = self._map_scalar_name_to_python(field_type.name)
                else:
                    python_type = t.Any

                # Wrap in list if needed
                if is_list:
                    python_type = list[python_type]

                # Make optional if not required
                if not is_required:
                    python_type = t.Optional[python_type]
                    field_info = Field(default=None)
                else:
                    field_info = Field()

                fields[field_name] = (python_type, field_info)

        return fields
