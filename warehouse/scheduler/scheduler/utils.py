import uuid
from typing import Literal

import structlog
from aiotrino.exceptions import TrinoQueryError
from dlt.common.schema import TTableSchemaColumns
from queryrewriter.types import TableResolver
from scheduler.graphql_client.client import Client as OSOClient
from scheduler.types import DataModelColumnInput
from sqlglot import exp

logger = structlog.getLogger(__name__)


def convert_uuid_bytes_to_str(uuid_bytes: bytes) -> str:
    """Convert UUID bytes to a string representation."""

    return str(uuid.UUID(bytes=uuid_bytes))


def get_trino_user(user_type: Literal["rw", "ro"], org_id: str, org_name: str) -> str:
    return f"{user_type}-{org_name.strip().lower()}-{org_id.replace('-', '').lower()}"


def ctas_query(query: exp.Query):
    """Return a dummy query to do a CTAS (CREATE TABLE AS SELECT).

    If a model's column types are unknown, the only way to create the table is to
    run the fully expanded query. This can be expensive so we add a WHERE FALSE to all
    SELECTS and hopefully the optimizer is smart enough to not do anything.

    Args:
        render_kwarg: Additional kwargs to pass to the renderer.
    Return:
        The mocked out ctas query.
    """
    query = query.limit(0)

    for select_or_set_op in query.find_all(exp.Select, exp.SetOperation):
        if isinstance(select_or_set_op, exp.Select) and select_or_set_op.args.get(
            "from"
        ):
            select_or_set_op.where(exp.false(), copy=False)

    return query


def table_to_fqn(table: exp.Table) -> str:
    """Convert a sqlglot Table expression to a fully qualified name string.

    Args:
        table: The sqlglot Table expression.

    Returns:
        The fully qualified name string.
    """
    if table.catalog and table.db:
        return f"{table.catalog}.{table.db}.{table.name}"
    if table.db:
        return f"{table.db}.{table.name}"
    return table.name


class OSOClientTableResolver(TableResolver):
    """A table resolver that uses the OSO client to resolve table references."""

    def __init__(self, oso_client: OSOClient):
        self._oso_client = oso_client

    async def resolve_tables(
        self, tables: dict[str, exp.Table], *, metadata: dict | None = None
    ):
        # We send the values of the table to be further resolved by the OSO client
        table_values_map = {table_to_fqn(value): key for key, value in tables.items()}

        if len(table_values_map) == 0:
            logger.debug("No tables to resolve.")
            return tables

        logger.debug(f"Resolving tables: {list(table_values_map.keys())}")

        resolved_tables = await self._oso_client.resolve_tables(
            references=list(table_values_map.keys()), metadata=metadata or {}
        )

        result: dict[str, exp.Table] = {}

        for resolved in resolved_tables.system.resolve_tables:
            key = table_values_map[resolved.reference]
            result[key] = exp.to_table(resolved.fqn)

        return result


def dlt_to_oso_schema(
    columns: TTableSchemaColumns | None,
) -> list[DataModelColumnInput]:
    """Convert DLT schema to OSO schema.

    Args:
        columns: The DLT columns.

    Returns:
        The OSO schema.
    """
    if not columns:
        return []
    oso_columns: list[DataModelColumnInput] = []
    for col in columns.values():
        name = col.get("name")
        data_type = col.get("data_type")
        if not name:
            logger.warning(
                "Column missing name",
                extra={"column": col},
            )
            continue
        oso_columns.append(DataModelColumnInput(name=name, type=data_type or "null"))
    return oso_columns


def aiotrino_query_error_to_json(error: TrinoQueryError):
    """Convert an aiotrino TrinoQueryError to a JSON-serializable dict.

    Args:
        error: The TrinoQueryError instance.

    Returns:
        A dictionary representation of the error.
    """

    return {
        "message": error.message,
        "error_code": error.error_code,
        "error_name": error.error_name,
        "error_type": error.error_type,
        "failure_info": error.failure_info,
        "query_id": error.query_id,
    }
