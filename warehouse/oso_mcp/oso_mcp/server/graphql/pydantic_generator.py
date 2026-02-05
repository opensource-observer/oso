"""Pydantic model generator for GraphQL types."""

from __future__ import annotations

import logging
import typing as t
from enum import Enum, StrEnum

from graphql import (
    GraphQLEnumType,
    GraphQLField,
    GraphQLInputObjectType,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLScalarType,
    GraphQLSchema,
    GraphQLUnionType,
)
from pydantic import BaseModel, Field, create_model

from .schema_visitor import (
    GraphQLSchemaTypeVisitor,
    VisitorControl,
)
from .types import MutationFilter, MutationInfo

logger = logging.getLogger(__name__)


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


class PydanticModelBuildContext:
    """Context for building a single Pydantic model.

    This class encapsulates all state needed while building one Pydantic model
    from a GraphQL type. Multiple contexts can be stacked when processing nested types.
    """

    def __init__(
        self,
        model_name: str,
        depth: int,
    ):
        """Initialize model build context.

        Args:
            model_name: Name for the Pydantic model being built
            depth: Current nesting depth
        """
        self._model_name = model_name
        self._depth = depth
        self._fields: dict[str, tuple[t.Any, t.Any]] = {}  # Accumulated fields

    @property
    def model_name(self) -> str:
        """Get the model name."""
        return self._model_name

    @property
    def depth(self) -> int:
        """Get the depth."""
        return self._depth

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


class PydanticModelAlreadyRegistered(Exception):
    """Raised when attempting to register a Pydantic model with a duplicate name."""

    def __init__(self, model_name: str):
        """Initialize with the duplicate model name.

        Args:
            model_name: Name of the model that is already registered
        """
        super().__init__(f"Pydantic model '{model_name}' is already registered.")
        self.model_name = model_name


