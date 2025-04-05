from dataclasses import dataclass
from typing import Any

from pydantic import Field
from sqlglot import exp, parse_one


def Column(sql_type: str, column_name: str | None = None) -> Any:
    try:
        parse_one(sql_type.replace("?", "VARCHAR"), into=exp.DataType, dialect="trino")
    except Exception as e:
        raise ValueError(f"Invalid SQL type: {sql_type}") from e
    json_schema_extra: dict[str, Any] = {"sql": sql_type}
    if column_name:
        json_schema_extra["column_name"] = column_name
    return Field(json_schema_extra=json_schema_extra)


@dataclass
class SeedConfig[T]:
    catalog: str
    schema: str
    table: str
    base: type[T]
    rows: list[T]
