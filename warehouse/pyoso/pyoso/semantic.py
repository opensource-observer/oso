from dataclasses import dataclass, field
from typing import Callable

import pandas as pd
import requests
from pyoso.exceptions import OsoHTTPError


@dataclass
class SemanticColumn:
    name: str
    type: str
    description: str


@dataclass
class SemanticRelationship:
    source_column: str
    target_table: str
    target_column: str


@dataclass
class SemanticTableResponse:
    name: str
    description: str
    columns: list[SemanticColumn] = field(default_factory=list)
    relationships: list[SemanticRelationship] = field(default_factory=list)


def map_to_semantic_table_response(table_data: dict) -> SemanticTableResponse:
    assert (
        "name" in table_data and table_data.get("name") is not None
    ), "Table name is required"
    columns = []
    if "columns" in table_data:
        for col_data in table_data["columns"]:
            assert (
                "name" in col_data and col_data.get("name") is not None
            ), "Column name is required"
            column = SemanticColumn(
                name=col_data.get("name"),
                type=col_data.get("type") or "",
                description=col_data.get("description") or "",
            )
            columns.append(column)

    # Extract relationships
    relationships = []
    if "relationships" in table_data:
        for rel_data in table_data["relationships"]:
            assert (
                "sourceColumn" in rel_data
                and "targetTable" in rel_data
                and "targetColumn" in rel_data
                and rel_data.get("sourceColumn") is not None
                and rel_data.get("targetTable") is not None
                and rel_data.get("targetColumn") is not None
            ), "Source column, target table and target column are required in relationship data"

            relationship = SemanticRelationship(
                source_column=rel_data.get("sourceColumn"),
                target_table=rel_data.get("targetTable"),
                target_column=rel_data.get("targetColumn"),
            )

            relationships.append(relationship)

    return SemanticTableResponse(
        name=table_data.get("name") or "",
        description=table_data.get("description") or "",
        columns=columns,
        relationships=relationships,
    )


def query_dynamic_models(base_url: str, api_key: str) -> list[SemanticTableResponse]:
    headers = {
        "Content-Type": "application/json",
    }
    headers["Authorization"] = f"Bearer {api_key}"
    try:
        response = requests.get(
            f"{base_url}connector",
            headers=headers,
        )
        response.raise_for_status()

        # Parse the JSON response
        response_data = response.json()

        # Map the response to SemanticTableResponse objects
        tables = []
        for table_data in response_data:
            table = map_to_semantic_table_response(table_data)
            tables.append(table)

        return tables
    except requests.HTTPError as e:
        raise OsoHTTPError(e, response=e.response) from None


def create_registry(
    base_url: str, api_key: str, to_pandas_fn: Callable[[str], pd.DataFrame]
):
    from oso_semantic import Dimension, Model
    from oso_semantic import QueryBuilder as InnerQueryBuilder
    from oso_semantic import (
        Registry,
        Relationship,
        RelationshipType,
        register_oso_models,
    )

    class QueryBuilder(InnerQueryBuilder):

        def __init__(self, registry: Registry):
            super().__init__(registry)

        def to_pandas(self):
            sql = self.build()
            return to_pandas_fn(sql.sql(dialect="trino"))

    registry = Registry(QueryBuilder)

    register_oso_models(registry)

    tables = query_dynamic_models(base_url, api_key)
    for table in tables:
        model_name = table.name.split(".")[-1]
        registry.register(
            Model(
                name=model_name,
                description=table.description,
                table=table.name,
                dimensions=[
                    Dimension(
                        name=column.name,
                        column_name=column.name,
                        description=column.description,
                    )
                    for column in table.columns
                ],
                relationships=[
                    Relationship(
                        name=f"{relationship.source_column}->{relationship.target_table.split('.')[-1]}.{relationship.target_column}",
                        type=RelationshipType.MANY_TO_ONE,
                        source_foreign_key=relationship.source_column,
                        ref_model=relationship.target_table.split(".")[-1],
                        ref_key=relationship.target_column,
                    )
                    for relationship in table.relationships
                ],
            )
        )

    return registry
