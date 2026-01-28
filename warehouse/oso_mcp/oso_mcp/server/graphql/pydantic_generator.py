"""Pydantic model generator for GraphQL types."""

import typing as t
from enum import StrEnum

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
    SelectionSetNode,
    VariableDefinitionNode,
)
from pydantic import BaseModel, Field, create_model


class UnsetNested(BaseModel):
    """Marker for unset nested fields in Pydantic models."""

    pass


class FieldTypeInfo:
    """Helper class to unwrap GraphQL field types and expose their properties.

    This class takes a GraphQL field type (which may be wrapped in NonNull and/or List)
    and provides convenient properties to access the base type and modifiers.
    """

    def __init__(self, base_type: t.Any, is_required: bool, is_list: bool):
        """Initialize with unwrapped field type information.

        Args:
            base_type: The unwrapped base GraphQL type
            is_required: Whether the field is required (NonNull)
            is_list: Whether the field is a list type
        """
        self._base_type = base_type
        self._is_required = is_required
        self._is_list = is_list

    @classmethod
    def from_graphql_type(cls, field_type: t.Any) -> "FieldTypeInfo":
        """Create FieldTypeInfo by unwrapping a GraphQL field type.

        Args:
            field_type: GraphQL field type (possibly wrapped in NonNull/List)

        Returns:
            FieldTypeInfo with unwrapped type information
        """
        # Check for NonNull wrapper
        is_required = isinstance(field_type, GraphQLNonNull)
        if is_required:
            field_type = field_type.of_type

        # Check for List wrapper
        is_list = isinstance(field_type, GraphQLList)
        if is_list:
            inner_type = field_type.of_type
            if isinstance(inner_type, GraphQLNonNull):
                inner_type = inner_type.of_type
            field_type = inner_type

        return cls(base_type=field_type, is_required=is_required, is_list=is_list)

    @property
    def base_type(self) -> t.Any:
        """The unwrapped base GraphQL type."""
        return self._base_type

    @property
    def is_required(self) -> bool:
        """Whether the field is required (NonNull)."""
        return self._is_required

    @property
    def is_list(self) -> bool:
        """Whether the field is a list type."""
        return self._is_list


class UnionTypeMarker:
    """Marker class for union types before they're converted to Pydantic fields.

    This class represents a GraphQL union type that needs to be converted to a
    Python Union type with discriminated fields.
    """

    def __init__(self, member_types: tuple[t.Type[BaseModel], ...]):
        """Initialize with union member types.

        Args:
            member_types: Tuple of Pydantic model classes for union members
        """
        self.member_types = member_types

    def to_union_type(self) -> t.Any:
        """Convert to a Python Union type annotation.

        Returns:
            Union type annotation of all member types
        """
        return t.Union[self.member_types]


