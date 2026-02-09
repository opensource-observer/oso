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
from oso_core.pydantictools.utils import is_pydantic_model_class
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


def create_graphql_type_string(type_name: str, is_required: bool, is_list: bool) -> str:
    """Create a string representation of the GraphQL type for documentation.

    Args:
        type_name: The base name of the GraphQL type (e.g. "User", "String")
        is_required: Whether the field is non-nullable (True if required)
        is_list: Whether the field is a list
    Returns:
        A string representation of the GraphQL type
    """
    graphql_type_string = type_name
    if is_list:
        graphql_type_string = f"[{graphql_type_string}]"
    if is_required:
        graphql_type_string = f"{graphql_type_string}!"
    return graphql_type_string


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


class PydanticModelAlreadyRegisteredError(Exception):
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

    def should_skip_depth(self, padding: int = 0) -> bool:
        """Check if we've exceeded max depth."""
        return self.current_depth + padding >= self._max_depth

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

    def create_pydantic_field(
        self,
        *,
        field_name: str,
        graphql_type_name: str,
        python_type: t.Any,
        description: str | None,
        is_required: bool,
        is_list: bool,
        discriminator: str | None = None,
    ) -> tuple[str, t.Any, t.Any]:
        """Helper to create a Pydantic field with GraphQL metadata.

        Args:
            field_name: Name of the field
            python_type: Python type annotation for the field
            description: Optional description for the field (from GraphQL schema)
            graphql_type_string: Optional string representation of the GraphQL type for documentation
            discriminator: Optional discriminator field for the Pydantic model

        Returns:
            Tuple of (python_type, Field) to be used in create_model
        """
        if is_list:
            python_type = t.List[python_type]

        graphql_type_string = create_graphql_type_string(
            graphql_type_name, is_required=is_required, is_list=is_list
        )

        alias = None
        if field_name.startswith("_"):
            # We need to alias fields that start with _ since Pydantic doesn't
            # allow them as-is
            alias = field_name
            # Strip leading underscores for the actual field name since Pydantic
            # doesn't allow them, but we can preserve the original name in the
            # alias for serialization
            new_field_name = field_name.lstrip("_")
            # Number of leading underscores removed
            underscore_len = len(field_name) - len(new_field_name)
            # Add trailing underscores with the same number of underscores
            field_name = f"{new_field_name}{'_' * underscore_len}"

        # Apply optional wrapper and create field info
        if not is_required:
            python_type = t.Optional[python_type]
            field_info = Field(
                default=None,
                description=description,
                json_schema_extra={"graphql_type_string": graphql_type_string},
                discriminator=discriminator,
                alias=alias,
            )
        else:
            logger.debug(
                f"Creating required field {field_name} with GraphQL type {graphql_type_string} and Python type {python_type} with description: {description}"
            )
            if is_pydantic_model_class(python_type):
                logger.debug(
                    f"Field {field_name} is a nested model with fields: {python_type.model_fields}"
                )
            field_info = Field(
                description=description,
                json_schema_extra={"graphql_type_string": graphql_type_string},
                discriminator=discriminator,
                alias=alias,
            )
        return field_name, python_type, field_info

    def add_field_to_context(
        self,
        *,
        field_name: str,
        graphql_type_name: str,
        python_type: t.Any,
        description: str | None,
        is_required: bool,
        is_list: bool,
        discriminator: str | None = None,
        require_model_context: bool = True,
    ):
        logger.debug(
            f"Adding field {field_name} of type {graphql_type_name} with description: {description} with Python type {python_type} to context required: {is_required} list: {is_list}"
        )

        updated_field_name, python_type, field_info = self.create_pydantic_field(
            field_name=field_name,
            graphql_type_name=graphql_type_name,
            python_type=python_type,
            description=description,
            is_required=is_required,
            is_list=is_list,
            discriminator=discriminator,
        )
        logger.debug(
            f"Created field info for {updated_field_name}: {field_info} and Python type: {python_type}"
        )
        current_context = self.current_context
        if not current_context:
            if require_model_context:
                raise RuntimeError(
                    f"Cannot add field {updated_field_name} without a context - "
                    "traversal may have started from an invalid point"
                )
            else:
                logger.debug(
                    "No context available to add field %s, skipping context addition",
                    updated_field_name,
                )
                return
        match current_context:
            case PydanticModelBuildContext():
                current_context.add_field(updated_field_name, python_type, field_info)
            case UnionTypeBuildContext():
                current_context.add_member(python_type)
            case _:
                raise RuntimeError(
                    "Invalid context type when adding field - this should never happen"
                )

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
        prefixed_name = self.next_context_name(name, no_prefix=no_prefix)
        if self.is_type_registered(prefixed_name):
            raise PydanticModelAlreadyRegisteredError(prefixed_name)

        discriminator = None
        if self.current_context and isinstance(
            self.current_context, UnionTypeBuildContext
        ):
            discriminator = name
        ctx = PydanticModelBuildContext(
            type_name=prefixed_name,
            depth=self.current_depth,
            discriminator=discriminator,
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
            raise PydanticModelAlreadyRegisteredError(name)

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

    def map_scalar_graphql_type_to_python(
        self, scalar_type: GraphQLScalarType
    ) -> t.Any:
        """Map GraphQL scalar type to Python type."""
        return self.map_scalar_graphql_type_name_to_python(scalar_type.name)

    def map_scalar_graphql_type_name_to_python(self, type_name: str) -> t.Any:
        """Map GraphQL scalar type name to Python type."""
        scalar_map = {
            "String": str,
            "Int": int,
            "Float": float,
            "Boolean": bool,
            "ID": str,
            "JSON": t.Any,
            "DateTime": str,  # ISO 8601 format
        }
        return scalar_map.get(type_name, t.Any)

    def handle_scalar(
        self,
        field_name: str,
        scalar_type: GraphQLScalarType,
        is_required: bool,
        is_list: bool,
        description: str | None,
    ) -> VisitorControl:
        """Handle a scalar type by adding it to the current context."""
        self.require_model_context("add scalar field")

        logger.debug(
            f"Adding scalar field: {field_name} of type {scalar_type.name} with description: {description}"
        )

        # Map to Python type
        python_type = self.map_scalar_graphql_type_to_python(scalar_type)

        self.add_field_to_context(
            field_name=field_name,
            graphql_type_name=scalar_type.name,
            python_type=python_type,
            description=description,
            is_required=is_required,
            is_list=is_list,
        )

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

        self.add_field_to_context(
            field_name=field_name,
            graphql_type_name=type_name,
            python_type=python_type,
            description=description,
            is_required=is_required,
            is_list=is_list,
        )

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
            logger.debug(f"Skipping object {object_type.name} due to depth limit")
            return VisitorControl.SKIP

        try:
            self.start_model_context(object_type.name)
        except PydanticModelAlreadyRegisteredError as e:
            python_type = self.get_type(e.model_name)

            self.add_field_to_context(
                field_name=field_name,
                graphql_type_name=object_type.name,
                python_type=python_type,
                description=description,
                is_required=is_required,
                is_list=is_list,
                require_model_context=False,
            )

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

        self.add_field_to_context(
            field_name=field_name,
            graphql_type_name=object_type.name,
            python_type=model,
            description=description,
            is_required=is_required,
            is_list=is_list,
            require_model_context=False,
        )

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
        except PydanticModelAlreadyRegisteredError as e:
            python_type = self.get_type(e.model_name)
            # Use existing model
            self.add_field_to_context(
                field_name=field_name,
                graphql_type_name=type_name,
                python_type=python_type,
                description=description,
                is_required=is_required,
                is_list=is_list,
                # Input objects can be shared across multiple parent contexts,
                # so we shouldn't require a parent context to add them
                require_model_context=False,
            )

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

        self.add_field_to_context(
            field_name=field_name,
            graphql_type_name=input_type.name,
            python_type=model,
            description=description,
            is_required=is_required,
            is_list=is_list,
            # Input objects can be shared across multiple parent contexts,
            # so we shouldn't require a parent context to add them
            require_model_context=False,
        )

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
        # Check depth limit - unions should be skipped at max depth. We add
        # padding to account for the extra depth that will be incurred from the
        # nested union objects
        if self.should_skip_depth(padding=1):
            logger.debug(f"Skipping union %s due to depth limit {union_type.name}")
            return VisitorControl.SKIP

        logger.debug(
            f"before union depth: {self.current_depth}, union: {union_type.name}, max_depth: {self._max_depth}"
        )

        try:
            self.start_union_context(union_type.name)
        except PydanticModelAlreadyRegisteredError as e:
            existing_type = self.get_type(e.model_name)
            assert t.get_origin(existing_type) == t.Union, (
                "Expected existing type to be a Union"
            )

            self.add_field_to_context(
                field_name=field_name,
                graphql_type_name=union_type.name,
                python_type=existing_type,
                description=description,
                is_required=is_required,
                is_list=is_list,
                discriminator="typename__",
            )

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

        self.add_field_to_context(
            field_name=field_name,
            graphql_type_name=union_type.name,
            python_type=union_type_materialized,
            description=description,
            is_required=is_required,
            is_list=is_list,
            discriminator="typename__",
        )

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
        python_type = t.Any

        self.add_field_to_context(
            field_name=field_name,
            graphql_type_name=str(gql_type),
            python_type=python_type,
            description=None,
            is_required=is_required,
            is_list=is_list,
        )

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


class MutationInfoContext:
    def __init__(self, name: str, field_def: GraphQLField, description: str | None):
        self._name = name
        self._field_def = field_def
        self._description = description
        self._input_type: type[BaseModel] | None = None
        self._return_type: t.Any = None

    def set_input_type(self, input_type: type[BaseModel]) -> None:
        self._input_type = input_type

    def set_return_type(self, return_type: t.Any) -> None:
        self._return_type = return_type

    def materialize(self) -> MutationInfo:
        assert self._input_type is not None, (
            "Input type must be set before materializing"
        )
        logger.debug(
            f"Materializing mutation info for {self._name} with input type {self._input_type} and return type {self._return_type}"
        )

        return MutationInfo(
            name=self._name,
            description=self._description or "",
            input_model=self._input_type,
            payload_model=self._return_type,
        )


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
            max_depth=4,
            use_context_prefix=False,
            ignore_unknown_types=ignore_unknown_types,
        )
        self._schema = schema
        self._filters: list[MutationFilter] = filters or []
        self._mutations: list[MutationInfo] = []

        # Mutation context tracking
        self._current_mutation_context: t.Optional[MutationInfoContext] = None

    @property
    def mutations(self) -> list[MutationInfo]:
        """Get the collected mutations."""
        return self._mutations

    def handle_enter_mutation_field(
        self,
        field_name: str,
        field_def: GraphQLField,
        return_type: t.Any,
        description: str | None,
    ) -> VisitorControl:
        """Handle entering a mutation field - store context for later collection."""

        if field_name.startswith("_"):
            logger.debug(
                f"Skipping mutation field {field_name} since it starts with an underscore"
            )
            return VisitorControl.SKIP

        self._current_mutation_context = MutationInfoContext(
            name=field_name,
            field_def=field_def,
            description=description,
        )

        return VisitorControl.CONTINUE  # Let traverser visit input and return types

    def handle_enter_mutation_arguments(self, mutation_name: str):
        """Handle entering mutation arguments - store input type context."""
        self.start_model_context(f"{mutation_name}Arguments")

        return VisitorControl.CONTINUE

    def handle_leave_mutation_arguments(self, mutation_name: str):
        """Handle leaving mutation arguments - store input type context."""
        arguments_name = self.finish_context()
        input_model = self.get_type(arguments_name)
        assert self._current_mutation_context is not None
        assert is_pydantic_model_class(input_model), (
            "Expected input model to be a Pydantic model class"
        )
        self._current_mutation_context.set_input_type(input_model)

        return VisitorControl.CONTINUE

    def handle_enter_mutation_return_type(self, mutation_name: str, return_type: t.Any):
        """Handle entering mutation return type - store return type context."""
        logger.debug(
            f"Entering mutation return type for {mutation_name}: {return_type}"
        )
        self.start_model_context(f"{mutation_name}ReturnType")

        return VisitorControl.CONTINUE

    def handle_leave_mutation_return_type(self, mutation_name: str, return_type: t.Any):
        """Handle leaving mutation return type - store return type context."""
        logger.debug(f"Leaving mutation return type for {mutation_name}: {return_type}")

        return_type_model_name = self.finish_context()
        assert self._current_mutation_context is not None, (
            "Mutation context should be set"
        )
        return_type_model = self.get_type(return_type_model_name)

        self._current_mutation_context.set_return_type(return_type_model)

        return VisitorControl.CONTINUE

    def handle_leave_mutation_field(
        self,
        field_name: str,
        field_def: GraphQLField,
        return_type: t.Any,
        description: str | None,
    ) -> VisitorControl:
        """Handle leaving a mutation field - collect the mutation info."""

        assert self._current_mutation_context is not None, (
            "Mutation context on leave must be set"
        )

        mutation_info = self._current_mutation_context.materialize()

        if not any(f.should_ignore(mutation_info) for f in self._filters):
            self._mutations.append(mutation_info)

        return VisitorControl.CONTINUE
