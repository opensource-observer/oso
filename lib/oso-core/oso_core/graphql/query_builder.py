import typing as t

from .introspection import get_graphql_introspection, get_type_info
from .types import GraphQLLogger, PaginationConfig, PaginationType


class FieldExpander:
    """Helper class to expand GraphQL fields with proper handling of depth and cycles."""

    def __init__(
        self,
        logger: GraphQLLogger,
        types_dict: t.Dict[str, t.Dict[str, t.Any]],
        max_depth: int,
        pagination_config: t.Optional[PaginationConfig] = None,
        exclude_fields: t.Optional[t.List[str]] = None,
    ):
        self.logger = logger
        self.types_dict = types_dict
        self.max_depth = max_depth
        self.visited_paths: t.Set[str] = set()
        self.pagination_config = pagination_config
        self.exclude_fields = exclude_fields or []

    def expand_abstract_type(
        self,
        field_name: str,
        type_def: t.Dict[str, t.Any],
        current_path: str,
        depth: int,
        field_path: str,
    ) -> t.Optional[str]:
        """Expand UNION or INTERFACE types using inline fragments."""
        if depth >= self.max_depth:
            self.logger.warning(
                f"GraphQLFactory: Skipping abstract type '{field_name}' "
                f"because it reached max depth ({self.max_depth})"
            )
            return None

        possible_types = type_def.get("possibleTypes", [])
        if not possible_types:
            return None

        fragments = []
        for possible_type in possible_types:
            type_name = possible_type.get("name")
            if not type_name:
                continue

            concrete_type = self.types_dict.get(type_name)
            if not concrete_type:
                continue

            concrete_fields = concrete_type.get("fields", [])
            if not concrete_fields:
                continue

            expanded_fields = []
            for subfield in concrete_fields:
                expanded = self.expand_field(
                    subfield,
                    f"{current_path}.{field_name}.{type_name}",
                    depth + 1,
                    field_path,
                )
                if expanded:
                    expanded_fields.append(expanded)

            if expanded_fields:
                fields_with_typename = ["__typename"] + expanded_fields
                fragments.append(
                    f"... on {type_name} {{ {' '.join(fields_with_typename)} }}"
                )

        if fragments:
            return f"{field_name} {{ {' '.join(fragments)} }}"
        return None

    def should_expand_pagination_field(self, field_path: str) -> bool:
        """Check if a field is needed for pagination."""
        if not self.pagination_config:
            return False

        pagination_fields = []

        if self.pagination_config.type == PaginationType.OFFSET:
            if self.pagination_config.total_count_path:
                pagination_fields.append(self.pagination_config.total_count_path)

        elif self.pagination_config.type in (
            PaginationType.CURSOR,
            PaginationType.RELAY,
        ):
            pagination_fields.extend(
                [
                    self.pagination_config.next_cursor_path,
                    self.pagination_config.has_next_path,
                ]
            )

        for pagination_field in pagination_fields:
            parts = pagination_field.split(".")
            if field_path.endswith(parts[0]):
                return True

        return False

    def expand_field(
        self,
        field: t.Dict[str, t.Any],
        current_path: str = "",
        depth: int = 0,
        field_path: str = "",
    ) -> t.Optional[str]:
        """
        Expand a field in the introspection query, handling cycles and max depth.
        Returns None if the field should be skipped due to expansion limitations.

        Args:
            field: The field to expand.
            current_path: The current path in the query (for cycle detection).
            depth: Current depth in the query.
            field_path: The dot-separated path of field names for exclusion checking.

        Returns:
            The expanded field as a GraphQL query string, or None if field should be skipped.
        """
        field_name = field.get("name", "")
        if not field_name:
            return None

        full_field_path = f"{field_path}.{field_name}" if field_path else field_name

        for exclude_pattern in self.exclude_fields:
            if full_field_path == exclude_pattern or full_field_path.startswith(
                exclude_pattern + "."
            ):
                return None

        for arg in field.get("args", []):
            if arg.get("type", {}).get("kind") == "NON_NULL":
                self.logger.warning(
                    f"GraphQLFactory: Skipping field '{field_name}' in '{current_path}' "
                    f"because it has a required argument '{arg['name']}' that cannot be provided."
                )
                return None

        field_type_obj = field.get("type", {})
        if not field_type_obj:
            return field_name

        type_info = get_type_info(field_type_obj)
        field_type_name = type_info.get("name")

        needs_expansion = type_info.get("needs_expansion", False)

        if type_info.get("is_scalar", True) or not field_type_name:
            return field_name

        type_def = self.types_dict.get(field_type_name)
        if not type_def:
            return field_name

        if type_info.get("is_abstract"):
            return self.expand_abstract_type(
                field_name, type_def, current_path, depth, full_field_path
            )

        type_fields = type_def.get("fields", [])
        if not type_fields:
            return field_name

        new_path = f"{current_path}.{field_name}.{field_type_name}"
        if new_path in self.visited_paths:
            return field_name

        self.visited_paths.add(new_path)

        is_pagination_field = self.should_expand_pagination_field(field_name)

        if depth >= self.max_depth and not is_pagination_field:
            if needs_expansion:
                self.logger.warning(
                    f"GraphQLFactory: Skipping field '{field_name}' of type '{field_type_name}' in '{current_path}' "
                    f"because it requires subfields but reached max depth ({self.max_depth})."
                )
                return None
            return field_name

        expanded_fields = []
        for subfield in type_fields:
            expanded = self.expand_field(subfield, new_path, depth + 1, full_field_path)
            if expanded:
                expanded_fields.append(expanded)

        if not expanded_fields and needs_expansion:
            self.logger.warning(
                f"GraphQLFactory: Skipping field '{field_name}' of type '{field_type_name}' in '{current_path}' "
                f"because none of its subfields could be expanded."
            )
            return None

        if expanded_fields:
            return f"{field_name} {{ {' '.join(expanded_fields)} }}"

        return field_name


