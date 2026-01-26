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
            python_type, field_info = self._create_pydantic_field(
                field_name, field.type
            )
            fields[field_name] = (python_type, field_info)

        # Create the model
        model = create_model(type_name, **fields)
        self._type_registry[type_name] = model
        return model

    def generate_payload_model(
        self, payload_type: GraphQLObjectType
    ) -> t.Type[BaseModel]:
        """Create Pydantic model from GraphQL payload type.

        Args:
            payload_type: GraphQL object type for mutation payload

        Returns:
            Dynamically created Pydantic model class
        """
        type_name = payload_type.name

        # Return registered type if available
        if type_name in self._type_registry:
            return self._type_registry[type_name]  # type: ignore

        fields = {}
        for field_name, field in payload_type.fields.items():
            python_type, field_info = self._create_pydantic_field(
                field_name, field.type
            )
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
        enum_members = {value.name: value.value for value in enum_type.values}

        # Create the enum
        enum_class = Enum(type_name, enum_members)
        self._type_registry[type_name] = enum_class
        return enum_class

    def _create_pydantic_field(
        self, name: str, gql_type: t.Any
    ) -> tuple[t.Any, t.Any]:
        """Create Pydantic field definition from GraphQL type.

        Args:
            name: Field name
            gql_type: GraphQL type

        Returns:
            Tuple of (python_type, field_info)
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
            python_type = list[self._map_graphql_type_to_python(inner_type)]
        else:
            python_type = self._map_graphql_type_to_python(gql_type)

        # Make optional if not required
        if not is_required:
            python_type = t.Optional[python_type]
            field_info = Field(default=None)
        else:
            field_info = Field()

        return python_type, field_info

    def _map_graphql_type_to_python(self, field_type: t.Any) -> t.Any:
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
            # For object types in payloads, use Any for now
            # Could be extended to generate nested models
            return t.Any

        # Default to Any for unknown types
        return t.Any
