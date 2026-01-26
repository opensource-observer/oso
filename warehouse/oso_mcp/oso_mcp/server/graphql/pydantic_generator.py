"""Pydantic model generator for GraphQL types."""

import typing as t
from enum import Enum

from graphql import (
    GraphQLEnumType,
    GraphQLInputObjectType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLScalarType,
)
from pydantic import BaseModel, Field, create_model


class UnsetNested(BaseModel):
    """Marker for unset nested fields in Pydantic models."""

    pass


class PydanticModelGenerator:
    """Dynamically generate Pydantic models from GraphQL types."""

    def __init__(self):
        """Initialize the model generator with a type registry."""
        self._type_registry: dict[str, t.Type[BaseModel] | t.Type[Enum]] = {}

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
        # type_name = payload_type.name

        # # Return registered type if available
        # if type_name in self._type_registry:
        #     return self._type_registry[type_name]  # type: ignore

        # fields = {}
        # for field_name, field in payload_type.fields.items():
        #     python_type, field_info = self._create_pydantic_field(
        #         field_name, field.type, depth=depth - 1, context_prefix=type_name
        #     )
        #     fields[field_name] = (python_type, field_info)

        # # Create the model
        # model = create_model(type_name, **fields)
        # self._type_registry[type_name] = model
        # return model

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

    def generate_enum(self, enum_type: GraphQLEnumType) -> t.Type[Enum]:
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
        enum_klass = type(type_name, (Enum,), enum_members)
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
