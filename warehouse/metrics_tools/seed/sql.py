import json
from dataclasses import dataclass
from typing import Any, Literal

from pydantic import BaseModel
from sqlglot import exp, parse_one
from sqlmesh.core.dialect import transform_values


@dataclass
class SqlColumn:
    column: exp.Column
    type: exp.DataType
    nullable: bool

    def __str__(self) -> str:
        return f"{self.column.sql()} {self.type.sql()} {'NOT NULL' if not self.nullable else ''}".strip()


def get_types(field: dict[str, Any]) -> list[str]:
    if "anyOf" in field:
        any_of_types: list[dict[str, Any]] = field["anyOf"]
        return [t for any_of_type in any_of_types for t in get_types(any_of_type)]
    elif "items" in field:
        return get_types(field["items"])
    elif "type" in field:
        return [field["type"]]
    elif "$ref" in field:
        return [field["$ref"]]
    else:
        raise ValueError(f"Unknown field type: {field}")


def get_sql_column_type(schema: dict[str, Any], column_props: dict[str, Any]) -> str:
    sql_type: str | None = column_props.get("sql")
    if not sql_type:
        raise ValueError(f"SQL type not defined for column '{column_props}'")

    ref_index = sql_type.find("?")
    if ref_index == -1:
        return sql_type

    type_list = get_types(column_props)

    ref = next((t for t in type_list if t.startswith("#/$defs/")), None)
    if not ref:
        raise ValueError(
            f"No reference starting with '#/$defs/' found in types: {type_list}"
        )

    ref_props: dict[str, Any] = schema["$defs"][ref.split("/")[-1]]["properties"]
    nested_types = get_sql_column_types(schema, ref_props)

    return sql_type.replace(
        "?", ",\n ".join(list(str(x) for x in nested_types.values())), 1
    )


def get_sql_column_types(
    schema: dict[str, Any],
    properties: dict[str, Any],
) -> dict[str, SqlColumn]:
    columns: dict[str, SqlColumn] = {}
    for column_name, column_props in properties.items():
        sql_type = get_sql_column_type(schema, column_props)
        column_name = column_props.get("column_name", column_name)
        # If the column has anyOf property, we need to check if it is nullable
        nullable = any(
            option.get("type") == "null" for option in column_props.get("anyOf", [])
        )
        columns[column_name] = SqlColumn(
            column=exp.column(col=column_name, quoted=True),
            type=exp.maybe_parse(sql_type, into=exp.DataType, dialect="trino"),
            nullable=nullable,
        )
    return columns


def sql_create_table_from_pydantic_schema(
    name: str, schema: dict[str, Any], dialect: Literal["trino", "duckdb"]
) -> str:
    if not name:
        raise ValueError("Table name not defined in schema")

    properties: dict[str, Any] = schema["properties"]
    columns = get_sql_column_types(schema, properties)

    create_table_sql = parse_one(
        f"CREATE TABLE IF NOT EXISTS {name} (\n  {',\n  '.join(list(str(x) for x in columns.values()))}\n)",
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
    properties: dict[str, Any] = schema["properties"]
    columns = get_sql_column_types(schema, properties)
    columns_to_types = {column.column.name: column.type for column in columns.values()}

    expressions = [
        tuple(
            map_values_to_sql(
                instance,
                columns_to_types,
            )
        )
        for instance in instances
    ]
    values_exp = exp.values(expressions)

    insert_into_sql = exp.insert(
        into=exp.to_table(name),
        expression=values_exp,
        columns=[
            exp.to_identifier(column.column.name, quoted=True)
            for column in columns.values()
        ],
    ).sql(dialect=dialect)

    return insert_into_sql


def map_values_to_sql(instance: BaseModel, columns_to_types: dict[str, exp.DataType]):
    values = []
    for column, value in instance.model_dump().items():
        column_type = columns_to_types.get(column)
        if (
            not isinstance(value, str)
            and column_type
            and column_type.is_type(exp.DataType.Type.JSON)
        ):
            value = json.dumps(value)
        values.append(value)

    return transform_values(tuple(values), columns_to_types)