class PydanticModelVisitor(GraphQLSchemaTypeVisitor):
    """Visitor that builds Pydantic models from GraphQL types.

    This visitor extends GraphQLSchemaVisitor to build Pydantic models during
    schema traversal. It uses a stack of PydanticModelBuildContext to manage
    nested model construction, and tracks depth to enforce max_depth limits.
    """

    def __init__(
        self,
        model_name: str,
        max_depth: int = 2,
        use_context_prefix: bool = False,
        ignore_unknown_types: bool = False,
    ):
        """Initialize the Pydantic model visitor.

        Args:
            model_name: Name of the root model to generate
            max_depth: Maximum nesting depth for object types
            use_context_prefix: If True, prefix nested type names with parent context
            ignore_unknown_types: If True, map unknown types to Any instead of raising error
        """
        super().__init__()
        self._type_registry: dict[str, t.Type[BaseModel] | StrEnum] = {}
        self._max_depth = max_depth
        self._use_context_prefix = use_context_prefix
        self._ignore_unknown_types = ignore_unknown_types
        self._context_stack: list[PydanticModelBuildContext] = []

    @property
    def current_depth(self) -> int:
        """Get the current depth based on stack size."""
        return len(self._context_stack)

    def get_type(self, name: str) -> t.Type[BaseModel] | StrEnum:
        """Get the type registry."""
        return self._type_registry[name]

    def is_type_registered(self, name: str) -> bool:
        """Check if a type is registered."""
        return name in self._type_registry

    def should_skip_depth(self) -> bool:
        """Check if we've exceeded max depth."""
        return self.current_depth >= self._max_depth

    def require_context(self, operation: str) -> PydanticModelBuildContext:
        """Get current context or raise error if none exists.

        Args:
            operation: Description of the operation being attempted (for error message)

        Returns:
            The current context

        Raises:
            RuntimeError: If no context exists (invalid traversal state)
        """
        if not self._context_stack:
            raise RuntimeError(
                f"Cannot {operation} without a context - "
                "traversal may have started from an invalid point"
            )
        return self._context_stack[-1]

    @property
    def current_context(self) -> t.Optional[PydanticModelBuildContext]:
        """Get the current context, or None if stack is empty.

        Returns:
            The current context or None
        """
        if not self._context_stack:
            return None
        return self._context_stack[-1]

    def start_context(
        self, name: str, no_prefix: bool = False
    ) -> type[BaseModel] | StrEnum | None:
        """Enter a new context with the given name.

        Args:
            name: Name of the new context
        """
        logger.debug(f"Starting context: {name}, no_prefix={no_prefix}")
        name = self.next_context_name(name, no_prefix=no_prefix)
        if self.is_type_registered(name):
            raise PydanticModelAlreadyRegistered(name)

        ctx = PydanticModelBuildContext(
            model_name=name,
            depth=self.current_depth,
        )
        self._context_stack.append(ctx)
        return None

    def next_context_name(self, name: str, no_prefix: bool = False) -> str:
        if (
            self._use_context_prefix
            and not no_prefix
            and self.current_context is not None
        ):
            return f"{self.current_context.model_name}{name}"
        return name

    def finish_context(self) -> str:
        """Exit the current context and materialize its model.

        Returns:
            The materialized Pydantic model of the exited context
        """
        self.require_context("finish context")
        ctx = self._context_stack.pop()
        model = ctx.materialize()
        self._type_registry[ctx.model_name] = model
        return ctx.model_name

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
        ctx = self.require_context("add scalar field")

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
        ctx.add_field(field_name, python_type, field_info)

        return VisitorControl.CONTINUE

    def handle_enum(
        self,
        field_name: str,
        enum_type: GraphQLEnumType,
        is_required: bool,
        is_list: bool,
    ) -> VisitorControl:
        """Handle an enum type by generating a StrEnum and adding to context."""
        ctx = self.require_context("add enum field")

        # Enums are always registered with their base name (no prefix)
        type_name = enum_type.name

        # Generate enum if not in registry
        if not self.is_type_registered(type_name):
            enum_members = {
                name: value.value for name, value in enum_type.values.items()
            }
            enum_klass = StrEnum(type_name, enum_members)
            self._type_registry[type_name] = enum_klass

        # Get the enum from registry
        python_type = self.get_type(type_name)

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
        ctx.add_field(field_name, python_type, field_info)

        return VisitorControl.CONTINUE

    def handle_enter_object(
        self,
        field_name: str,
        object_type: GraphQLObjectType,
        is_required: bool,
        is_list: bool,
    ) -> VisitorControl:
        """Handle entering an object type by pushing a new context."""
        # Check depth limit - skip traversal without adding field to parent
        # (fields at max depth are not requested in the query, so they shouldn't
        # be in the model - this avoids validation errors for missing fields)
        if self.should_skip_depth():
            return VisitorControl.SKIP

        try:
            self.start_context(object_type.name)
        except PydanticModelAlreadyRegistered as e:
            python_type = self.get_type(e.model_name)
            # Use existing model
            current_context = self.require_context("add object field")

            # Apply list wrapper if needed
            if is_list:
                python_type = list[python_type]  # type: ignore

            # Apply optional wrapper
            if not is_required:
                python_type = t.Optional[python_type]  # type: ignore
                field_info = Field(default=None)
            else:
                field_info = Field()

            current_context.add_field(field_name, python_type, field_info)

            return VisitorControl.SKIP  # Don't revisit
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
        created_model_name = self.finish_context()
        model = self.get_type(created_model_name)

        # Add to parent context if exists
        if self.current_context:
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

            self.current_context.add_field(field_name, python_type, field_info)

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

        try:
            self.start_context(type_name)
        except PydanticModelAlreadyRegistered as e:
            python_type = self.get_type(e.model_name)
            # Use existing model
            if self.current_context:
                # Apply list wrapper if needed
                if is_list:
                    python_type = list[python_type]  # type: ignore

                # Apply optional wrapper
                if not is_required:
                    python_type = t.Optional[python_type]  # type: ignore
                    field_info = Field(default=None)
                else:
                    field_info = Field()

                self.current_context.add_field(field_name, python_type, field_info)

            return VisitorControl.SKIP  # Don't revisit
        return VisitorControl.CONTINUE

    def handle_leave_input_object(
        self,
        field_name: str,
        input_type: GraphQLInputObjectType,
        is_required: bool,
        is_list: bool,
    ) -> VisitorControl:
        """Handle leaving an input object type by materializing the model."""
        if not self.current_context:
            raise RuntimeError("No context to finish for input object")

        model_name = self.finish_context()
        model = self.get_type(model_name)

        # Add to parent context if exists
        if self.current_context:
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

            self.current_context.add_field(field_name, python_type, field_info)

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
        if self.should_skip_depth():
            return VisitorControl.SKIP

        current_context = self.require_context("add union field")

        # TODO: Implement union handling with discriminated types
        # For now, just add as Any
        python_type = t.Any
        if is_list:
            python_type = list[python_type]
        if not is_required:
            python_type = t.Optional[python_type]
            field_info = Field(default=None)
        else:
            field_info = Field()
        current_context.add_field(field_name, python_type, field_info)

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

        ctx = self.require_context("add unknown field")

        # Add as Any
        python_type = t.Any
        if is_list:
            python_type = list[python_type]
        if not is_required:
            python_type = t.Optional[python_type]
            field_info = Field(default=None)
        else:
            field_info = Field()
        ctx.add_field(field_name, python_type, field_info)

        return VisitorControl.CONTINUE


