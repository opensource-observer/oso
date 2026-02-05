"""Pydantic model generator for GraphQL types."""

from __future__ import annotations

import abc
import logging
import typing as t
from enum import StrEnum

from graphql import (
    GraphQLEnumType,
    GraphQLField,
    GraphQLInputObjectType,
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

GeneratedType = t.Type[BaseModel] | StrEnum | t.Any


class UnsetNested(BaseModel):
    """Marker for unset nested fields in Pydantic models."""

    pass


class TypeBuildContext(abc.ABC):
    """Generic context for building a type"""

    @property
    @abc.abstractmethod
    def type_name(self) -> str:
        """Get the type name being built."""
        pass

    @property
    @abc.abstractmethod
    def depth(self) -> int:
        """Get the current depth."""
        pass

    @abc.abstractmethod
    def materialize(self) -> GeneratedType:
        """Materialize the type being built."""
        pass


class UnionTypeBuildContext(TypeBuildContext):
    """Context for building a union type.

    This class encapsulates all state needed while building one union type
    from a GraphQL union. Multiple contexts can be stacked when processing nested types.
    """

    def __init__(
        self,
        type_name: str,
        depth: int,
    ):
        """Initialize union type build context.

        Args:
            type_name: Name of the union type being built
            depth: Current nesting depth
            member_types: List of member types in the union
        """
        self._type_name = type_name
        self._depth = depth
        self._member_types: list[t.Any] = []

    @property
    def type_name(self) -> str:
        """Get the union type name."""
        return self._type_name

    @property
    def depth(self) -> int:
        """Get the depth."""
        return self._depth

    def add_member(self, member_type: t.Any, *args) -> None:
        """Add a member type to the union.

        Args:
            member_type: Member type to add
        """
        self._member_types.append(member_type)

    def materialize(self) -> t.Any:
        """Create the union type from member types.

        Returns:
            The union type
        """
        return t.Union[tuple(self._member_types)]


class PydanticModelBuildContext(TypeBuildContext):
    """Context for building a single Pydantic model.

    This class encapsulates all state needed while building one Pydantic model
    from a GraphQL type. Multiple contexts can be stacked when processing nested types.
    """

    def __init__(
        self,
        type_name: str,
        depth: int,
        discriminator: str | None = None,
    ):
        """Initialize model build context.

        Args:
            type_name: Name for the Pydantic model being built
            depth: Current nesting depth
            discriminator: Optional discriminator field for model (for unions)
        """
        self._type_name = type_name
        self._depth = depth
        self._fields: dict[str, tuple[t.Any, t.Any]] = {}  # Accumulated fields
        self._discriminator = discriminator

    @property
    def type_name(self) -> str:
        """Get the model name."""
        return self._type_name

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
        fields = self._fields.copy()
        if self._discriminator:
            # Add discriminator field if specified
            fields["typename__"] = (
                t.Literal[self._discriminator],
                Field(alias="__typename"),
            )

        if not fields:
            # Create empty model if no fields
            return create_model(self._type_name)

        return create_model(self._type_name, **fields)  # type: ignore # pyright: ignore


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
        self._type_registry: dict[str, GeneratedType] = {}
        self._max_depth = max_depth
        self._use_context_prefix = use_context_prefix
        self._ignore_unknown_types = ignore_unknown_types
        self._context_stack: list[TypeBuildContext] = []

    @property
    def current_depth(self) -> int:
        """Get the current depth based on stack size."""
        return len(self._context_stack)

    def get_type(self, name: str) -> GeneratedType:
        """Get the type registry."""
        return self._type_registry[name]

    def is_type_registered(self, name: str) -> bool:
        """Check if a type is registered."""
        return name in self._type_registry

    def should_skip_depth(self) -> bool:
        """Check if we've exceeded max depth."""
        return self.current_depth >= self._max_depth

    def require_context(self, operation: str) -> TypeBuildContext:
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

    def require_model_context(self, operation: str) -> PydanticModelBuildContext:
        """Get current Pydantic model context or raise error if none exists.

        Args:
            operation: Description of the operation being attempted (for error message)
        Returns:
            The current Pydantic model context
        Raises:
            RuntimeError: If no context exists (invalid traversal state)
        """

        ctx = self.require_context(operation)
        if not isinstance(ctx, PydanticModelBuildContext):
            raise RuntimeError(
                f"Cannot {operation} without a Pydantic model context - "
                "traversal may have started from an invalid point or the visitor is context is misconfigured"
            )
        return ctx

    @property
    def current_context(self) -> t.Optional[TypeBuildContext]:
        """Get the current context, or None if stack is empty.

        Returns:
            The current context or None
        """
        if not self._context_stack:
            return None
        return self._context_stack[-1]

    def start_model_context(self, name: str, no_prefix: bool = False) -> None:
        """Enter a new context with the given name.

        Args:
            name: Name of the new context
        """
        logger.debug(f"Starting context: {name}, no_prefix={no_prefix}")
        name = self.next_context_name(name, no_prefix=no_prefix)
        if self.is_type_registered(name):
            raise PydanticModelAlreadyRegistered(name)

        ctx = PydanticModelBuildContext(
            type_name=name,
            depth=self.current_depth,
        )
        self._context_stack.append(ctx)
        return None

    def start_union_context(self, name: str, no_prefix: bool = False) -> None:
        """Enter a new union context with the given name.

        Args:
            name: Name of the new union context
        """
        logger.debug(f"Starting union context: {name}, no_prefix={no_prefix}")
        name = self.next_context_name(name, no_prefix=no_prefix)
        if self.is_type_registered(name):
            raise PydanticModelAlreadyRegistered(name)

        ctx = UnionTypeBuildContext(
            type_name=name,
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
            return f"{self.current_context.type_name}{name}"
        return name

    def finish_context(self) -> str:
        """Exit the current context and materialize its model.

        Returns:
            The materialized Pydantic model of the exited context
        """
        self.require_context("finish context")
        ctx = self._context_stack.pop()
        logger.debug(f"Finishing context: {ctx.type_name} at depth {ctx.depth}")
        model = ctx.materialize()
        self._type_registry[ctx.type_name] = model
        return ctx.type_name

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
        description: str | None,
    ) -> VisitorControl:
        """Handle a scalar type by adding it to the current context."""
        ctx = self.require_model_context("add scalar field")

        logger.debug(
            f"Adding scalar field: {field_name} of type {scalar_type.name} with description: {description}"
        )

        # Map to Python type
        python_type = self._map_scalar_to_python(scalar_type)

        # Apply list wrapper if needed
        if is_list:
            python_type = list[python_type]

        # Apply optional wrapper and create field info
        if not is_required:
            python_type = t.Optional[python_type]
            field_info = Field(default=None, description=description)
        else:
            field_info = Field(description=description)

        # Add to current context
        ctx.add_field(field_name, python_type, field_info)

        return VisitorControl.CONTINUE

    def handle_enum(
        self,
        field_name: str,
        enum_type: GraphQLEnumType,
        is_required: bool,
        is_list: bool,
        description: str | None,
    ) -> VisitorControl:
        """Handle an enum type by generating a StrEnum and adding to context."""
        ctx = self.require_model_context("add enum field")

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
            field_info = Field(default=None, description=description)
        else:
            field_info = Field(description=description)

        # Add to current context
        ctx.add_field(field_name, python_type, field_info)

        return VisitorControl.CONTINUE

    def handle_enter_object(
        self,
        field_name: str,
        object_type: GraphQLObjectType,
        is_required: bool,
        is_list: bool,
        description: str | None,
    ) -> VisitorControl:
        """Handle entering an object type by pushing a new context."""
        # Check depth limit - skip traversal without adding field to parent
        # (fields at max depth are not requested in the query, so they shouldn't
        # be in the model - this avoids validation errors for missing fields)
        if self.should_skip_depth():
            return VisitorControl.SKIP

        try:
            self.start_model_context(object_type.name)
        except PydanticModelAlreadyRegistered as e:
            python_type = self.get_type(e.model_name)

            # If we're at the root no need to add the field to anything
            # And this type is already registered so we can skip
            if self.current_context is None:
                return VisitorControl.SKIP

            # Use existing model
            current_context = self.require_context("add object field")

            # Apply list wrapper if needed
            if is_list:
                python_type = list[python_type]  # type: ignore

            # Apply optional wrapper
            if not is_required:
                python_type = t.Optional[python_type]  # type: ignore
                field_info = Field(default=None, description=description)
            else:
                field_info = Field(description=description)

            match current_context:
                case PydanticModelBuildContext():
                    current_context.add_field(field_name, python_type, field_info)
                case UnionTypeBuildContext():
                    current_context.add_member(python_type)

            return VisitorControl.SKIP  # Don't revisit
        return VisitorControl.CONTINUE

    def handle_leave_object(
        self,
        field_name: str,
        object_type: GraphQLObjectType,
        is_required: bool,
        is_list: bool,
        description: str | None,
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
                field_info = Field(default=None, description=description)
            else:
                field_info = Field(description=description)

            current_context = self.current_context
            match current_context:
                case PydanticModelBuildContext():
                    current_context.add_field(field_name, python_type, field_info)
                case UnionTypeBuildContext():
                    current_context.add_member(python_type)

        return VisitorControl.CONTINUE

    def handle_enter_input_object(
        self,
        field_name: str,
        input_type: GraphQLInputObjectType,
        is_required: bool,
        is_list: bool,
        description: str | None,
    ) -> VisitorControl:
        """Handle entering an input object type by pushing a new context."""
        # Input types always use base name (no prefix)
        type_name = input_type.name

        try:
            self.start_model_context(type_name, no_prefix=True)
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
                    field_info = Field(default=None, description=description)
                else:
                    field_info = Field(description=description)

                current_context = self.current_context
                match current_context:
                    case PydanticModelBuildContext():
                        current_context.add_field(field_name, python_type, field_info)
                    case UnionTypeBuildContext():
                        current_context.add_member(python_type)

            return VisitorControl.SKIP  # Don't revisit
        return VisitorControl.CONTINUE

    def handle_leave_input_object(
        self,
        field_name: str,
        input_type: GraphQLInputObjectType,
        is_required: bool,
        is_list: bool,
        description: str | None,
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
                field_info = Field(default=None, description=description)
            else:
                field_info = Field(description=description)

            current_context = self.current_context
            match current_context:
                case PydanticModelBuildContext():
                    current_context.add_field(field_name, python_type, field_info)
                case UnionTypeBuildContext():
                    current_context.add_member(python_type)

        return VisitorControl.CONTINUE

    def handle_enter_union(
        self,
        field_name: str,
        union_type: GraphQLUnionType,
        is_required: bool,
        is_list: bool,
        description: str | None,
    ) -> VisitorControl:
        """Handle a union type.

        Unions are treated like nested objects for depth purposes - they should be
        skipped when max_depth is reached since they contain nested object types.
        """
        # Check depth limit - unions should be skipped at max depth
        if self.should_skip_depth():
            return VisitorControl.SKIP

        try:
            self.start_union_context(union_type.name)
        except PydanticModelAlreadyRegistered as e:
            existing_type = self.get_type(e.model_name)
            assert t.get_origin(existing_type) == t.Union
            # Use existing union
            current_context = self.require_model_context("add union field")
            # Apply list wrapper if needed
            if is_list:
                existing_type = list[existing_type]  # type: ignore
            # Apply optional wrapper
            if not is_required:
                existing_type = t.Optional[existing_type]  # type: ignore
                field_info = Field(
                    default=None, description=description, discriminator="typename__"
                )
            else:
                field_info = Field(description=description, discriminator="typename__")
            current_context.add_field(field_name, existing_type, field_info)

        return VisitorControl.CONTINUE

    def handle_leave_union(
        self,
        field_name: str,
        union_type: GraphQLUnionType,
        is_required: bool,
        is_list: bool,
        description: str | None,
    ) -> VisitorControl:
        """Handle leaving a union type by materializing the union."""
        if not self.current_context:
            raise RuntimeError("No context to finish for union type")

        union_name = self.finish_context()
        union_type_materialized = self.get_type(union_name)

        # Add to parent context if exists
        if self.current_context:
            python_type: t.Any = union_type_materialized

            # Apply list wrapper if needed
            if is_list:
                python_type = list[python_type]

            # Apply optional wrapper
            if not is_required:
                python_type = t.Optional[python_type]
                field_info = Field(default=None, description=description)
            else:
                field_info = Field(description=description)

            current_context = self.require_model_context("add union field")
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

        match ctx:
            case PydanticModelBuildContext():
                ctx.add_field(field_name, python_type, field_info)
            case UnionTypeBuildContext():
                ctx.add_member(python_type)

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
        input_description: str | None,
        return_description: str | None,
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
        input_description: str | None,
        return_description: str | None,
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
