from typing import Any, Literal

from pydantic import BaseModel
from sqlglot import exp, parse_one
from sqlmesh.core.dialect import transform_values


def sql_create_table_from_pydantic_schema(
    name: str, schema: dict[str, Any], dialect: Literal["trino", "duckdb"]
) -> str:
    properties: dict[str, Any] = schema["properties"]
    if not name:
        raise ValueError("Table name not defined in schema")
    columns = []
    for column_name, column_props in properties.items():
        sql_type = column_props.get("sql")
        if not sql_type:
            raise ValueError(f"SQL type not defined for column '{column_name}'")
        # If the column has anyOf property, we need to check if it is nullable
        nullable = (
            "NOT NULL"
            if not any(
                option.get("type") == "null" for option in column_props.get("anyOf", [])
            )
            else ""
        )
        columns.append(f"{column_name} {sql_type} {nullable}".strip())

    create_table_sql = parse_one(
        f"CREATE TABLE IF NOT EXISTS {name} (\n  {',\n  '.join(columns)}\n)",
        dialect="trino",
    ).sql(dialect=dialect)

    return create_table_sql


def sql_insert_from_pydantic_instances(
    name: str,
    instances: list[BaseModel],
    dialect: Literal["trino", "duckdb"],
) -> str:
    if not name:
        raise ValueError("Table name not defined in schema")
    if not instances:
        return ""

    schema = instances[0].model_json_schema()
    columns_to_types: dict[str, exp.DataType] = {}
    for column_name, column_props in schema["properties"].items():
        sql_type = column_props.get("sql")
        if not sql_type:
            raise ValueError(f"SQL type not defined for column '{column_name}'")
        # If the column has anyOf property, we need to check if it is nullable

        columns_to_types[column_name] = exp.maybe_parse(
            sql_type, into=exp.DataType, dialect=dialect
        )
        columns_to_types[column_name]

    casted_columns = [
        exp.alias_(exp.cast(exp.column(column), to=kind), column, copy=False)
        for column, kind in columns_to_types.items()
    ]
    expressions = [
        tuple(transform_values(tuple(instance.model_dump().values()), columns_to_types))
        for instance in instances
    ]
    values_exp = exp.values(expressions, alias="t", columns=columns_to_types)

    insert_into_sql = exp.insert(
        into=exp.to_table(name),
        expression=exp.select(*casted_columns)
        .from_(values_exp, copy=False)
        .where(exp.false() if not instances else None, copy=False),
    ).sql(dialect=dialect)

    return insert_into_sql
