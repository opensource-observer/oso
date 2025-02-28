from dataclasses import dataclass
from typing import Any, Callable, Concatenate, Dict, Optional, ParamSpec, TypeVar, cast

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


def get_grapqhl_introspection(config: GraphQLResourceConfig) -> Dict[str, Any]:
    """
    Fetch the GraphQL introspection query from the given endpoint.

    Args:
        config: The configuration for the GraphQL resource.

    Returns:
        The introspection query.
    """

    transport = RequestsHTTPTransport(
        url=config.endpoint,
        use_json=True,
        headers=config.headers,
    )

    client = Client(
        transport=transport,
        fetch_schema_from_transport=True,
    )

    populated_query = INTROSPECTION_QUERY.replace(
        "{{ DEPTH }}", create_fragment(config.max_depth + 1)
    )

    try:
        return client.execute(gql(populated_query))
    except TransportError as exception:
        raise ValueError(
            "Failed to fetch GraphQL introspection query.",
        ) from exception


@dataclass(frozen=True)
class _TypeToPython:
    String = "str"
    Int = "int"
    Float = "float"
    Boolean = "bool"
    Date = "date"
    DateTime = "datetime"


class TypeToPython:
    """
    A mapping of GraphQL types to Python types.

    Args:
        available_types: The available types in the introspection query.

    Returns:
        The Python type for the given GraphQL type.
    """

    def __init__(self, available_types):
        self.available_types = available_types

    def __getitem__(self, name: str) -> str:
        if name in _TypeToPython.__dict__:
            return _TypeToPython.__dict__[name]

        is_object = next(
            (type for type in self.available_types if type["name"] == name),
            None,
        )

        return f'"{name}"' if is_object else "Any"


def resolve_type(graphql_type: Any, instance: TypeToPython) -> str:
    """
    Resolve the type of a GraphQL field.

    Args:
        graphql_type: The GraphQL type.
        instance: The instance of the TypeToPython class.

    Returns:
        The Python type for the given GraphQL type.
    """

    if graphql_type["kind"] == "NON_NULL":
        return resolve_type(graphql_type["ofType"], instance)
    if graphql_type["kind"] == "LIST":
        return (
            f"List[{resolve_type(graphql_type["ofType"], instance)}]"
            if "ofType" in graphql_type
            else "Any"
        )
    if graphql_type["kind"] == "ENUM":
        return "str"

    return instance[graphql_type["name"]]


def expand_field(
    field: Dict[str, Any],
    introspection_dict: Dict[str, Any],
    max_depth=FRAGMENT_MAX_DEPTH,
) -> str:
    """
    Expand a field in the introspection query.

    Args:
        field: The field to expand.
        introspection_dict: The introspection dictionary.
        max_depth: The maximum depth of the introspection query.

    Returns:
        The expanded field.
    """

    field_name = field.get("name", "")

    if max_depth == 0:
        return field_name

    field_type = (
        field.get("type", {}).get("ofType", {}).get("name")
        if field.get("type", {}).get("name") is None
        else field.get("type", {}).get("name")
    )

    field_args = field.get("args")
    if field_args:
        # TODO(jabolo): Support input arguments in the query
        return ""

    if not field_type:
        return ""

    intro_type = introspection_dict.get(field_type)
    if not intro_type:
        raise ValueError(
            f"Type '{field_type}' not found in the introspection query.",
        )

    type_fields = intro_type.get("fields")
    if not type_fields:
        return f"{field_name}"

    if max_depth == 1:
        return ""

    return f"{field_name} {{ {' '.join([
        expand_field(f, introspection_dict, max_depth - 1) for f in type_fields
    ])} }}"


def get_query_parameters(parameters: Optional[Dict[str, Dict[str, Any]]]):
    """
    Get the parameters for the GraphQL query.

    Args:
        parameters: The parameters for the query.

    Returns:
        The parameters for the query.
    """

    if not parameters:
        return "", ""

    return (
        f"({', '.join([f'${key}: {value['type']}' for key, value in parameters.items()])})",
        f"({', '.join([f'{key}: ${key}' for key in parameters.keys()])})",
    )


Q = ParamSpec("Q")
T = TypeVar("T")


def _graphql_factory(
    _resource: Callable[Q, T]
) -> Callable[Concatenate[GraphQLResourceConfig, Q], T]:
    """
    This factory creates a DLT asset from a GraphQL resource, automatically
    wiring the introspection query to the target query and generating a Pydantic model.

    Args:
        resource: The function to decorate.
    """

    def _factory(config: GraphQLResourceConfig, /, *_args: Q.args, **kwargs: Q.kwargs):
        """
        Wrap the decorated function with the GraphQL factory.

        Args:
            config: The configuration for the GraphQL resource.
            *_args: The arguments for the decorated function.
            **kwargs: The keyword arguments for the decorated

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
            The GraphQL factory for the DLT asset.

            Args:
                context: The asset execution context.

            Returns:
                The DLT asset.
            """

            introspection = get_grapqhl_introspection(config)
            available_types = introspection["__schema"]["types"]

            if not available_types:
                raise ValueError(
                    "Malfomed introspection query, no types found.",
                )

            dictionary_types = {type["name"]: type for type in available_types}

            target_object = dictionary_types.get(config.target_type)

            if not target_object:
                raise ValueError(
                    f"Target query '{config.target_type}' not found in the introspection query.",
                )

            type_to_python = TypeToPython(available_types)

            all_types = [
                (
                    expand_field(field, dictionary_types, config.max_depth),
                    resolve_type(field["type"], type_to_python),
                )
                for field in target_object["fields"]
            ]

            query_parameters, query_variables = get_query_parameters(config.parameters)

            generated_query = f"""
                query {query_parameters} {{
                    {config.target_query} {query_variables} {{
                        {" ".join([field[0] for field in all_types])}
                    }}
                }}
            """

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

                client = Client(
                    transport=RequestsHTTPTransport(
                        url=config.endpoint,
                        use_json=True,
                        headers=config.headers,
                    ),
                )

                context.log.info(
                    f"GraphQL factory: fetching data from {config.endpoint}"
                )

                context.log.info(f"GraphQL factory: {generated_query}")

                # TODO(jabolo): use debounce mechanism
                result = client.execute(
                    gql(generated_query),
                    variable_values={
                        key: param["value"]
                        for key, param in (config.parameters or {}).items()
                    },
                )

                yield config.transform_fn(result) if config.transform_fn else result

            yield _execute_query

        return _dlt_graphql_asset

    return cast(Callable[Concatenate[GraphQLResourceConfig, Q], T], _factory)


graphql_factory = _graphql_factory(dlt_factory)
