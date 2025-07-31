import time
from dataclasses import dataclass
from enum import Enum
from functools import cache
from typing import (
    Any,
    Callable,
    Concatenate,
    Dict,
    Generator,
    List,
    Optional,
    ParamSpec,
    Set,
    Tuple,
    TypeVar,
    cast,
)

import dlt
from dagster import AssetExecutionContext
from dlt.extract.resource import DltResource
from gql import Client, gql
from gql.transport.exceptions import TransportError
from gql.transport.requests import RequestsHTTPTransport

# The maximum depth of the introspection query.
FRAGMENT_MAX_DEPTH = 10

# The introspection query to fetch the schema of a GraphQL resource.
INTROSPECTION_QUERY = """
  query IntrospectionQuery {
    __schema {
      queryType { name }
      mutationType { name }
      subscriptionType { name }
      types {
        ...FullType
      }
      directives {
        name
        description
        locations
        args {
          ...InputValue
        }
      }
    }
  }
  fragment FullType on __Type {
    kind
    name
    description
    fields(includeDeprecated: true) {
      name
      description
      args {
        ...InputValue
      }
      type {
        ...TypeRef
      }
      isDeprecated
      deprecationReason
    }
    inputFields {
      ...InputValue
    }
    interfaces {
      ...TypeRef
    }
    enumValues(includeDeprecated: true) {
      name
      description
      isDeprecated
      deprecationReason
    }
    possibleTypes {
      ...TypeRef
    }
  }
  fragment InputValue on __InputValue {
    name
    description
    type { ...TypeRef }
    defaultValue
  }
  fragment TypeRef on __Type {
    {{ DEPTH }}
  }
"""


class PaginationType(Enum):
    """Supported pagination types."""

    OFFSET = "offset"
    CURSOR = "cursor"
    RELAY = "relay"


@dataclass
class PaginationConfig:
    """
    Configuration for pagination in GraphQL queries.

    Args:
        type: The type of pagination (offset, cursor, or relay).
        page_size: Number of items per page.
        max_pages: Maximum number of pages to fetch (None for unlimited).
        rate_limit_seconds: Seconds to wait between page requests.

        For offset-based pagination:
        offset_field: Name of the offset field (default: "offset").
        limit_field: Name of the limit field (default: "limit").
        total_count_path: Path to total count field (e.g., "totalCount").

        For cursor-based pagination:
        cursor_field: Name of the cursor field (default: "after").
        page_size_field: Name of the page size field (default: "first").
        next_cursor_path: Path to next cursor value (e.g., "pageInfo.endCursor").
        has_next_path: Path to hasNext field (e.g., "pageInfo.hasNextPage").

        For relay-style pagination:
        Uses cursor-based fields but expects standard Relay connection structure.
        edge_path: Path to edges array (default: "edges").
        node_path: Path to node within edge (default: "node").
    """

    type: PaginationType
    page_size: int = 50
    max_pages: Optional[int] = None
    rate_limit_seconds: float = 0.0

    offset_field: str = "offset"
    limit_field: str = "limit"
    total_count_path: Optional[str] = None

    cursor_field: str = "after"
    page_size_field: str = "first"
    next_cursor_path: str = "pageInfo.endCursor"
    has_next_path: str = "pageInfo.hasNextPage"

    edge_path: str = "edges"
    node_path: str = "node"

    stop_condition: Optional[Callable[[Dict[str, Any], int], bool]] = None


@dataclass
class GraphQLResourceConfig:
    """
    Configuration for a GraphQL resource.

    Args:
        name: The name of the GraphQL resource.
        endpoint: The endpoint of the GraphQL resource.
        target_type: The type to target in the introspection query.
        target_query: The query to target in the main query.
        max_depth: The maximum depth of the GraphQL query.
        headers: The headers to include in the introspection query.
        transform_fn: The function to transform the result of the query.
        parameters: The parameters to include in the introspection query.
        pagination: The pagination configuration.
        exclude: Fields to exclude from the GraphQL schema expansion.
        deps_rate_limit_seconds: Seconds to wait between dependency calls.
        deps: Dependencies for the GraphQL resource. If provided, the main query results
              will be used as intermediate data to feed the dependencies, and those
              intermediate rows will be skipped from the final output. The factory can
              only return one consistent data shape, so deps serve as a means to transform
              the intermediate data into the final desired output format.
    """

    name: str
    endpoint: str
    target_type: str
    target_query: str
    max_depth: int = 5
    headers: Optional[Dict[str, str]] = None
    transform_fn: Optional[Callable[[Any], Any]] = None
    parameters: Optional[Dict[str, Dict[str, Any]]] = None
    pagination: Optional[PaginationConfig] = None
    exclude: Optional[List[str]] = None
    deps_rate_limit_seconds: float = 0.0
    deps: Optional[
        List[
            Callable[
                [AssetExecutionContext, Any],
                Generator[Any, Any, Any],
            ]
        ]
    ] = None


