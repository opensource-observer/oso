import typing as t

import dlt
import structlog
from dagster import AssetExecutionContext, AssetKey, AssetSpec
from dagster_dlt.translator import DltResourceTranslatorData
from dagster_embedded_elt.dlt import (
    DagsterDltResource,
    DagsterDltTranslator,
    dlt_assets,
)
from dlt.common.schema.typing import TWriteDispositionConfig
from dlt.destinations import bigquery
from dlt.extract.resource import DltResource
from dlt.pipeline.pipeline import Pipeline
from dlt.sources.credentials import (
    ConnectionStringCredentials,
    GcpServiceAccountCredentials,
)
from oso_dagster.config import DagsterConfig
from oso_dagster.dlt_sources.sql_database.helpers import engine_from_credentials
from sqlalchemy import Engine, MetaData, Table
from sqlalchemy.exc import NoSuchTableError

from ..dlt_sources.sql_database import TableBackend, sql_table
from ..utils.secrets import SecretReference, SecretResolver
from .common import AssetFactoryResponse, AssetList, early_resources_asset_factory

logger = structlog.get_logger(__name__)


class SQLTableOptions(t.TypedDict):
    """Typed dict for the input to the sql_table function from the sql_database
    dlt verified source"""

    table: str
    schema: t.NotRequired[str]
    metadata: t.NotRequired[MetaData]
    incremental: t.NotRequired[dlt.sources.incremental[t.Any]]
    chunk_size: t.NotRequired[int]
    backend: t.NotRequired[TableBackend]
    detect_precision_hints: t.NotRequired[bool]
    defer_table_reflect: t.NotRequired[bool]
    table_adapter_callback: t.NotRequired[t.Callable[[Table], None]]
    backend_kwargs: t.NotRequired[t.Dict[str, t.Any]]


class TopLevelSQLTableOptions(SQLTableOptions):
    destination_table_name: t.NotRequired[str]
    write_disposition: t.NotRequired[TWriteDispositionConfig]


def _generate_asset_for_table(
    source_name: str,
    credentials: ConnectionStringCredentials | Engine | str,
    pipeline: Pipeline,
    table_options: TopLevelSQLTableOptions,
    translator: DagsterDltTranslator,
    pool_size: t.Optional[int] = None,
):
    all_table_options = table_options.copy()

    @dlt.source(name=f"{source_name}_{table_options['table']}")
    def _source():
        destination_table_name = table_options.get("destination_table_name")
        write_disposition = table_options.get("write_disposition")
        if destination_table_name:
            del table_options["destination_table_name"]
        if write_disposition:
            del table_options["write_disposition"]
        table = t.cast(SQLTableOptions, table_options)
        resource = sql_table(credentials, **table)
        if destination_table_name:
            resource.table_name = destination_table_name
        return resource

    @dlt_assets(
        name=f"{source_name}_{table_options['table']}",
        dlt_source=_source(),
        dlt_pipeline=pipeline,
        dagster_dlt_translator=translator,
    )
    def _asset(context: AssetExecutionContext, dlt: DagsterDltResource):
        kwargs = {}
        write_disposition = all_table_options.get("write_disposition")
        if write_disposition:
            kwargs["write_disposition"] = write_disposition

        yield from dlt.run(context=context, loader_file_format="jsonl", **kwargs)

    return _asset


def sql_assets(
    source_name: str,
    source_credential_reference: SecretReference,
    sql_tables: t.List[TopLevelSQLTableOptions],
    group_name: str = "",
    environment: str = "production",
    asset_type: str = "source",
    pool_size: t.Optional[int] = None,
    concurrency_key: t.Optional[str] = None,
):
    """A convenience sql asset factory that should handle any basic incremental
    table or or full refresh sql source and configure a destination to the
    default oso data warehouse (bigquery at this time)
    """

    @early_resources_asset_factory(caller_depth=2)
    def factory(
        secrets: SecretResolver,
        global_config: DagsterConfig,
        dlt_staging_destination: dlt.destinations.filesystem,
    ):
        tags = {
            "opensource.observer/environment": environment,
            "opensource.observer/factory": "sql_dlt",
            "opensource.observer/type": asset_type,
            "opensource.observer/source": "unstable",
        }
        if concurrency_key is not None:
            tags["dagster/concurrency_key"] = concurrency_key
        translator = PrefixedDltTranslator(source_name, tags)

        connection_string = secrets.resolve_as_str(source_credential_reference)
        credentials: ConnectionStringCredentials | Engine | str = (
            ConnectionStringCredentials(connection_string)
        )
        if pool_size:
            credentials = engine_from_credentials(credentials, pool_size=pool_size)

        assets: AssetList = []

        for table in sql_tables:
            pipeline_name = f"{source_name}_{table['table']}_to_bigquery"
            if group_name != "":
                pipeline_name = (
                    f"{source_name}_{group_name}_{table['table']}_to_bigquery"
                )
                if table.get("destination_table_name") is None:
                    table["destination_table_name"] = f"{group_name}__{table['table']}"

            # This prevents loading the table eagerly at dagster startup. This
            # significantly speeds up the loading of the dagster UI and prevents
            # unnecessary table reflection.
            if not global_config.eagerly_load_sql_tables:
                logger.info(
                    f"Deferring table reflection for {table['table']}",
                    source_name=source_name,
                    table=table["table"],
                )
                if table.get("defer_table_reflect") is None:
                    table["defer_table_reflect"] = True

            pipeline = dlt.pipeline(
                pipeline_name=pipeline_name,
                destination=bigquery(
                    credentials=GcpServiceAccountCredentials(
                        project_id=global_config.project_id
                    )
                ),
                dataset_name=source_name,
                staging=dlt_staging_destination,
                progress="log",
            )
            try:
                asset_def = _generate_asset_for_table(
                    source_name, credentials, pipeline, table, translator
                )
                assets.append(asset_def)
            except NoSuchTableError:
                logger.error(
                    f'Failed to load table "{table["table"]}" for source "{source_name}"'
                )

        return AssetFactoryResponse(assets=assets)

    return factory


class PrefixedDltTranslator(DagsterDltTranslator):
    """Prefixes DLT asset names with the specified prefix"""

    def __init__(
        self,
        source_name: str,
        tags: t.Dict[str, str],
        prefix: t.Optional[t.Sequence[str]] = None,
        include_deps: bool = False,
    ):
        self._prefix = prefix or t.cast(t.Sequence[str], [])
        self._source_name = source_name
        self._include_deps = include_deps
        self._tags = tags.copy()

    def get_asset_spec(self, data: DltResourceTranslatorData):
        return AssetSpec(
            key=self.get_asset_key_from_resource(data.resource),
            tags=self._tags,
            deps=self.get_deps_asset_keys_from_resource(data.resource),
        )

    def get_asset_key_from_resource(self, resource: DltResource) -> AssetKey:
        key: t.List[str] = []
        key.extend(self._prefix)
        key.append(self._source_name)
        key.append(resource.name)
        return AssetKey(key)

    def get_deps_asset_keys_from_resource(
        self, resource: DltResource
    ) -> t.Iterable[AssetKey]:
        """We don't include the source here in the graph. It's not a necessary stub to represent"""
        if not self._include_deps:
            return []
        key: t.List[str] = []
        key.extend(self._prefix)
        key.append(self._source_name)
        key.append("sources")
        key.append(resource.name)
        return [AssetKey(key)]