def get_query_parameters(
    parameters: t.Optional[t.Dict[str, t.Dict[str, t.Any]]],
    pagination_config: t.Optional[PaginationConfig] = None,
) -> tuple[str, str]:
    """
    Get the parameters for the GraphQL query.

    Args:
        parameters: The parameters for the query.
        pagination_config: The pagination configuration.

    Returns:
        A tuple with the parameter definitions and variable references.

    Raises:
        ValueError: If user-provided parameters conflict with pagination field names.
    """
    all_params = {}

    if parameters:
        all_params.update(parameters)

    if pagination_config:
        pagination_fields = []

        if pagination_config.type == PaginationType.NONE:
            pass
        elif pagination_config.type == PaginationType.OFFSET:
            pagination_fields = [
                pagination_config.offset_field,
                pagination_config.limit_field,
            ]
            all_params[pagination_config.offset_field] = {
                "type": "Int",
                "value": 0,
            }
            all_params[pagination_config.limit_field] = {
                "type": "Int!",
                "value": pagination_config.page_size,
            }
        elif pagination_config.type in (PaginationType.CURSOR, PaginationType.RELAY):
            pagination_fields = [
                pagination_config.cursor_field,
                pagination_config.page_size_field,
            ]
            all_params[pagination_config.cursor_field] = {
                "type": "String",
                "value": None,
            }
            all_params[pagination_config.page_size_field] = {
                "type": "Int!",
                "value": pagination_config.page_size,
            }
        elif pagination_config.type == PaginationType.KEYSET:
            pagination_fields = [
                "orderBy",
                "orderDirection",
                pagination_config.page_size_field,
                "where",
            ]
            all_params["orderBy"] = {
                "type": "String!",
                "value": None,
            }
            all_params["orderDirection"] = {
                "type": "String!",
                "value": pagination_config.order_direction,
            }
            all_params[pagination_config.page_size_field] = {
                "type": "Int!",
                "value": pagination_config.page_size,
            }
            all_params["where"] = {
                "type": "Domain_filter",
                "value": {pagination_config.order_by_field: 0},
            }

        if parameters:
            conflicts = set(parameters.keys()) & set(pagination_fields)
            if conflicts:
                conflict_list = ", ".join(f"'{field}'" for field in sorted(conflicts))
                raise ValueError(
                    f"Parameter name conflict: {conflict_list} cannot be used "
                    f"as user parameters because they are reserved for "
                    f"pagination. Remove them from the parameters configuration "
                    f"or change the pagination field names."
                )

    if not all_params:
        return "", ""

    param_defs = ", ".join(
        [f"${key}: {value['type']}" for key, value in all_params.items()]
    )
    param_refs = ", ".join([f"{key}: ${key}" for key in all_params])

    return f"({param_defs})", f"({param_refs})"


