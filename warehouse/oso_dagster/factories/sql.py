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
from dlt.pipeline.pipeline import Pipeline
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
from .common import early_resources_asset_factory, AssetFactoryResponse, AssetList
from ..utils.secrets import SecretReference, SecretResolver


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


class TopLevelSQLTableOptions(SQLTableOptions):
    destination_table_name: NotRequired[str]


def _generate_asset_for_table(
    source_name: str,
    credentials: ConnectionStringCredentials,
    pipeline: Pipeline,
    table_options: TopLevelSQLTableOptions,
    translator: DagsterDltTranslator,
):
    @dlt.source(name=f"{source_name}_{table_options["table"]}")
    def _source():
        destination_table_name = table_options.get("destination_table_name")
        if destination_table_name:
            del table_options["destination_table_name"]
        table = cast(SQLTableOptions, table_options)
        resource = sql_table(credentials, **table)
        if destination_table_name:
            resource.table_name = destination_table_name
        return resource

    @dlt_assets(
        name=f"{source_name}_{table_options["table"]}",
        dlt_source=_source(),
        dlt_pipeline=pipeline,
        dlt_dagster_translator=translator,
    )
    def _asset(context: AssetExecutionContext, dlt: DagsterDltResource):
        yield from dlt.run(context=context, loader_file_format="jsonl")

    return _asset


def sql_assets(
    source_name: str,
    source_credential_reference: SecretReference,
    sql_tables: List[TopLevelSQLTableOptions],
    group_name: str = "",
    environment: str = "production",
    asset_type: str = "source"
):
    """A convenience sql asset factory that should handle any basic incremental
    table or or full refresh sql source and configure a destination to the
    default oso data warehouse (bigquery at this time)
    """

    @early_resources_asset_factory(caller_depth=2)
    def factory(
        secrets: SecretResolver,
        project_id: str,
        dlt_gcs_staging: dlt.destinations.filesystem,
    ):
        
        tags = {
            "opensource.observer/environment": environment,
            "opensource.observer/factory": "sql_dlt",
            "opensource.observer/type": asset_type,
        }
        translator = PrefixedDltTranslator(source_name, tags) 

        connection_string = secrets.resolve_as_str(source_credential_reference)
        credentials = ConnectionStringCredentials(connection_string)

        assets: AssetList = []

        for table in sql_tables:
            pipeline_name = f"{source_name}_{table["table"]}_to_bigquery"
            if group_name != "":
                pipeline_name = f"{source_name}_{group_name}_{table["table"]}_to_bigquery"
                if table.get("destination_table_name") is None:
                    table['destination_table_name'] = f"{group_name}__{table["table"]}"

            pipeline = dlt.pipeline(
                pipeline_name=pipeline_name,
                destination="bigquery",
                credentials={
                    "project_id": project_id,
                },
                dataset_name=source_name,
                staging=dlt_gcs_staging,
                progress="log",
            )
            asset_def = _generate_asset_for_table(
                source_name, credentials, pipeline, table, translator
            )
            assets.append(
                asset_def
            )

        return AssetFactoryResponse(assets=assets)

    return factory


class PrefixedDltTranslator(DagsterDltTranslator):
    """Prefixes DLT asset names with the specified prefix"""

    def __init__(
        self,
        source_name: str,
        tags: Dict[str, str],
        prefix: Optional[Sequence[str]] = None,
        include_deps: bool = False,
    ):
        self._prefix = prefix or cast(Sequence[str], [])
        self._source_name = source_name
        self._include_deps = include_deps
        self._tags = tags.copy()

    def get_asset_key(self, resource: DltResource) -> AssetKey:
        key: List[str] = []
        key.extend(self._prefix)
        key.append(self._source_name)
        key.append(resource.name)
        return AssetKey(key)

    def get_deps_asset_keys(self, resource: DltResource) -> Iterable[AssetKey]:
        """We don't include the source here in the graph. It's not a necessary stub to represent"""
        if not self._include_deps:
            return []
        key: List[str] = []
        key.extend(self._prefix)
        key.append(self._source_name)
        key.append("sources")
        key.append(resource.name)
        return [AssetKey(key)]
    
    def get_tags(self, resource: DltResource):
        # As of 2024-07-10 This doesn't work. We will make a PR upstream
        return self._tags
