from typing import Any, Callable, Dict, Optional
from dataclasses import dataclass

import dlt
from gql import Client, gql
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
        endpoint: The endpoint of the GraphQL resource.
        max_depth: The maximum depth of the GraphQL query.
        target_query: The target query to execute.
        headers: The headers to include in the introspection query.
    """

    endpoint: str
    max_depth: int = 5
    target_query: Optional[str] = None
    headers: Optional[Dict[str, str]] = None


def get_grapqhl_introspection(config: GraphQLResourceConfig) -> Dict[str, Any]:
    """
    Fetch the GraphQL introspection query from the given endpoint.

    Args:
        config: The configuration for the GraphQL resource.
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
        "{{ DEPTH }}", create_fragment(config.max_depth)
    )

    try:
        return client.execute(gql(populated_query))
    except Exception as exception:
        raise ValueError(
            "Failed to fetch GraphQL introspection query.",
        ) from exception


def _graphql_resource[
    T, **P
](resource: Callable[P, T]) -> Callable[[GraphQLResourceConfig], Callable[P, T]]:
    """
    This factory is a wrapper of the `dlt.resource` decorator.

    Args:
        resource: The function to decorate.
    """

    def _factory(config: GraphQLResourceConfig) -> Callable[P, T]:
        def _decorator(*args: P.args, **kwargs: P.kwargs) -> T:
            if not config.target_query:
                raise ValueError(
                    "Target query not specified in the GraphQL resource config."
                )

            _introspection = get_grapqhl_introspection(config)

            # TODO: Build pydantic model from introspection.
            #   - Use the introspection to build a schema of the
            #     root query type, since nested types are `JSON` by
            #     default.

            # TODO: Build query from introspection.
            #   - Use the introspection to build a query for the
            #     target query, using the root query type.

            # TODO: Execute the query.
            #   - Execute the query using the introspection and
            #     the target query.

            # TODO: Handle pagination.

            # TODO: Yield the results.

            return resource(*args, **kwargs)

        return _decorator

    return _factory


graphql_resource = _graphql_resource(dlt.resource)
"""
This is the GraphQL resource factory that wraps the `dlt.resource` decorator.

Example:
    ```python
    @dlt_factory(
        key_prefix="open_collective",
        op_tags={
            "dagster-k8s/config": K8S_CONFIG,
        },
    )
    def expenses(
        personal_token: str = secret_ref_arg(
            group_name="open_collective", key="personal_token"
        ),
    ):
        open_collective_resource = graphql_resource(
            GraphQLResourceConfig(
                endpoint="https://api.opencollective.com/graphql/v2",
                max_depth=5,
                target_query="Transactions",
                headers={
                    "Personal-Token": personal_token,
                },
            ),
        )

        yield open_collective_resource(
            name="expenses",
            primary_key="id",
            write_disposition="merge",
        )
    ```
"""