def create_fragment(depth: int, max_depth=FRAGMENT_MAX_DEPTH) -> str:
    """
    Create a fragment for the GraphQL introspection query
    that recurses to a given depth.

    Args:
        depth: The depth of the fragment.
        max_depth: The maximum depth of the fragment, defaults to `FRAGMENT_MAX_DEPTH`.

    Returns:
        A string with the GraphQL fragment at the specified depth.
    """

    if depth <= 0 or depth > max_depth:
        return ""

    if depth == 1:
        return "kind name"

    return f"kind name ofType {{ {create_fragment(depth - 1)} }}"


@cache
def get_graphql_introspection(
    endpoint: str, headers_tuple: Optional[Tuple[Tuple[str, str], ...]], max_depth: int
) -> Dict[str, Any]:
    """
    Fetch the GraphQL introspection query from the given endpoint.

    Args:
        endpoint: The GraphQL endpoint URL.
        headers_tuple: Headers as a tuple of tuples for hashability.
        max_depth: Maximum depth for the introspection query.

    Returns:
        The introspection query result.
    """
    headers_dict = dict(headers_tuple) if headers_tuple else None

    transport = RequestsHTTPTransport(
        url=endpoint,
        use_json=True,
        headers=headers_dict,
        timeout=300,
    )

    client = Client(
        transport=transport,
        fetch_schema_from_transport=True,
    )

    populated_query = INTROSPECTION_QUERY.replace(
        "{{ DEPTH }}", create_fragment(max_depth + 5)
    )

    try:
        return client.execute(gql(populated_query))
    except TransportError as exception:
        raise ValueError(
            f"Failed to fetch GraphQL introspection query from {endpoint}.",
        ) from exception


@dataclass(frozen=True)
class _TypeToPython:
    String = "str"
    Int = "int"
    Float = "float"
    Boolean = "bool"
    Date = "date"
    DateTime = "datetime"
    ID = "str"


class TypeToPython:
    """
    A mapping of GraphQL types to Python types.

    Args:
        available_types: The available types in the introspection query.
    """

    def __init__(self, available_types: List[Dict[str, Any]]):
        self.available_types = available_types
        self._scalar_types = {
            attr: getattr(_TypeToPython, attr)
            for attr in dir(_TypeToPython)
            if not attr.startswith("_")
        }

    def __getitem__(self, name: str) -> str:
        """
        Get the Python type for the given GraphQL type.

        Args:
            name: The name of the GraphQL type.

        Returns:
            The Python type for the given GraphQL type.
        """
        if name in self._scalar_types:
            return self._scalar_types[name]

        is_object = next(
            (type_obj for type_obj in self.available_types if type_obj["name"] == name),
            None,
        )

        return f'"{name}"' if is_object else "Any"