class GraphQLQueryBuilder:
    """Builds complete GraphQL queries from configuration."""

    def __init__(
        self,
        logger: GraphQLLogger,
        introspection_fetcher: t.Optional[
            t.Callable[
                [str, t.Optional[t.Tuple[t.Tuple[str, str], ...]], int],
                t.Dict[str, t.Any],
            ]
        ] = None,
    ):
        """
        Initialize the query builder.

        Args:
            logger: Logger instance with debug/info/warning/error methods.
            introspection_fetcher: Optional custom function to fetch introspection.
                Defaults to get_graphql_introspection if not provided.
        """
        self.logger = logger
        self.introspection_fetcher = introspection_fetcher or get_graphql_introspection

    def build_query(
        self,
        endpoint: str,
        headers_tuple: t.Optional[t.Tuple[t.Tuple[str, str], ...]],
        target_type: str,
        target_query: str,
        max_depth: int,
        parameters: t.Optional[t.Dict[str, t.Dict[str, t.Any]]],
        pagination_config: t.Optional[PaginationConfig],
        exclude_fields: t.Optional[t.List[str]],
    ) -> str:
        """
        Build a complete GraphQL query from configuration.

        Args:
            endpoint: The GraphQL endpoint URL.
            headers_tuple: Headers as a tuple of tuples for hashability.
            target_type: The type to target in the introspection query.
            target_query: The query to target in the main query.
            max_depth: Maximum depth for field expansion.
            parameters: Optional query parameters.
            pagination_config: Optional pagination configuration.
            exclude_fields: Optional list of field patterns to exclude.

        Returns:
            The generated GraphQL query string.

        Raises:
            ValueError: If validation fails or query cannot be built.
        """
        introspection = self.introspection_fetcher(endpoint, headers_tuple, max_depth)

        available_types = introspection["__schema"]["types"]
        if not available_types:
            raise ValueError("Malformed introspection query, no types found.")

        dictionary_types = {type_obj["name"]: type_obj for type_obj in available_types}

        target_object = dictionary_types.get(target_type)
        if not target_object:
            raise ValueError(
                f"Target type '{target_type}' not found in the introspection query."
            )

        target_field = next(
            (f for f in target_object.get("fields", []) if f["name"] == target_query),
            None,
        )
        if not target_field:
            raise ValueError(
                f"Target query '{target_query}' not found in type '{target_type}'."
            )

        type_info = get_type_info(target_field.get("type", {}))
        return_type_name = type_info.get("name")
        if not return_type_name:
            raise ValueError(
                f"Could not determine return type for query '{target_query}'."
            )

        return_type_def = dictionary_types.get(return_type_name)
        if not return_type_def:
            raise ValueError(f"Type '{return_type_name}' not found in schema.")

        field_expander = FieldExpander(
            self.logger,
            dictionary_types,
            max_depth,
            pagination_config,
            exclude_fields,
        )

        expanded_fields = []
        if return_type_def.get("fields"):
            for field in return_type_def.get("fields", []):
                expanded = field_expander.expand_field(field, "", 0, "")
                if expanded:
                    expanded_fields.append(expanded)

        query_parameters, query_variables = get_query_parameters(
            parameters, pagination_config
        )

        selection_set = ""
        if expanded_fields:
            selection_set = f" {{ {' '.join(expanded_fields)} }}"
        elif return_type_def.get("kind") == "OBJECT":
            raise ValueError(
                f"Could not expand any fields for query '{target_query}' with return type '{return_type_name}'. "
                "This might be because all sub-fields require arguments, are excluded, or max_depth is too low."
            )

        generated_body = f"{{ {target_query}{query_variables}{selection_set} }}"
        generated_query = f"query {query_parameters} {generated_body}"

        return generated_query
