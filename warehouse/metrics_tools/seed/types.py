from typing import Any

from pydantic import Field
from sqlglot import exp, parse_one


def Column(sql_type: str, column_name: str | None = None) -> Any:
    try:
        parse_one(sql_type.replace("?", "VARCHAR"), into=exp.DataType, dialect="trino")
    except Exception as e:
        raise ValueError(f"Invalid SQL type: {sql_type}") from e

    return Field(json_schema_extra={"sql": sql_type, "column_name": column_name})