class PydanticModelGenerator:
    """Dynamically generate Pydantic models from GraphQL types."""

    def __init__(self, ignore_unknown_types: bool = False):
        """Initialize the model generator with a type registry."""
        self._type_registry: dict[str, t.Type[BaseModel] | StrEnum] = {}
        self._ignore_unknown_types = ignore_unknown_types

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

    def generate_enum(self, enum_type: GraphQLEnumType) -> StrEnum:
        """Create Python StrEnum from GraphQL enum type. StrEnum is used to
        ensure that enum values are serialized as strings in JSON.

        Args:
            enum_type: GraphQL enum type

        Returns:
            Dynamically created StrEnum class
        """
        type_name = enum_type.name

        # Return registered enum if available
        if type_name in self._type_registry:
            return self._type_registry[type_name]  # type: ignore

        # Create enum members
        enum_members = {name: value.value for name, value in enum_type.values.items()}

        # Create the enum
        enum_klass = StrEnum(type_name, enum_members)
        self._type_registry[type_name] = enum_klass
        return enum_klass

    def generate_union_member_model(
        self,
        union_type: GraphQLUnionType,
        member_type: GraphQLObjectType,
        max_depth: int,
        context_prefix: str,
    ) -> t.Type[BaseModel]:
        """Generate a Pydantic model for a union member type.

        This adds the typename__ discriminator field to the model.

        Args:
            union_type: GraphQL union type
            member_type: GraphQL object type for this union member
            max_depth: Maximum depth for nested types
            context_prefix: Prefix for type names

        Returns:
            Dynamically created Pydantic model class for union member
        """
        # Generate the base model for this union member
        member_model_name = f"{context_prefix}{member_type.name}"

        # Check if already registered
        if member_model_name in self._type_registry:
            return self._type_registry[member_model_name]  # type: ignore

        # Build fields from the member type
        fields: dict[str, tuple[t.Any, t.Any]] = {}

        # Add discriminator field: typename__
        fields["typename__"] = (
            t.Literal[member_type.name],
            Field(alias="__typename"),
        )

        # Add all other fields from the member type
        for field_name, field in member_type.fields.items():
            field_result = self._create_pydantic_field(
                field_name,
                field.type,
                max_depth=max_depth - 1,
                context_prefix=member_model_name,
            )
            if field_result is None:
                continue
            python_type, field_info = field_result
            fields[field_name] = (python_type, field_info)

        # Create the model
        model = create_model(member_model_name, **fields)  # type: ignore
        self._type_registry[member_model_name] = model
        return model  # type: ignore

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

        # Check if it's a union type marker
        if isinstance(python_type, UnionTypeMarker):
            return self._create_union_field(python_type, is_required)

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
        match field_type:
            case GraphQLScalarType():
                scalar_map = {
                    "String": str,
                    "Int": int,
                    "Float": float,
                    "Boolean": bool,
                    "ID": str,
                    "JSON": t.Any,
                    "DateTime": str,  # ISO 8601 format
                }
                return scalar_map.get(field_type.name, t.Any)

            case GraphQLEnumType():
                return self.generate_enum(field_type)

            case GraphQLInputObjectType():
                return self.generate_input_model(field_type)

            case GraphQLObjectType():
                if max_depth > 0:
                    return self._get_or_create_model(
                        field_type, max_depth=max_depth, context_prefix=context_prefix
                    )
                return UnsetNested()

            case GraphQLUnionType():
                if max_depth > 0:
                    union_members = [
                        self.generate_union_member_model(
                            field_type, member_type, max_depth, context_prefix
                        )
                        for member_type in field_type.types
                        if isinstance(member_type, GraphQLObjectType)
                    ]
                    if union_members:
                        return UnionTypeMarker(tuple(union_members))
                return UnsetNested()

            case _:
                if not self._ignore_unknown_types:
                    raise TypeError(
                        f"Unsupported GraphQL type for field {name}: {field_type}"
                    )
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

    def _is_union_type_marker(self, python_type: t.Any) -> bool:
        """Check if a python_type is a union type marker.

        Args:
            python_type: The type to check

        Returns:
            True if the type is a UnionTypeMarker instance
        """
        return isinstance(python_type, UnionTypeMarker)

    def _is_fragment_model(self, model: t.Any) -> bool:
        """Check if a model is a valid BaseModel fragment.

        Args:
            model: The model to check

        Returns:
            True if the model is a BaseModel subclass
        """
        return isinstance(model, type) and issubclass(model, BaseModel)

    def _create_union_field(
        self, union_marker: UnionTypeMarker, is_required: bool
    ) -> tuple[t.Any, t.Any]:
        """Create a Pydantic field definition for a union type.

        Args:
            union_marker: UnionTypeMarker containing the union member types
            is_required: Whether the field is required

        Returns:
            Tuple of (python_type, field_info)
        """
        python_type = union_marker.to_union_type()

        # Union fields need discriminator
        if not is_required:
            python_type = t.Optional[python_type]
            field_info = Field(default=None, discriminator="typename__")
        else:
            field_info = Field(discriminator="typename__")

        return python_type, field_info

    def _is_single_fragment_spread(
        self, selection_set: SelectionSetNode
    ) -> t.Optional[str]:
        """Check if a selection set contains only a single fragment spread.

        Args:
            selection_set: Selection set to check

        Returns:
            Fragment name if selection set contains only one fragment spread, None otherwise
        """
        if len(selection_set.selections) != 1:
            return None

        selection = selection_set.selections[0]
        if isinstance(selection, FragmentSpreadNode):
            return selection.name.value

        return None

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

    def _build_nested_object_model_from_selection(
        self,
        field_type: GraphQLObjectType,
        selection: FieldNode,
        max_depth: int,
        context_prefix: str,
        schema: GraphQLSchema,
    ) -> t.Any | None:
        """Build a Pydantic model for a nested object type from a field selection.

        Args:
            field_type: GraphQL object type
            selection: Field selection node
            max_depth: Maximum nesting depth
            context_prefix: Prefix for nested type names
            schema: GraphQL schema

        Returns:
            Pydantic model class or None if selection set is missing or max depth reached
        """
        if not selection.selection_set or max_depth <= 0:
            return None

        # Check if selection set contains only a single fragment spread
        fragment_name = self._is_single_fragment_spread(selection.selection_set)
        if fragment_name:
            fragment_model_name = f"{fragment_name}Response"
            if fragment_model_name in self._type_registry:
                return self._type_registry[fragment_model_name]
            # Fragment model not found, fall through to build a new model

        # Build or retrieve nested model
        nested_type_name = f"{context_prefix}{field_type.name}"
        if nested_type_name in self._type_registry:
            return self._type_registry[nested_type_name]

        nested_fields = self._build_fields_from_selection_set(
            selection.selection_set,
            field_type,
            schema,
            max_depth - 1,
            nested_type_name,
        )
        python_type = create_model(nested_type_name, **nested_fields)  # type: ignore
        self._type_registry[nested_type_name] = python_type
        return python_type

    def _handle_fragment_spread(
        self, fragment_name: str, fields: dict[str, tuple[t.Any, t.Any]]
    ) -> None:
        """Handle a fragment spread by adding fragment fields to the fields dict.

        Args:
            fragment_name: Name of the fragment
            fields: Dictionary to add fields to (modified in-place)
        """
        fragment_model_name = f"{fragment_name}Response"
        if fragment_model_name not in self._type_registry:
            return

        fragment_model = self._type_registry[fragment_model_name]
        if not self._is_fragment_model(fragment_model):
            return

        # Type assertion: after _is_fragment_model check, this must be a BaseModel
        assert isinstance(fragment_model, type) and issubclass(
            fragment_model, BaseModel
        )

        # Spread the fragment's fields into this model
        for field_name, field_info in fragment_model.model_fields.items():
            fields[field_name] = (field_info.annotation, Field())

    def _handle_field_node(
        self,
        selection: FieldNode,
        parent_type: GraphQLObjectType,
        schema: GraphQLSchema,
        max_depth: int,
        context_prefix: str,
        fields: dict[str, tuple[t.Any, t.Any]],
    ) -> None:
        """Handle a field node selection by adding the field to the fields dict.

        Args:
            selection: Field selection node
            parent_type: Parent GraphQL type
            schema: GraphQL schema
            max_depth: Maximum nesting depth
            context_prefix: Prefix for nested type names
            fields: Dictionary to add fields to (modified in-place)
        """
        field_name = selection.name.value

        # Get field definition from parent type
        if field_name not in parent_type.fields:
            return

        field_def = parent_type.fields[field_name]
        type_info = FieldTypeInfo.from_graphql_type(field_def.type)

        # Determine Python type based on the base type
        if isinstance(type_info.base_type, GraphQLObjectType):
            python_type = self._build_nested_object_model_from_selection(
                type_info.base_type, selection, max_depth, context_prefix, schema
            )
            # Skip field if model building failed (e.g., max depth reached)
            if python_type is None:
                return
        elif isinstance(type_info.base_type, GraphQLEnumType):
            python_type = self.generate_enum(type_info.base_type)
        elif isinstance(type_info.base_type, GraphQLScalarType):
            python_type = self._map_scalar_name_to_python(type_info.base_type.name)
        else:
            python_type = t.Any

        # Wrap in list if needed
        if type_info.is_list:
            python_type = list[python_type]

        # Make optional if not required
        if not type_info.is_required:
            python_type = t.Optional[python_type]
            field_info = Field(default=None)
        else:
            field_info = Field()

        fields[field_name] = (python_type, field_info)

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
            match selection:
                case FragmentSpreadNode():
                    self._handle_fragment_spread(selection.name.value, fields)
                case FieldNode():
                    self._handle_field_node(
                        selection,
                        parent_type,
                        schema,
                        max_depth,
                        context_prefix,
                        fields,
                    )
                case _:
                    raise TypeError(
                        f"Unexpected selection type in selection set: {type(selection)}"
                    )

        return fields
