from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from gql import Client, gql
from gql.transport.exceptions import TransportError
from gql.transport.requests import RequestsHTTPTransport
from graphql.error import GraphQLSyntaxError

FRAGMENT_MAX_DEPTH = 10

INTROSPECTION_DEPTH_BUFFER = 5

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
    """Create a fragment for introspection query that recurses to a given depth."""
    if depth <= 0 or depth > max_depth:
        return ""

    if depth == 1:
        return "kind name"

    return f"kind name ofType {{ {create_fragment(depth - 1)} }}"


def get_graphql_introspection(
    endpoint: str,
    headers_tuple: Optional[Tuple[Tuple[str, str], ...]],
    max_depth: int,
) -> Dict[str, Any]:
    """Fetch the GraphQL introspection query from the given endpoint."""
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

    introspection_depth = max_depth + INTROSPECTION_DEPTH_BUFFER
    populated_query = INTROSPECTION_QUERY.replace(
        "{{ DEPTH }}", create_fragment(introspection_depth)
    )

    try:
        return client.execute(gql(populated_query))
    except (TransportError, GraphQLSyntaxError) as exception:
        raise ValueError(
            f"Failed to fetch GraphQL introspection query from {endpoint}."
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
    """A mapping of GraphQL types to Python types."""

    def __init__(self, available_types: List[Dict[str, Any]]):
        self.available_types = available_types
        self._scalar_types = {
            attr: getattr(_TypeToPython, attr)
            for attr in dir(_TypeToPython)
            if not attr.startswith("_")
        }

    def __getitem__(self, name: str) -> str:
        """Get the Python type for the given GraphQL type."""
        if name in self._scalar_types:
            return self._scalar_types[name]

        is_object = next(
            (t for t in self.available_types if t["name"] == name),
            None,
        )

        return f'"{name}"' if is_object else "Any"


def get_type_info(graphql_type: Dict[str, Any]) -> Dict[str, Any]:
    """Extract core type information from a GraphQL type."""
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
            "is_abstract": inner_type.get("is_abstract", False),
        }

    if graphql_type["kind"] == "OBJECT":
        return {
            "kind": graphql_type["kind"],
            "name": graphql_type["name"],
            "is_scalar": False,
            "needs_expansion": True,
        }

    if graphql_type["kind"] in ("UNION", "INTERFACE"):
        return {
            "kind": graphql_type["kind"],
            "name": graphql_type["name"],
            "is_scalar": False,
            "needs_expansion": True,
            "is_abstract": True,
        }

    is_scalar = graphql_type["kind"] in ("SCALAR", "ENUM")
    return {
        "kind": graphql_type["kind"],
        "name": graphql_type["name"],
        "is_scalar": is_scalar,
        "needs_expansion": not is_scalar,
    }


def resolve_type(graphql_type: Dict[str, Any], type_mapper: TypeToPython) -> str:
    """Resolve the type of a GraphQL field to a Python type annotation."""
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