def map_variable_scalar(scalar_name: str) -> t.Any:
    """Map scalar name to Python type for variables."""
    scalar_map = {
        "String": str,
        "Int": int,
        "Float": float,
        "Boolean": bool,
        "ID": str,
        "DateTime": str,
        "Date": str,
        "JSON": dict,
        "BigInt": int,
        "Decimal": float,
    }
    return scalar_map.get(scalar_name, str)


class MutationCollectorVisitor(PydanticModelVisitor):
    """Collects MutationInfo during schema traversal using mutation field hooks.

    This visitor inherits from PydanticModelVisitor to leverage the inherited
    enter/leave hooks for building Pydantic models during traversal.

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
        # Initialize parent visitor
        super().__init__(
            model_name="",  # Unused - contexts created during traversal
            max_depth=2,
            use_context_prefix=False,
            ignore_unknown_types=ignore_unknown_types,
        )
        self._schema = schema
        self._filters: list[MutationFilter] = filters or []
        self._mutations: list[MutationInfo] = []

        # Mutation context tracking
        self._current_mutation_name: str | None = None
        self._current_mutation_def: GraphQLField | None = None
        self._current_input_type: GraphQLInputObjectType | None = None
        self._current_return_type: GraphQLObjectType | None = None

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
        """Handle entering a mutation field - store context for later collection."""
        # Skip mutations without input type
        if not input_type:
            return VisitorControl.SKIP

        # Skip if return type is not an object
        if not isinstance(return_type, GraphQLObjectType):
            return VisitorControl.SKIP

        # Clear context stack so depth counting starts fresh for each mutation
        # (the Mutation root type context shouldn't count toward payload depth)
        self._context_stack.clear()

        # # Store mutation context (models will be built by inherited hooks during traversal)
        self._current_mutation_name = field_name
        self._current_mutation_def = field_def
        self._current_input_type = input_type
        self._current_return_type = return_type

        return VisitorControl.CONTINUE  # Let traverser visit input and return types

    def handle_leave_mutation_field(
        self,
        field_name: str,
        field_def: GraphQLField,
        input_type: GraphQLInputObjectType | None,
        return_type: t.Any,
    ) -> VisitorControl:
        """Handle leaving a mutation field - collect the mutation info."""

        if self._current_mutation_name is None:
            return VisitorControl.CONTINUE

        # Get models built by inherited hooks during traversal
        input_model = self.get_type(input_type.name) if input_type else None
        payload_model = (
            self.get_type(return_type.name)
            if isinstance(return_type, GraphQLObjectType)
            else None
        )

        if input_model and payload_model and isinstance(return_type, GraphQLObjectType):
            assert isinstance(input_model, type), (
                "Schema should only accept model types as inputs"
            )
            assert isinstance(payload_model, type), (
                "Schema should only return model types"
            )
            assert issubclass(input_model, BaseModel)
            assert issubclass(payload_model, BaseModel)

            current_mutation_def = self._current_mutation_def
            description = ""
            if current_mutation_def:
                description = current_mutation_def.description or ""
            current_input_type = self._current_input_type
            graphql_input_type_name = ""
            if current_input_type:
                graphql_input_type_name = current_input_type.name

            mutation_info = MutationInfo(
                name=self._current_mutation_name,
                description=description,
                input_model=input_model,
                payload_model=payload_model,
                payload_fields=list(return_type.fields.keys()),
                graphql_input_type_name=graphql_input_type_name,
            )

            if not any(f.should_ignore(mutation_info) for f in self._filters):
                self._mutations.append(mutation_info)

        # Clear context
        self._current_mutation_name = None
        self._current_mutation_def = None
        self._current_input_type = None
        self._current_return_type = None

        return VisitorControl.CONTINUE