def get_type_info(graphql_type: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract core type information from a GraphQL type, handling NULL and LIST wrappers.

    Args:
        graphql_type: The GraphQL type object.

    Returns:
        A dictionary with the core type information.
    """
    if not graphql_type:
        return {
            "kind": "UNKNOWN",
            "name": None,
            "needs_expansion": False,
        }

    if graphql_type["kind"] in ("NON_NULL", "LIST"):
        if "ofType" not in graphql_type or not graphql_type["ofType"]:
            return {
                "kind": graphql_type["kind"],
                "name": None,
                "is_scalar": False,
            }

        inner_type = get_type_info(graphql_type["ofType"])
        return {
            "kind": graphql_type["kind"],
            "wrapped_kind": inner_type["kind"],
            "name": inner_type["name"],
            "is_scalar": inner_type.get("is_scalar", False),
            "needs_expansion": graphql_type["kind"] == "LIST"
            or inner_type.get("needs_expansion", False),
        }

    if graphql_type["kind"] == "OBJECT":
        return {
            "kind": graphql_type["kind"],
            "name": graphql_type["name"],
            "is_scalar": False,
            "needs_expansion": True,
        }

    is_scalar = graphql_type["kind"] in ("SCALAR", "ENUM")
    return {
        "kind": graphql_type["kind"],
        "name": graphql_type["name"],
        "is_scalar": is_scalar,
        "needs_expansion": not is_scalar,
    }


def resolve_type(graphql_type: Dict[str, Any], type_mapper: TypeToPython) -> str:
    """
    Resolve the type of a GraphQL field to a Python type annotation.

    Args:
        graphql_type: The GraphQL type.
        type_mapper: The instance of the TypeToPython class.

    Returns:
        The Python type annotation for the given GraphQL type.
    """
    if not graphql_type:
        return "Any"

    if graphql_type["kind"] == "NON_NULL":
        if "ofType" not in graphql_type or not graphql_type["ofType"]:
            return "Any"
        return resolve_type(graphql_type["ofType"], type_mapper)

    if graphql_type["kind"] == "LIST":
        if "ofType" not in graphql_type or not graphql_type["ofType"]:
            return "List[Any]"
        inner_type = resolve_type(graphql_type["ofType"], type_mapper)
        return f"List[{inner_type}]"

    if graphql_type["kind"] == "ENUM":
        return "str"

    type_name = graphql_type.get("name")
    if not type_name:
        return "Any"

    return type_mapper[type_name]


class FieldExpander:
    """
    Helper class to expand GraphQL fields with proper handling of depth and cycles.
    """

    def __init__(
        self,
        context: AssetExecutionContext,
        types_dict: Dict[str, Dict[str, Any]],
        max_depth: int,
        pagination_config: Optional[PaginationConfig] = None,
        exclude_fields: Optional[List[str]] = None,
    ):
        self.context = context
        self.types_dict = types_dict
        self.max_depth = max_depth
        self.visited_paths: Set[str] = set()
        self.pagination_config = pagination_config
        self.exclude_fields = exclude_fields or []

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
        field: Dict[str, Any],
        current_path: str = "",
        depth: int = 0,
        field_path: str = "",
    ) -> Optional[str]:
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
                self.context.log.warning(
                    f"GraphQLFactory: Skipping field '{field_name}' because it has a required argument '{arg['name']}' that cannot be provided."
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
                self.context.log.warning(
                    f"GraphQLFactory: Skipping field '{field_name}' of type '{field_type_name}' because it "
                    f"requires subfields but reached max depth ({self.max_depth})."
                )
                return None
            return field_name

        expanded_fields = []
        for subfield in type_fields:
            expanded = self.expand_field(subfield, new_path, depth + 1, full_field_path)
            if expanded:
                expanded_fields.append(expanded)

        if not expanded_fields and needs_expansion:
            self.context.log.warning(
                f"GraphQLFactory: Skipping field '{field_name}' of type '{field_type_name}' "
                f"because none of its subfields could be expanded."
            )
            return None

        if expanded_fields:
            return f"{field_name} {{ {' '.join(expanded_fields)} }}"

        return field_name


def get_query_parameters(
    parameters: Optional[Dict[str, Dict[str, Any]]],
    pagination_config: Optional[PaginationConfig] = None,
) -> tuple[str, str]:
    """
    Get the parameters for the GraphQL query.

    Args:
        parameters: The parameters for the query.
        pagination_config: The pagination configuration.

    Returns:
        A tuple with the parameter definitions and variable references.
    """
    all_params = {}

    if parameters:
        all_params.update(parameters)

    if pagination_config:
        if pagination_config.type == PaginationType.OFFSET:
            all_params[pagination_config.offset_field] = {
                "type": "Int",
                "value": 0,
            }
            all_params[pagination_config.limit_field] = {
                "type": "Int!",
                "value": pagination_config.page_size,
            }
        elif pagination_config.type in (PaginationType.CURSOR, PaginationType.RELAY):
            all_params[pagination_config.cursor_field] = {
                "type": "String",
                "value": None,
            }
            all_params[pagination_config.page_size_field] = {
                "type": "Int!",
                "value": pagination_config.page_size,
            }

    if not all_params:
        return "", ""

    param_defs = ", ".join(
        [f"${key}: {value['type']}" for key, value in all_params.items()]
    )
    param_refs = ", ".join([f"{key}: ${key}" for key in all_params])

    return f"({param_defs})", f"({param_refs})"


def get_nested_value(data: Dict[str, Any], path: str) -> Any:
    """Get a value from nested dictionary using dot notation path."""
    keys = path.split(".")
    value = data

    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None

    return value


def extract_data_for_pagination(
    result: Dict[str, Any],
    config: GraphQLResourceConfig,
) -> tuple[List[Any], Optional[Dict[str, Any]]]:
    """
    Extract data and pagination info from the result.

    Returns:
        A tuple of (data_items, pagination_info)
    """
    if config.transform_fn:
        data = config.transform_fn(result)
    else:
        data = result.get(config.target_query, [])

    if not isinstance(data, list):
        if config.pagination and config.pagination.type == PaginationType.RELAY:
            edges = get_nested_value(data, config.pagination.edge_path) or []
            data = [
                get_nested_value(edge, config.pagination.node_path) for edge in edges
            ]
        else:
            data = [data] if data else []

    pagination_info = None
    if config.pagination:
        if config.pagination.type == PaginationType.OFFSET:
            total_count = None
            if config.pagination.total_count_path:
                total_count = get_nested_value(
                    result.get(config.target_query, {}),
                    config.pagination.total_count_path,
                )
            pagination_info = {"total_count": total_count}

        elif config.pagination.type in (PaginationType.CURSOR, PaginationType.RELAY):
            target_data = result.get(config.target_query, {})
            next_cursor = get_nested_value(
                target_data, config.pagination.next_cursor_path
            )
            has_next = get_nested_value(target_data, config.pagination.has_next_path)

            pagination_info = {
                "next_cursor": next_cursor,
                "has_next": has_next,
            }

    return data, pagination_info


Q = ParamSpec("Q")
T = TypeVar("T")


def _graphql_factory(
    _resource: Callable[Q, T],
) -> Callable[
    Concatenate[GraphQLResourceConfig, AssetExecutionContext, Q], DltResource
]:
    """
    This factory creates a DLT asset from a GraphQL resource, automatically
    wiring the introspection query to the target query and generating a Pydantic model.

    Args:
        resource: The function to decorate.
    """

    def _factory(
        config: GraphQLResourceConfig,
        context: AssetExecutionContext,
        /,
        *_args: Q.args,
        **kwargs: Q.kwargs,
    ):
        """
        Wrap the decorated function with the GraphQLFactory.

        Args:
            config: The configuration for the GraphQL resource.
            *_args: The arguments for the decorated function.
            **kwargs: The keyword arguments for the decorated function.

        Returns:
            The DLT asset.
        """

        if not config.target_query or not config.target_query.strip():
            raise ValueError(
                "Target query not specified in the GraphQL resource config."
            )

        if not config.target_type or not config.target_type.strip():
            raise ValueError(
                "Target type not specified in the GraphQL resource config."
            )

        @dlt.resource(name=config.name, **kwargs)
        def _execute_query():
            """
            Execute the GraphQL query.

            Returns:
                The GraphQL query result
            """

            headers_tuple = (
                tuple(sorted(config.headers.items())) if config.headers else None
            )
            introspection = get_graphql_introspection(
                config.endpoint, headers_tuple, config.max_depth
            )

            available_types = introspection["__schema"]["types"]
            if not available_types:
                raise ValueError("Malformed introspection query, no types found.")

            dictionary_types = {
                type_obj["name"]: type_obj for type_obj in available_types
            }

            target_object = dictionary_types.get(config.target_type)
            if not target_object:
                raise ValueError(
                    f"Target type '{config.target_type}' not found in the introspection query."
                )

            target_field = next(
                (
                    f
                    for f in target_object.get("fields", [])
                    if f["name"] == config.target_query
                ),
                None,
            )
            if not target_field:
                raise ValueError(
                    f"Target query '{config.target_query}' not found in type '{config.target_type}'."
                )

            type_info = get_type_info(target_field.get("type", {}))
            return_type_name = type_info.get("name")
            if not return_type_name:
                raise ValueError(
                    f"Could not determine return type for query '{config.target_query}'."
                )

            return_type_def = dictionary_types.get(return_type_name)
            if not return_type_def:
                raise ValueError(f"Type '{return_type_name}' not found in schema.")

            field_expander = FieldExpander(
                context,
                dictionary_types,
                config.max_depth,
                config.pagination,
                config.exclude,
            )

            expanded_fields = []
            if return_type_def.get("fields"):
                for field in return_type_def.get("fields", []):
                    expanded = field_expander.expand_field(field, "", 0, "")
                    if expanded:
                        expanded_fields.append(expanded)

            query_parameters, query_variables = get_query_parameters(
                config.parameters, config.pagination
            )

            selection_set = ""
            if expanded_fields:
                selection_set = f" {{ {' '.join(expanded_fields)} }}"
            elif return_type_def.get("kind") == "OBJECT":
                raise ValueError(
                    f"Could not expand any fields for query '{config.target_query}' with return type '{return_type_name}'. "
                    "This might be because all sub-fields require arguments, are excluded, or max_depth is too low."
                )

            generated_body = (
                f"{{ {config.target_query}{query_variables}{selection_set} }}"
            )
            generated_query = f"query {query_parameters} {generated_body}"

            transport = RequestsHTTPTransport(
                url=config.endpoint,
                use_json=True,
                headers=config.headers,
            )

            client = Client(transport=transport)

            context.log.info(f"GraphQLFactory: fetching data from {config.endpoint}")
            context.log.info(f"GraphQLFactory: generated query:\n\n{generated_query}")

            variables = {
                key: param["value"] for key, param in (config.parameters or {}).items()
            }

            page_count = 0
            total_items = 0
            has_more = True

            while has_more:
                try:
                    if config.pagination:
                        if config.pagination.type == PaginationType.OFFSET:
                            variables[config.pagination.offset_field] = (
                                page_count * config.pagination.page_size
                            )
                            variables[config.pagination.limit_field] = (
                                config.pagination.page_size
                            )
                        elif config.pagination.type in (
                            PaginationType.CURSOR,
                            PaginationType.RELAY,
                        ):
                            if page_count > 0 or variables.get(
                                config.pagination.cursor_field
                            ):
                                pass
                            else:
                                variables[config.pagination.cursor_field] = None
                            variables[config.pagination.page_size_field] = (
                                config.pagination.page_size
                            )

                    result = client.execute(
                        gql(generated_query),
                        variable_values=variables,
                    )

                    data_items, pagination_info = extract_data_for_pagination(
                        result, config
                    )

                    if isinstance(data_items, list):
                        for item_idx, item in enumerate(data_items):
                            total_items += 1
                            if config.deps:
                                if item_idx > 0 and config.deps_rate_limit_seconds > 0:
                                    time.sleep(config.deps_rate_limit_seconds)
                                for i, dep in enumerate(config.deps):
                                    if i > 0 and config.deps_rate_limit_seconds > 0:
                                        time.sleep(config.deps_rate_limit_seconds)
                                    yield from dep(context, item)
                            else:
                                yield item
                    else:
                        total_items += 1
                        if config.deps:
                            for i, dep in enumerate(config.deps):
                                if i > 0 and config.deps_rate_limit_seconds > 0:
                                    time.sleep(config.deps_rate_limit_seconds)
                                yield from dep(context, data_items)
                        else:
                            yield data_items

                    page_count += 1

                    if not config.pagination:
                        has_more = False
                    elif config.pagination.stop_condition:
                        has_more = not config.pagination.stop_condition(
                            result, page_count
                        )
                    elif (
                        config.pagination.max_pages
                        and page_count >= config.pagination.max_pages
                    ):
                        has_more = False
                        context.log.info(
                            f"GraphQLFactory: Reached max pages limit ({config.pagination.max_pages})"
                        )
                    elif config.pagination.type == PaginationType.OFFSET:
                        if (
                            pagination_info
                            and pagination_info.get("total_count") is not None
                        ):
                            current_offset = page_count * config.pagination.page_size
                            has_more = current_offset < pagination_info["total_count"]
                        else:
                            has_more = len(data_items) == config.pagination.page_size
                    elif config.pagination.type in (
                        PaginationType.CURSOR,
                        PaginationType.RELAY,
                    ):
                        if pagination_info:
                            has_more = bool(
                                pagination_info.get("has_next", False)
                                and pagination_info.get("next_cursor")
                            )
                            if has_more:
                                variables[config.pagination.cursor_field] = (
                                    pagination_info["next_cursor"]
                                )
                        else:
                            has_more = False

                    if (
                        has_more
                        and config.pagination
                        and config.pagination.rate_limit_seconds > 0
                    ):
                        time.sleep(config.pagination.rate_limit_seconds)

                    context.log.info(
                        f"GraphQLFactory: Fetched page {page_count} with {len(data_items)} items "
                        f"(total: {total_items})"
                    )

                except TransportError as e:
                    context.log.error(f"GraphQL query execution failed: {str(e)}")
                    raise ValueError(
                        f"Failed to execute GraphQL query: {str(e)}"
                    ) from e

            context.log.info(
                f"GraphQLFactory: Completed fetching {total_items} total items"
            )

        return _execute_query

    return cast(
        Callable[
            Concatenate[GraphQLResourceConfig, AssetExecutionContext, Q], DltResource
        ],
        _factory,
    )


graphql_factory = _graphql_factory(dlt.resource)
