from typing import (
    TypedDict,
    Dict,
    Any,
    cast,
    Sequence,
    Optional,
    List,
    Iterable,
    NotRequired,
    Callable,
)
from dagster import AssetKey
import dlt
from dlt.extract.resource import DltResource
from dlt.sources.credentials import ConnectionStringCredentials
from sqlalchemy import MetaData, Table
from dagster import AssetExecutionContext
from dagster_embedded_elt.dlt import (
    DagsterDltTranslator,
    dlt_assets,
    DagsterDltResource,
)

from ..dlt_sources.sql_database import sql_table, TableBackend


class SQLTableOptions(TypedDict):
    """Typed dict for the input to the sql_table function from the sql_database
    dlt verified source"""

    table: str
    schema: NotRequired[str]
    metadata: NotRequired[MetaData]
    incremental: NotRequired[dlt.sources.incremental[Any]]
    chunk_size: NotRequired[int]
    backend: NotRequired[TableBackend]
    detect_precision_hints: NotRequired[bool]
    defer_table_reflect: NotRequired[bool]
    table_adapter_callback: NotRequired[Callable[[Table], None]]
    backend_kwargs: NotRequired[Dict[str, Any]]


def sql_assets(
    source_name: str,
    source_credential_reference: str,
    sql_tables: List[SQLTableOptions],
):
    """A convenience sql asset factory that should handle any basic time series
    or simple sql source and configure a destination to the default oso
    data warehouse (bigquery at this time)
    """

    translator = PrefixedDltTranslator(source_name)
    pipeline = dlt.pipeline(
        pipeline_name=f"{source_name}_to_bigquery",
        destination="bigquery",
        dataset_name=source_name,
        progress="log",
    )

    credentials = ConnectionStringCredentials(
        connection_string=source_credential_reference
    )

    @dlt.source
    def _source():
        for table in sql_tables:
            yield sql_table(credentials, **table)

    @dlt_assets(
        name=source_name,
        dlt_source=_source(),
        dlt_pipeline=pipeline,
        dlt_dagster_translator=translator,
    )
    def _asset(context: AssetExecutionContext, dlt: DagsterDltResource):
        yield from dlt.run(context=context)

    return _asset


class PrefixedDltTranslator(DagsterDltTranslator):
    def __init__(self, source_name: str, prefix: Optional[Sequence[str]] = None):
        self._prefix = prefix or cast(Sequence[str], [])
        self._source_name = source_name

    def get_asset_key(self, resource: DltResource) -> AssetKey:
        key: List[str] = []
        key.extend(self._prefix)
        key.append(self._source_name)
        key.append(resource.name)
        return AssetKey(key)

    def get_deps_asset_keys(self, resource: DltResource) -> Iterable[AssetKey]:
        """We don't include the source here in the graph. It's not a necessary stub to represent"""
        key: List[str] = []
        key.extend(self._prefix)
        key.append("source")
        key.append(self._source_name)
        key.append(resource.name)
        return [AssetKey(key)]
