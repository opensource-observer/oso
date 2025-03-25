from dataclasses import dataclass
from typing import (
    Any,
    Callable,
    Concatenate,
    Dict,
    List,
    Optional,
    ParamSpec,
    Set,
    TypeVar,
    cast,
)

import dlt
from dagster import AssetExecutionContext
from gql import Client, gql
from gql.transport.exceptions import TransportError
from gql.transport.requests import RequestsHTTPTransport

from .dlt import dlt_factory

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
    """

    # TODO(jabolo): Add ability to pass secrets
    name: str
    endpoint: str
    target_type: str
    target_query: str
    max_depth: int = 5
    headers: Optional[Dict[str, str]] = None
    transform_fn: Optional[Callable[[Any], Any]] = None
    parameters: Optional[Dict[str, Dict[str, Any]]] = None


def get_graphql_introspection(config: GraphQLResourceConfig) -> Dict[str, Any]:
    """
    Fetch the GraphQL introspection query from the given endpoint.

    Args:
        config: The configuration for the GraphQL resource.

    Returns:
        The introspection query result.
    """

    transport = RequestsHTTPTransport(
        url=config.endpoint,
        use_json=True,
        headers=config.headers,
        timeout=300,
    )

    client = Client(
        transport=transport,
        fetch_schema_from_transport=True,
    )

    populated_query = INTROSPECTION_QUERY.replace(
        "{{ DEPTH }}", create_fragment(config.max_depth + 5)
    )

    try:
        return client.execute(gql(populated_query))
    except TransportError as exception:
        raise ValueError(
            f"Failed to fetch GraphQL introspection query from {config.endpoint}.",
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
    ):
        self.context = context
        self.types_dict = types_dict
        self.max_depth = max_depth
        self.visited_paths: Set[str] = set()

    def expand_field(
        self, field: Dict[str, Any], current_path: str = "", depth: int = 0
    ) -> Optional[str]:
        """
        Expand a field in the introspection query, handling cycles and max depth.
        Returns None if the field should be skipped due to expansion limitations.

        Args:
            field: The field to expand.
            current_path: The current path in the query (for cycle detection).
            depth: Current depth in the query.

        Returns:
            The expanded field as a GraphQL query string, or None if field should be skipped.
        """
        field_name = field.get("name", "")
        if not field_name:
            return None

        # TODO(jabolo): Handle field arguments
        field_args = field.get("args", [])
        if field_args:
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

        if depth >= self.max_depth:
            if needs_expansion:
                self.context.log.warning(
                    f"GraphQLFactory: Skipping field '{field_name}' of type '{field_type_name}' because it "
                    f"requires subfields but reached max depth ({self.max_depth})."
                )
                return None
            return field_name

        expanded_fields = []
        for subfield in type_fields:
            expanded = self.expand_field(subfield, new_path, depth + 1)
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
) -> tuple[str, str]:
    """
    Get the parameters for the GraphQL query.

    Args:
        parameters: The parameters for the query.

    Returns:
        A tuple with the parameter definitions and variable references.
    """
    if not parameters:
        return "", ""

    param_defs = ", ".join(
        [f'${key}: {value["type"]}' for key, value in parameters.items()]
    )
    param_refs = ", ".join([f"{key}: ${key}" for key in parameters.keys()])

    return f"({param_defs})", f"({param_refs})"


Q = ParamSpec("Q")
T = TypeVar("T")


def _graphql_factory(
    _resource: Callable[Q, T],
) -> Callable[Concatenate[GraphQLResourceConfig, Q], T]:
    """
    This factory creates a DLT asset from a GraphQL resource, automatically
    wiring the introspection query to the target query and generating a Pydantic model.

    Args:
        resource: The function to decorate.
    """

    def _factory(config: GraphQLResourceConfig, /, *_args: Q.args, **kwargs: Q.kwargs):
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

        @dlt_factory(name=config.name, **kwargs)
        def _dlt_graphql_asset(context: AssetExecutionContext):
            """
            The GraphQLFactory for the DLT asset.

            Args:
                context: The asset execution context.

            Returns:
                The DLT asset.
            """

            introspection = get_graphql_introspection(config)

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

            type_to_python = TypeToPython(available_types)

            field_expander = FieldExpander(context, dictionary_types, config.max_depth)

            expanded_fields = []
            field_types = []

            context.log.info(
                f"Starting field expansion for type '{config.target_type}'"
            )

            for field in target_object.get("fields", []):
                expanded = field_expander.expand_field(field)

                if expanded:
                    expanded_fields.append(expanded)
                    field_types.append(
                        (
                            field.get("name"),
                            resolve_type(field.get("type"), type_to_python),
                        )
                    )
                else:
                    field_name = field.get("name", "")
                    context.log.warning(
                        f"GraphQLFactory: Field '{field_name}' was skipped in the query."
                    )

            query_parameters, query_variables = get_query_parameters(config.parameters)

            generated_body = f"{{ {config.target_query} {query_variables} {{ {" ".join(expanded_fields)} }} }}"
            generated_query = f"query {query_parameters} {generated_body}"

            # TODO(jabolo): Pass dynamic DLT config
            @dlt.resource(
                name=config.name,
            )
            def _execute_query():
                """
                Execute the GraphQL query.

                Returns:
                    The GraphQL query result
                """
                transport = RequestsHTTPTransport(
                    url=config.endpoint,
                    use_json=True,
                    headers=config.headers,
                )

                client = Client(transport=transport)

                context.log.info(
                    f"GraphQLFactory: fetching data from {config.endpoint}"
                )
                context.log.info(
                    f"GraphQLFactory: generated query:\n\n{generated_query}"
                )

                try:
                    result = client.execute(
                        gql(generated_query),
                        variable_values={
                            key: param["value"]
                            for key, param in (config.parameters or {}).items()
                        },
                    )

                    processed_result = (
                        config.transform_fn(result) if config.transform_fn else result
                    )

                    if isinstance(processed_result, list):
                        yield from processed_result
                    else:
                        yield processed_result

                except TransportError as e:
                    context.log.error(f"GraphQL query execution failed: {str(e)}")
                    raise ValueError(
                        f"Failed to execute GraphQL query: {str(e)}"
                    ) from e

            yield _execute_query

        return _dlt_graphql_asset

    return cast(Callable[Concatenate[GraphQLResourceConfig, Q], T], _factory)


graphql_factory = _graphql_factory(dlt_factory)
