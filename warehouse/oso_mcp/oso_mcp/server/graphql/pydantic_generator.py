"""Pydantic model generator for GraphQL types."""

from __future__ import annotations

import typing as t
from enum import Enum, StrEnum

if t.TYPE_CHECKING:
    from .types import MutationFilter, MutationInfo

from graphql import (
    FieldNode,
    FragmentSpreadNode,
    GraphQLEnumType,
    GraphQLField,
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

from .schema_visitor import (
    GraphQLSchemaTypeTraverser,
    GraphQLSchemaTypeVisitor,
    VisitorControl,
)


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


class ContextMode(Enum):
    """Mode for model generation context."""

    INPUT = "input"  # Processing GraphQLInputObjectType
    OUTPUT = (
        "output"  # Processing GraphQLObjectType (with optional SelectionSet filtering)
    )


class ModelBuilderContext:
    """Context for tracking state during model building.

    This class encapsulates all state needed during GraphQL type traversal
    and Pydantic model generation.
    """

    def __init__(
        self,
        mode: ContextMode,
        max_depth: int,
        context_prefix: str = "",
        selection_set: t.Optional[SelectionSetNode] = None,
        schema: t.Optional[GraphQLSchema] = None,
        parent_type: t.Optional[
            t.Union[GraphQLObjectType, GraphQLInputObjectType]
        ] = None,
    ):
        """Initialize model builder context.

        Args:
            mode: Context mode (INPUT or OUTPUT)
            max_depth: Maximum nesting depth for object types
            context_prefix: Prefix for nested type names
            selection_set: Optional SelectionSet for field filtering (None = all fields)
            schema: GraphQL schema (for SelectionSet mode)
            parent_type: Parent GraphQL type being processed
        """
        self.mode = mode
        self.max_depth = max_depth
        self.current_depth = 0
        self.context_prefix = context_prefix
        self.selection_set = selection_set
        self.schema = schema
        self.parent_type = parent_type
        self.fields: dict[str, tuple[t.Any, t.Any]] = {}


class PydanticModelBuildContext:
    """Context for building a single Pydantic model.

    This class encapsulates all state needed while building one Pydantic model
    from a GraphQL type. Multiple contexts can be stacked when processing nested types.
    """

    def __init__(
        self,
        model_name: str,
        parent_type: t.Union[GraphQLObjectType, GraphQLInputObjectType],
        depth: int,
        context_prefix: str = "",
    ):
        """Initialize model build context.

        Args:
            model_name: Name for the Pydantic model being built
            parent_type: GraphQL type being converted to Pydantic model
            depth: Current nesting depth
            context_prefix: Prefix for nested type names
        """
        self._model_name = model_name
        self._parent_type = parent_type
        self._depth = depth
        self._context_prefix = context_prefix
        self._fields: dict[str, tuple[t.Any, t.Any]] = {}  # Accumulated fields

    @property
    def model_name(self) -> str:
        """Get the model name."""
        return self._model_name

    @property
    def depth(self) -> int:
        """Get the depth."""
        return self._depth

    @property
    def context_prefix(self) -> str:
        """Get the context prefix."""
        return self._context_prefix

    def add_field(self, field_name: str, python_type: t.Any, field_info: t.Any = None):
        """Add a field to the model being built.

        Args:
            field_name: Name of the field
            python_type: Python type annotation for the field
            field_info: Optional Pydantic Field with metadata (default value, description, etc.)
        """
        self._fields[field_name] = (
            python_type,
            field_info if field_info is not None else ...,
        )

    def materialize(self) -> t.Type[BaseModel]:
        """Create the Pydantic model from accumulated fields.

        Returns:
            Dynamically created Pydantic model class
        """
        if not self._fields:
            # Create empty model if no fields
            return create_model(self._model_name)

        return create_model(self._model_name, **self._fields)  # type: ignore # pyright: ignore


class PydanticModelVisitor(GraphQLSchemaTypeVisitor):
    """Visitor that builds Pydantic models from GraphQL types.

    This visitor extends GraphQLSchemaVisitor to build Pydantic models during
    schema traversal. It uses a stack of PydanticModelBuildContext to manage
    nested model construction, and tracks depth to enforce max_depth limits.
    """

    def __init__(
        self,
        model_name: str,
        parent_type: t.Union[GraphQLObjectType, GraphQLInputObjectType],
        max_depth: int = 2,
        use_context_prefix: bool = False,
        ignore_unknown_types: bool = False,
    ):
        """Initialize the Pydantic model visitor.

        Args:
            model_name: Name of the root model to generate
            parent_type: GraphQL type to start traversal from
            max_depth: Maximum nesting depth for object types
            use_context_prefix: If True, prefix nested type names with parent context
            ignore_unknown_types: If True, map unknown types to Any instead of raising error
        """
        super().__init__()
        self._type_registry: dict[str, t.Type[BaseModel] | StrEnum] = {}
        self._max_depth = max_depth
        self._use_context_prefix = use_context_prefix
        self._root_model_name = model_name
        self._ignore_unknown_types = ignore_unknown_types
        self._context_stack: list[PydanticModelBuildContext] = []

    @property
    def _current_depth(self) -> int:
        """Get the current depth based on stack size."""
        return len(self._context_stack)

    def _should_skip_depth(self) -> bool:
        """Check if we've exceeded max depth."""
        return self._current_depth >= self._max_depth

    def _get_type_name(self, base_name: str, parent_prefix: str = "") -> str:
        """Get the type name, potentially with context prefix.

        Args:
            base_name: Base type name from GraphQL schema
            parent_prefix: Prefix from parent context

        Returns:
            Type name, optionally prefixed
        """
        if not self._use_context_prefix:
            return base_name

        if parent_prefix:
            return f"{parent_prefix}{base_name}"
        elif self._root_model_name:
            return f"{self._root_model_name}{base_name}"
        else:
            return base_name

    def _map_scalar_to_python(self, scalar_type: GraphQLScalarType) -> t.Any:
        """Map GraphQL scalar type to Python type."""
        scalar_map = {
            "String": str,
            "Int": int,
            "Float": float,
            "Boolean": bool,
            "ID": str,
            "JSON": t.Any,
            "DateTime": str,  # ISO 8601 format
        }
        return scalar_map.get(scalar_type.name, t.Any)

    def handle_scalar(
        self,
        field_name: str,
        scalar_type: GraphQLScalarType,
        is_required: bool,
        is_list: bool,
    ) -> VisitorControl:
        """Handle a scalar type by adding it to the current context."""
        if not self._context_stack:
            return VisitorControl.CONTINUE

        # Map to Python type
        python_type = self._map_scalar_to_python(scalar_type)

        # Apply list wrapper if needed
        if is_list:
            python_type = list[python_type]

        # Apply optional wrapper and create field info
        if not is_required:
            python_type = t.Optional[python_type]
            field_info = Field(default=None)
        else:
            field_info = Field()

        # Add to current context
        self._context_stack[-1].add_field(field_name, python_type, field_info)

        return VisitorControl.CONTINUE

    def handle_enum(
        self,
        field_name: str,
        enum_type: GraphQLEnumType,
        is_required: bool,
        is_list: bool,
    ) -> VisitorControl:
        """Handle an enum type by generating a StrEnum and adding to context."""
        # Enums are always registered with their base name (no prefix)
        type_name = enum_type.name

        # Generate enum if not in registry
        if type_name not in self._type_registry:
            enum_members = {
                name: value.value for name, value in enum_type.values.items()
            }
            enum_klass = StrEnum(type_name, enum_members)
            self._type_registry[type_name] = enum_klass

        if not self._context_stack:
            return VisitorControl.CONTINUE

        # Get the enum from registry
        python_type = self._type_registry[type_name]

        # Apply list wrapper if needed
        if is_list:
            python_type = list[python_type]  # type: ignore

        # Apply optional wrapper and create field info
        if not is_required:
            python_type = t.Optional[python_type]  # type: ignore
            field_info = Field(default=None)
        else:
            field_info = Field()

        # Add to current context
        self._context_stack[-1].add_field(field_name, python_type, field_info)

        return VisitorControl.CONTINUE

    def handle_enter_object(
        self,
        field_name: str,
        object_type: GraphQLObjectType,
        is_required: bool,
        is_list: bool,
    ) -> VisitorControl:
        """Handle entering an object type by pushing a new context."""
        # At root level (stack is empty), use root_model_name
        if not self._context_stack:
            type_name = self._root_model_name
            context_prefix = self._root_model_name if self._use_context_prefix else ""
        else:
            # Get parent prefix
            parent_prefix = self._context_stack[-1].context_prefix

            # Generate type name (with prefix if enabled)
            type_name = self._get_type_name(object_type.name, parent_prefix)
            context_prefix = (
                f"{parent_prefix}{type_name}" if self._use_context_prefix else ""
            )

        # Check depth limit
        if self._should_skip_depth():
            return VisitorControl.SKIP

        # Check if already in registry
        if type_name in self._type_registry:
            # Use existing model
            if self._context_stack:
                python_type = self._type_registry[type_name]

                # Apply list wrapper if needed
                if is_list:
                    python_type = list[python_type]  # type: ignore

                # Apply optional wrapper
                if not is_required:
                    python_type = t.Optional[python_type]  # type: ignore
                    field_info = Field(default=None)
                else:
                    field_info = Field()

                self._context_stack[-1].add_field(field_name, python_type, field_info)

            return VisitorControl.SKIP  # Don't revisit

        # Push new context for this object
        ctx = PydanticModelBuildContext(
            model_name=type_name,
            parent_type=object_type,
            depth=self._current_depth,
            context_prefix=context_prefix,
        )
        self._context_stack.append(ctx)

        return VisitorControl.CONTINUE

    def handle_leave_object(
        self,
        field_name: str,
        object_type: GraphQLObjectType,
        is_required: bool,
        is_list: bool,
    ) -> VisitorControl:
        """Handle leaving an object type by materializing the model."""
        if not self._context_stack:
            return VisitorControl.CONTINUE

        # Pop context and build model
        ctx = self._context_stack.pop()
        model = ctx.materialize()
        self._type_registry[ctx.model_name] = model

        # Add to parent context if exists
        if self._context_stack:
            python_type: t.Any = model

            # Apply list wrapper if needed
            if is_list:
                python_type = list[python_type]

            # Apply optional wrapper
            if not is_required:
                python_type = t.Optional[python_type]
                field_info = Field(default=None)
            else:
                field_info = Field()

            self._context_stack[-1].add_field(field_name, python_type, field_info)

        return VisitorControl.CONTINUE

    def handle_enter_input_object(
        self,
        field_name: str,
        input_type: GraphQLInputObjectType,
        is_required: bool,
        is_list: bool,
    ) -> VisitorControl:
        """Handle entering an input object type by pushing a new context."""
        # Input types always use base name (no prefix)
        type_name = input_type.name

        # Check if already in registry
        if type_name in self._type_registry:
            # Use existing model
            if self._context_stack:
                python_type = self._type_registry[type_name]

                # Apply list wrapper if needed
                if is_list:
                    python_type = list[python_type]  # type: ignore

                # Apply optional wrapper
                if not is_required:
                    python_type = t.Optional[python_type]  # type: ignore
                    field_info = Field(default=None)
                else:
                    field_info = Field()

                self._context_stack[-1].add_field(field_name, python_type, field_info)

            return VisitorControl.SKIP  # Don't revisit

        # Push new context
        ctx = PydanticModelBuildContext(
            model_name=type_name,
            parent_type=input_type,
            depth=self._current_depth,
            context_prefix="",  # Input types don't use prefix
        )
        self._context_stack.append(ctx)

        return VisitorControl.CONTINUE

    def handle_leave_input_object(
        self,
        field_name: str,
        input_type: GraphQLInputObjectType,
        is_required: bool,
        is_list: bool,
    ) -> VisitorControl:
        """Handle leaving an input object type by materializing the model."""
        if not self._context_stack:
            return VisitorControl.CONTINUE

        # Pop context and build model
        ctx = self._context_stack.pop()
        model = ctx.materialize()
        self._type_registry[ctx.model_name] = model

        # Add to parent context if exists
        if self._context_stack:
            python_type: t.Any = model

            # Apply list wrapper if needed
            if is_list:
                python_type = list[python_type]

            # Apply optional wrapper
            if not is_required:
                python_type = t.Optional[python_type]
                field_info = Field(default=None)
            else:
                field_info = Field()

            self._context_stack[-1].add_field(field_name, python_type, field_info)

        return VisitorControl.CONTINUE

    def handle_union(
        self,
        field_name: str,
        union_type: GraphQLUnionType,
        is_required: bool,
        is_list: bool,
    ) -> VisitorControl:
        """Handle a union type.

        Unions are treated like nested objects for depth purposes - they should be
        skipped when max_depth is reached since they contain nested object types.
        """
        # Check depth limit - unions should be skipped at max depth
        if self._should_skip_depth():
            return VisitorControl.SKIP

        # TODO: Implement union handling with discriminated types
        # For now, just add as Any
        if self._context_stack:
            python_type = t.Any
            if is_list:
                python_type = list[python_type]
            if not is_required:
                python_type = t.Optional[python_type]
                field_info = Field(default=None)
            else:
                field_info = Field()
            self._context_stack[-1].add_field(field_name, python_type, field_info)

        return VisitorControl.CONTINUE

    def handle_unknown(
        self,
        field_name: str,
        gql_type: t.Any,
        is_required: bool,
        is_list: bool,
    ) -> VisitorControl:
        """Handle an unknown type."""
        if not self._ignore_unknown_types:
            raise TypeError(
                f"Unsupported GraphQL type for field {field_name}: {gql_type}"
            )

        # Add as Any
        if self._context_stack:
            python_type = t.Any
            if is_list:
                python_type = list[python_type]
            if not is_required:
                python_type = t.Optional[python_type]
                field_info = Field(default=None)
            else:
                field_info = Field()
            self._context_stack[-1].add_field(field_name, python_type, field_info)

        return VisitorControl.CONTINUE

    # Public API methods for generating Pydantic models

    @classmethod
    def generate_input_model(
        cls,
        input_type: GraphQLInputObjectType,
        ignore_unknown_types: bool = False,
    ) -> t.Type[BaseModel]:
        """Create Pydantic model from GraphQL input type.

        Args:
            input_type: GraphQL input object type
            ignore_unknown_types: If True, map unknown types to Any instead of raising error

        Returns:
            Dynamically created Pydantic model class
        """
        # Create visitor with high max_depth to capture all required nested input fields
        visitor = cls(
            model_name=input_type.name,
            parent_type=input_type,
            max_depth=100,  # High depth for input types to include all required fields
            use_context_prefix=False,
            ignore_unknown_types=ignore_unknown_types,
        )

        # Create traverser and visit the input type
        traverser = GraphQLSchemaTypeTraverser(visitor)
        traverser.visit(input_type, field_name="")

        # Return the generated model from registry
        return visitor._type_registry[input_type.name]  # type: ignore

    @classmethod
    def generate_payload_model(
        cls,
        payload_type: GraphQLObjectType,
        max_depth: int = 2,
        ignore_unknown_types: bool = False,
    ) -> t.Type[BaseModel]:
        """Create Pydantic model from GraphQL object type (visits all fields).

        Args:
            payload_type: GraphQL object type
            max_depth: Maximum nesting depth for object types
            ignore_unknown_types: If True, map unknown types to Any instead of raising error

        Returns:
            Dynamically created Pydantic model class
        """
        # Create visitor without context prefix (visits all fields)
        visitor = cls(
            model_name=payload_type.name,
            parent_type=payload_type,
            max_depth=max_depth,
            use_context_prefix=False,
            ignore_unknown_types=ignore_unknown_types,
        )

        # Create traverser and visit the payload type (selection_set=None visits all fields)
        traverser = GraphQLSchemaTypeTraverser(visitor)
        traverser.visit(payload_type, field_name="")

        # Return the generated model from registry
        return visitor._type_registry[payload_type.name]  # type: ignore

    @classmethod
    def generate_model_from_selection_set(
        cls,
        operation_name: str,
        selection_set: SelectionSetNode,
        parent_type: GraphQLObjectType,
        schema: GraphQLSchema,
        max_depth: int = 100,
        ignore_unknown_types: bool = False,
        fragments: t.Optional[t.Dict[str, t.Any]] = None,
    ) -> t.Type[BaseModel]:
        """Create Pydantic model from GraphQL selection set (visits only selected fields).

        This method is used for custom .graphql query files where only specific fields
        are selected. Type names are prefixed with the operation name to avoid collisions.

        Args:
            operation_name: Name of the GraphQL operation
            selection_set: SelectionSet specifying which fields to visit
            parent_type: GraphQL object type to start from
            schema: GraphQL schema for type lookup
            max_depth: Maximum nesting depth for object types (default 100 for hand-written queries)
            ignore_unknown_types: If True, map unknown types to Any instead of raising error
            fragments: Optional dict of fragment definitions by name

        Returns:
            Dynamically created Pydantic model class
        """
        model_name = f"{operation_name}Response"

        # Create visitor with context prefix enabled
        visitor = cls(
            model_name=model_name,
            parent_type=parent_type,
            max_depth=max_depth,
            use_context_prefix=True,
            ignore_unknown_types=ignore_unknown_types,
        )

        # Create traverser with selection_set to filter fields
        traverser = GraphQLSchemaTypeTraverser(
            visitor,
            selection_set=selection_set,
            schema=schema,
            fragments=fragments,
        )
        traverser.visit(parent_type, field_name="")

        # Return the generated model from registry
        return visitor._type_registry[model_name]  # type: ignore


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
        # Delegate to PydanticModelVisitor
        return PydanticModelVisitor.generate_input_model(
            input_type, ignore_unknown_types=self._ignore_unknown_types
        )

    def generate_payload_model(
        self, payload_type: GraphQLObjectType, max_depth: int = 2
    ) -> t.Type[BaseModel]:
        """Create Pydantic model from GraphQL payload type.

        Args:
            payload_type: GraphQL object type for mutation payload
            max_depth: Maximum nesting depth for object types

        Returns:
            Dynamically created Pydantic model class
        """
        # Delegate to PydanticModelVisitor
        return PydanticModelVisitor.generate_payload_model(
            payload_type,
            max_depth=max_depth,
            ignore_unknown_types=self._ignore_unknown_types,
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
        max_depth: int = 100,
        fragments: t.Optional[t.Dict[str, t.Any]] = None,
    ) -> t.Type[BaseModel]:
        """Generate Pydantic model from GraphQL selection set.

        Args:
            operation_name: Name of the query operation (for model naming)
            selection_set: Selection set from query
            parent_type: The GraphQL type being selected from
            schema: GraphQL schema for type lookup
            max_depth: Maximum nesting depth for object types (default 100 for hand-written queries)
            fragments: Optional dict of fragment definitions by name

        Returns:
            Dynamically created Pydantic model class for response
        """
        # Delegate to PydanticModelVisitor
        return PydanticModelVisitor.generate_model_from_selection_set(
            operation_name=operation_name,
            selection_set=selection_set,
            parent_type=parent_type,
            schema=schema,
            max_depth=max_depth,
            ignore_unknown_types=self._ignore_unknown_types,
            fragments=fragments,
        )

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


class MutationCollectorVisitor(GraphQLSchemaTypeVisitor):
    """Collects MutationInfo during schema traversal using mutation field hooks.

    This visitor implements the handle_enter_mutation_field hook to collect
    mutation information as the schema's Mutation type is traversed.

    Example:
        visitor = MutationCollectorVisitor(schema, filters)
        traverser = GraphQLSchemaTypeTraverser(visitor, schema=schema)
        if schema.mutation_type:
            traverser.visit(schema.mutation_type, field_name="")
        mutations = visitor.mutations
    """

    def __init__(
        self,
        schema: GraphQLSchema,
        filters: list[MutationFilter] | None = None,
        ignore_unknown_types: bool = False,
    ):
        """Initialize the mutation collector visitor.

        Args:
            schema: GraphQL schema being traversed
            filters: Optional list of MutationFilter to filter out mutations
            ignore_unknown_types: If True, map unknown types to Any instead of raising error
        """
        self._schema = schema
        self._filters: list[MutationFilter] = filters or []
        self._ignore_unknown_types = ignore_unknown_types
        self._mutations: list[MutationInfo] = []

    @property
    def mutations(self) -> list[MutationInfo]:
        """Get the collected mutations."""
        return self._mutations

    def handle_enter_mutation_field(
        self,
        field_name: str,
        field_def: GraphQLField,
        input_type: GraphQLInputObjectType | None,
        return_type: t.Any,
    ) -> VisitorControl:
        """Handle entering a mutation field - collect mutation info.

        This is called for each field on the Mutation type. We extract the
        input and return types and generate Pydantic models for them.
        """
        # Import at runtime to avoid circular import
        from .types import MutationInfo

        # Skip mutations without input type
        if not input_type:
            return VisitorControl.SKIP

        # Skip if return type is not an object
        if not isinstance(return_type, GraphQLObjectType):
            return VisitorControl.SKIP

        # Generate models using PydanticModelVisitor
        input_model = PydanticModelVisitor.generate_input_model(
            input_type, ignore_unknown_types=self._ignore_unknown_types
        )
        payload_model = PydanticModelVisitor.generate_payload_model(
            return_type, ignore_unknown_types=self._ignore_unknown_types
        )

        mutation_info = MutationInfo(
            name=field_name,
            description=field_def.description or "",
            input_model=input_model,
            payload_model=payload_model,
            payload_fields=list(return_type.fields.keys()),
            graphql_input_type_name=input_type.name,
        )

        # Apply filters
        if not any(f.should_ignore(mutation_info) for f in self._filters):
            self._mutations.append(mutation_info)

        return VisitorControl.SKIP  # Don't need to traverse payload fields
