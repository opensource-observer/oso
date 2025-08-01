"""
Auxiliary resources for sqlmesh
"""

import abc
import json
import math
import typing as t
from itertools import batched

import structlog
from dagster import (
    AssetExecutionContext,
    AssetKey,
    AssetOut,
    AssetsDefinition,
    MaterializeResult,
    multi_asset,
)
from dagster_sqlmesh import SQLMeshDagsterTranslator
from dagster_sqlmesh.controller.base import SQLMeshInstance
from metrics_service.types import TableMetadata, TableReference
from metrics_tools.transfer.coordinator import Destination, Source, transfer
from openai import BaseModel
from oso_dagster.resources.bq import BigQueryImporterResource
from oso_dagster.resources.clickhouse import ClickhouseImporterResource
from oso_dagster.resources.duckdb import DuckDBExporterResource, DuckDBImporterResource
from oso_dagster.resources.trino import TrinoExporterResource
from pydantic import Field
from sqlglot import exp
from sqlmesh import Context
from sqlmesh.core.dialect import parse_one
from sqlmesh.core.model import Model

logger = structlog.get_logger(__name__)

BIGQUERY_BATCH_SIZE = 10000


class PrefixedSQLMeshTranslator(SQLMeshDagsterTranslator):
    def __init__(self, prefix: str, default_catalog: str):
        self._prefix = prefix
        self._default_catalog = default_catalog

    def get_asset_key(self, context: Context, fqn: str) -> AssetKey:
        table = exp.to_table(fqn)  # Ensure fqn is a valid table expression
        if table.catalog in ["bigquery", self._default_catalog]:
            # For BigQuery and Iceberg, we use the db and table name
            if table.db == "oso":
                path = [self._prefix, table.name]
            else:
                path = [table.db, table.name]
        else:
            # For other catalogs, we use catalog, db, and table name (these are likely external things)
            path = [table.catalog, table.db, table.name]

        return AssetKey(path)

    def get_group_name(self, context, model):
        return "sqlmesh"

    def get_tags(self, context: Context, model: Model) -> t.Dict[str, str]:
        """Loads tags for a model.

        Does a basic translation. If the tag is a string with no `:` it will be
        considered a boolean tag with the value "true".

        If the tag is a string with a `:` it will be split on the `:` and the
        key will be the left side the value will be the right side.

        Skipped tags: index, order_by
        """
        tags: t.Dict[str, str] = self.get_unfiltered_tags(context, model)
        for blocked_tag in ["index", "order_by"]:
            if blocked_tag in tags:
                del tags[blocked_tag]
        return tags

    def get_unfiltered_tags(self, context: Context, model: Model) -> t.Dict[str, str]:
        """Loads unfiltered tags for a model.

        This is similar to get_tags but does not filter out the index and order_by tags.
        """
        tags: t.Dict[str, str] = {}
        for tag in model.tags:
            if "=" in tag:
                key, value = tag.split("=")
                tags[key] = value
            else:
                tags[tag] = "true"
        return tags


class SQLMeshExportedAssetDefinition(BaseModel):
    outs: t.Dict[str, str]
    internal_asset_deps: t.Mapping[str, t.Set[str]]
    deps: t.List[str]
    extras: t.Dict[str, t.Any] = Field(default_factory=dict)

    @classmethod
    def from_dagster_objs(
        cls,
        outs: t.Dict[str, AssetKey],
        internal_asset_deps: t.Mapping[str, t.Set[AssetKey]],
        deps: t.List[AssetKey],
        extras: t.Dict[str, t.Any] | None = None,
    ):
        processed_outs = {name: out.to_user_string() for name, out in outs.items()}
        processed_internal_asset_deps = {
            name: {dep.to_user_string() for dep in deps_set}
            for name, deps_set in internal_asset_deps.items()
        }
        processed_deps = [dep.to_user_string() for dep in deps]
        return cls(
            outs=processed_outs,
            internal_asset_deps=processed_internal_asset_deps,
            deps=processed_deps,
            extras=extras or {},
        )

    def outs_as_dagster_obj(self) -> t.Dict[str, AssetOut]:
        """Converts the outs to AssetOuts."""
        return {
            name: AssetOut(key=AssetKey.from_user_string(self.outs[name]))
            for name in self.outs
        }

    def internal_asset_deps_as_dagster_obj(self) -> t.Mapping[str, t.Set[AssetKey]]:
        """Converts the internal asset deps to AssetDeps."""
        return {
            name: {AssetKey.from_user_string(dep) for dep in deps_set}
            for name, deps_set in self.internal_asset_deps.items()
        }

    def deps_as_dagster_obj(self) -> t.List[AssetKey]:
        """Converts the deps to AssetKeys."""
        return [AssetKey.from_user_string(dep) for dep in self.deps]


class SQLMeshExporter(abc.ABC):
    @abc.abstractmethod
    def name(self) -> str:
        """Returns the name of the exporter."""
        raise NotImplementedError("Not implemented")

    @abc.abstractmethod
    def create_export_asset(
        self,
        mesh: SQLMeshInstance,
        translator: PrefixedSQLMeshTranslator,
        to_export: t.List[t.Tuple[Model, AssetKey]],
    ) -> SQLMeshExportedAssetDefinition:
        """This creates an export asset that can be cached"""
        raise NotImplementedError("Not implemented")

    def asset_from_definition(
        self,
        definition: SQLMeshExportedAssetDefinition,
    ) -> AssetsDefinition:
        """Converts the exported asset definition to a Dagster AssetsDefinition."""
        outs = definition.outs_as_dagster_obj()
        internal_asset_deps = definition.internal_asset_deps_as_dagster_obj()
        deps = definition.deps_as_dagster_obj()

        return multi_asset(
            outs=outs,
            internal_asset_deps=internal_asset_deps,
            deps=deps,
            **self.asset_options(definition),
        )(self.asset_function(definition))

    def asset_options(
        self, definition: SQLMeshExportedAssetDefinition
    ) -> t.Dict[str, t.Any]:
        """Returns the options for the asset."""
        return dict(
            compute_kind="sqlmesh-export",
            can_subset=True,
        )

    @abc.abstractmethod
    def asset_function(self, definition: SQLMeshExportedAssetDefinition) -> t.Callable:
        raise NotImplementedError("Not implemented")


class Trino2ClickhouseSQLMeshExporter(SQLMeshExporter):
    def __init__(
        self,
        prefix: str | t.List[str],
        *,
        destination_catalog: str,
        destination_schema: str,
        source_catalog: str,
        source_schema: str,
    ):
        self._prefix = prefix

        self._destination_catalog = destination_catalog
        self._destination_schema = destination_schema

        self._source_catalog = source_catalog
        self._source_schema = source_schema

    def name(self) -> str:
        return "trino2clickhouse"

    def trino_destination_table(self, table_name: str):
        return f"{self._destination_catalog}.{self._destination_schema}.{table_name}"

    def clickhouse_destination_table(self, table_name: str):
        return f"{self._destination_schema}.{table_name}"

    def trino_source_table(self, table_name: str):
        return f"{self._source_catalog}.{self._source_schema}.{table_name}"

    def convert_model_key_to_clickhouse_out(self, key: AssetKey) -> AssetKey:
        return AssetKey(
            path=[*self._prefix, key.path[-1]],
        )

    def create_export_asset(
        self,
        mesh: SQLMeshInstance,
        translator: PrefixedSQLMeshTranslator,
        to_export: t.List[t.Tuple[Model, AssetKey]],
    ) -> SQLMeshExportedAssetDefinition:
        clickhouse_outs = {
            key.path[-1]: self.convert_model_key_to_clickhouse_out(key)
            for _, key in to_export
        }
        internal_asset_deps: t.Mapping[str, t.Set[AssetKey]] = {
            key.path[-1]: {key} for _, key in to_export
        }
        deps = [key for _, key in to_export]
        table_metadata: dict[str, dict] = {}

        for model, asset_key in to_export:
            tags = translator.get_unfiltered_tags(mesh.context, model)
            index = "index" in tags and json.loads(tags["index"]) or None
            order_by = "order_by" in tags and json.loads(tags["order_by"]) or None
            table_metadata[asset_key.path[-1]] = TableMetadata(
                index=index,
                order_by=order_by,
            ).model_dump()
        extras = dict(table_metadata=table_metadata)

        return SQLMeshExportedAssetDefinition.from_dagster_objs(
            outs=clickhouse_outs,
            internal_asset_deps=internal_asset_deps,
            deps=deps,
            extras=extras,
        )

    def asset_function(self, definition: SQLMeshExportedAssetDefinition):
        table_metadata = {
            name: TableMetadata.model_validate(raw_metadata)
            for name, raw_metadata in definition.extras.get(
                "table_metadata", {}
            ).items()
        }

        async def trino_clickhouse_export(
            context: AssetExecutionContext,
            trino_exporter: TrinoExporterResource,
            clickhouse_importer: ClickhouseImporterResource,
        ):
            async with trino_exporter.get_exporter(
                "trino-export", log_override=context.log
            ) as exporter:
                logger.debug(f"exporting to {self._destination_catalog}")
                with clickhouse_importer.get() as importer:
                    selected_output_names = (
                        context.op_execution_context.selected_output_names
                    )
                    for table_name in selected_output_names:
                        metadata = table_metadata.get(table_name, TableMetadata())
                        logger.info(
                            f"Exporting table {table_name} with metadata: {metadata}"
                        )
                        await transfer(
                            Source(
                                exporter=exporter,
                                table=TableReference(
                                    catalog_name=self._source_catalog,
                                    schema_name=self._source_schema,
                                    table_name=table_name,
                                ),
                            ),
                            Destination(
                                importer=importer,
                                table=TableReference(
                                    schema_name=self._destination_schema,
                                    table_name=table_name,
                                    metadata=metadata,
                                ),
                            ),
                            log_override=context.log,
                        )
                        yield MaterializeResult(
                            asset_key=AssetKey(table_name).with_prefix(self._prefix)
                        )

        return trino_clickhouse_export

    def generate_create_table_query(
        self, model: Model, source_table: str, destination_table: str
    ):
        base_create_query = f"""
            CREATE table {destination_table} (
                placeholder VARCHAR,
            )
        """

        columns = model.columns_to_types
        assert columns is not None, "columns must not be None"

        create_query = parse_one(base_create_query, dialect="trino")
        create_query.this.set(
            "expressions",
            [
                exp.ColumnDef(this=exp.to_identifier(column_name), kind=column_type)
                for column_name, column_type in columns.items()
            ],
        )

        properties = [
            # DO NOT USE exp.EngineProperty. This doesn't currently work
            # properly for sqlglot in this context. Also don't parse a create
            # query that has the WITH (engine = 'something') portion in it. It
            # will parse as an exp.EngineProperty and cause problems when
            # rerendering to sql
            exp.Property(
                this=exp.Var(this="engine"),
                value=exp.Literal(this="MergeTree", is_string=True),
            ),
        ]
        if model.time_column:
            properties.append(
                exp.Property(
                    this=exp.Var(this="order_by"),
                    value=exp.Literal(
                        this=model.time_column.column.sql(dialect="trino"),
                        is_string=True,
                    ),
                )
            )
        create_query.set(
            "properties",
            exp.Properties(
                expressions=properties,
            ),
        )
        return create_query

    def generate_insert_query(
        self, model: Model, source_table: str, destination_table: str
    ) -> exp.Expression:
        assert model.columns_to_types is not None, "columns must not be None"
        select = exp.select(
            *[column_name for column_name in model.columns_to_types.keys()]
        ).from_(source_table)
        insert = exp.Insert(this=exp.to_table(destination_table), expression=select)

        return insert


class Trino2BigQuerySQLMeshExporter(SQLMeshExporter):
    def __init__(
        self,
        prefix: str | t.List[str],
        *,
        project_id: str,
        dataset_id: str,
        source_catalog: str,
        source_schema: str,
    ):
        self._prefix = prefix
        self._project_id = project_id
        self._dataset_id = dataset_id
        self._source_catalog = source_catalog
        self._source_schema = source_schema

    def name(self) -> str:
        return "trino2bigquery"

    def bigquery_destination_table(self, table_name: str) -> str:
        return f"`{self._project_id}.{self._dataset_id}.{table_name}`"

    def convert_model_key_to_bigquery_out(self, key: AssetKey) -> AssetKey:
        return AssetKey(
            path=[*self._prefix, key.path[-1]],
        )

    def create_export_asset(
        self,
        mesh: SQLMeshInstance,
        translator: SQLMeshDagsterTranslator,
        to_export: t.List[t.Tuple[Model, AssetKey]],  # Added translator parameter
    ) -> SQLMeshExportedAssetDefinition:
        bigquery_outs = {
            key.path[-1]: self.convert_model_key_to_bigquery_out(key)
            for _, key in to_export
        }
        internal_asset_deps: t.Mapping[str, t.Set[AssetKey]] = {
            key.path[-1]: {key} for _, key in to_export
        }
        deps = [key for _, key in to_export]

        return SQLMeshExportedAssetDefinition.from_dagster_objs(
            outs=bigquery_outs,
            internal_asset_deps=internal_asset_deps,
            deps=deps,
        )

    def asset_function(self, definition: SQLMeshExportedAssetDefinition):
        async def trino_bigquery_export(
            context: AssetExecutionContext,
            trino_exporter: TrinoExporterResource,
            bigquery_importer: BigQueryImporterResource,
        ):
            async with trino_exporter.get_exporter(
                "trino-export", log_override=context.log
            ) as exporter:
                with bigquery_importer.get() as importer:
                    selected_output_names = list(
                        context.op_execution_context.selected_output_names
                    )

                    if len(selected_output_names) > BIGQUERY_BATCH_SIZE:
                        context.log.info(
                            f"Large number of tables detected ({len(selected_output_names)}). "
                            f"Processing in batches of {BIGQUERY_BATCH_SIZE} to respect BigQuery limits."
                        )

                        total_batches = math.ceil(
                            len(selected_output_names) / BIGQUERY_BATCH_SIZE
                        )

                        for batch_num, batch in enumerate(
                            batched(selected_output_names, BIGQUERY_BATCH_SIZE), 1
                        ):
                            context.log.info(
                                f"Processing batch {batch_num}/{total_batches}: {len(batch)} tables"
                            )

                            for table_name in batch:
                                await transfer(
                                    Source(
                                        exporter=exporter,
                                        table=TableReference(
                                            catalog_name=self._source_catalog,
                                            schema_name=self._source_schema,
                                            table_name=table_name,
                                        ),
                                    ),
                                    Destination(
                                        importer=importer,
                                        table=TableReference(
                                            schema_name=self._dataset_id,
                                            table_name=table_name,
                                        ),
                                    ),
                                    log_override=context.log,
                                )
                                yield MaterializeResult(
                                    asset_key=AssetKey(table_name).with_prefix(
                                        self._prefix
                                    )
                                )
                    else:
                        for table_name in selected_output_names:
                            await transfer(
                                Source(
                                    exporter=exporter,
                                    table=TableReference(
                                        catalog_name=self._source_catalog,
                                        schema_name=self._source_schema,
                                        table_name=table_name,
                                    ),
                                ),
                                Destination(
                                    importer=importer,
                                    table=TableReference(
                                        schema_name=self._dataset_id,
                                        table_name=table_name,
                                    ),
                                ),
                                log_override=context.log,
                            )
                            yield MaterializeResult(
                                asset_key=AssetKey(table_name).with_prefix(self._prefix)
                            )

        return trino_bigquery_export

    def generate_create_table_query(
        self, model: Model, destination_table: str
    ) -> exp.Expression:
        base_create_query = f"""
            CREATE TABLE IF NOT EXISTS {destination_table} (
                placeholder STRING
            )
        """

        columns = model.columns_to_types
        assert columns is not None, "columns must not be None"

        create_query = parse_one(base_create_query, dialect="bigquery")
        create_query.this.set(
            "expressions",
            [
                exp.ColumnDef(this=exp.to_identifier(column_name), kind=column_type)
                for column_name, column_type in columns.items()
            ],
        )

        return create_query

    def generate_insert_query(
        self, model: Model, destination_table: str
    ) -> exp.Expression:
        assert model.columns_to_types is not None, "columns must not be None"
        select = exp.select(*list(model.columns_to_types.keys())).from_(
            model.name, dialect="bigquery"
        )
        insert = exp.Insert(
            this=exp.to_table(destination_table, dialect="bigquery"),
            expression=select,
        )

        return insert


class DuckDB2BigQuerySQLMeshExporter(SQLMeshExporter):
    def __init__(
        self,
        prefix: str | t.List[str],
        *,
        source_catalog: str,
        source_schema: str,
        project_id: str,
        dataset_id: str,
        bucket_name: str,
    ):
        self._prefix = prefix
        self._source_catalog = source_catalog
        self._source_schema = source_schema
        self._project_id = project_id
        self._dataset_id = dataset_id
        self._bucket_name = bucket_name

    def name(self) -> str:
        return "duckdb2bigquery"

    def bigquery_destination_table(self, table_name: str) -> str:
        return f"`{self._project_id}.{self._dataset_id}.{table_name}`"

    def convert_model_key_to_bigquery_out(self, key: AssetKey) -> AssetKey:
        return AssetKey(
            path=[*self._prefix, key.path[-1]],
        )

    def create_export_asset(
        self,
        mesh: SQLMeshInstance,
        translator: SQLMeshDagsterTranslator,
        to_export: t.List[t.Tuple[Model, AssetKey]],  # Added translator parameter
    ) -> SQLMeshExportedAssetDefinition:
        bigquery_outs = {
            key.path[-1]: self.convert_model_key_to_bigquery_out(key)
            for _, key in to_export
        }
        internal_asset_deps: t.Mapping[str, t.Set[AssetKey]] = {
            key.path[-1]: {key} for _, key in to_export
        }
        deps = [key for _, key in to_export]

        return SQLMeshExportedAssetDefinition.from_dagster_objs(
            outs=bigquery_outs,
            internal_asset_deps=internal_asset_deps,
            deps=deps,
        )

    def asset_function(self, definition: SQLMeshExportedAssetDefinition):
        async def duckdb_bigquery_export(
            context: AssetExecutionContext,
            duckdb_exporter: DuckDBExporterResource,
            bigquery_importer: BigQueryImporterResource,
        ):
            async with duckdb_exporter.get(
                export_prefix=(
                    self._prefix
                    if isinstance(self._prefix, str)
                    else "_".join(self._prefix)
                ),
                gcs_bucket_name=self._bucket_name,
            ) as exporter:
                with bigquery_importer.get() as importer:
                    selected_output_names = list(
                        context.op_execution_context.selected_output_names
                    )

                    if len(selected_output_names) > BIGQUERY_BATCH_SIZE:
                        context.log.info(
                            f"Large number of tables detected ({len(selected_output_names)}). "
                            f"Processing in batches of {BIGQUERY_BATCH_SIZE} to respect BigQuery limits."
                        )

                        total_batches = math.ceil(
                            len(selected_output_names) / BIGQUERY_BATCH_SIZE
                        )

                        for batch_num, batch in enumerate(
                            batched(selected_output_names, BIGQUERY_BATCH_SIZE), 1
                        ):
                            context.log.info(
                                f"Processing batch {batch_num}/{total_batches}: {len(batch)} tables"
                            )

                            for table_name in batch:
                                await transfer(
                                    Source(
                                        exporter=exporter,
                                        table=TableReference(
                                            catalog_name=self._source_catalog,
                                            schema_name=self._source_schema,
                                            table_name=table_name,
                                        ),
                                    ),
                                    Destination(
                                        importer=importer,
                                        table=TableReference(
                                            schema_name=self._dataset_id,
                                            table_name=table_name,
                                        ),
                                    ),
                                    log_override=context.log,
                                )
                                yield MaterializeResult(
                                    asset_key=AssetKey(table_name).with_prefix(
                                        self._prefix
                                    )
                                )
                    else:
                        for table_name in selected_output_names:
                            await transfer(
                                Source(
                                    exporter=exporter,
                                    table=TableReference(
                                        catalog_name=self._source_catalog,
                                        schema_name=self._source_schema,
                                        table_name=table_name,
                                    ),
                                ),
                                Destination(
                                    importer=importer,
                                    table=TableReference(
                                        schema_name=self._dataset_id,
                                        table_name=table_name,
                                    ),
                                ),
                                log_override=context.log,
                            )
                            yield MaterializeResult(
                                asset_key=AssetKey(table_name).with_prefix(self._prefix)
                            )

        return duckdb_bigquery_export

    def generate_create_table_query(
        self, model: Model, destination_table: str
    ) -> exp.Expression:
        base_create_query = f"""
            CREATE TABLE IF NOT EXISTS {destination_table} (
                placeholder STRING
            )
        """

        columns = model.columns_to_types
        assert columns is not None, "columns must not be None"

        create_query = parse_one(base_create_query, dialect="bigquery")
        create_query.this.set(
            "expressions",
            [
                exp.ColumnDef(this=exp.to_identifier(column_name), kind=column_type)
                for column_name, column_type in columns.items()
            ],
        )

        return create_query

    def generate_insert_query(
        self, model: Model, destination_table: str
    ) -> exp.Expression:
        assert model.columns_to_types is not None, "columns must not be None"
        select = exp.select(*list(model.columns_to_types.keys())).from_(
            model.name, dialect="bigquery"
        )
        insert = exp.Insert(
            this=exp.to_table(destination_table, dialect="bigquery"),
            expression=select,
        )

        return insert


class Trino2DuckDBSQLMeshExporter(SQLMeshExporter):
    def __init__(
        self,
        prefix: str | t.List[str],
        *,
        destination_catalog: str,
        destination_schema: str,
        source_catalog: str,
        source_schema: str,
    ):
        self._prefix = prefix
        self._destination_catalog = destination_catalog
        self._destination_schema = destination_schema
        self._source_catalog = source_catalog
        self._source_schema = source_schema

    def name(self) -> str:
        return "trino2duckdb"

    def convert_model_key_to_duckdb_out(self, key: AssetKey) -> AssetKey:
        return AssetKey(
            path=[*self._prefix, key.path[-1]],
        )

    def create_export_asset(
        self,
        mesh: SQLMeshInstance,
        translator: SQLMeshDagsterTranslator,  # Added translator parameter
        to_export: t.List[t.Tuple[Model, AssetKey]],
    ) -> SQLMeshExportedAssetDefinition:
        duckdb_outs = {
            key.path[-1]: self.convert_model_key_to_duckdb_out(key)
            for _, key in to_export
        }
        internal_asset_deps: t.Mapping[str, t.Set[AssetKey]] = {
            key.path[-1]: {key} for _, key in to_export
        }
        deps = [key for _, key in to_export]

        return SQLMeshExportedAssetDefinition.from_dagster_objs(
            outs=duckdb_outs,
            internal_asset_deps=internal_asset_deps,
            deps=deps,
        )

    def asset_function(self, definition: SQLMeshExportedAssetDefinition):
        async def trino_duckdb_export(
            context: AssetExecutionContext,
            trino_exporter: TrinoExporterResource,
            duckdb_importer: DuckDBImporterResource,
        ):
            async with trino_exporter.get_exporter(
                "trino-export", log_override=context.log
            ) as exporter:
                with duckdb_importer.get() as importer:
                    selected_output_names = (
                        context.op_execution_context.selected_output_names
                    )
                    for table_name in selected_output_names:
                        await transfer(
                            Source(
                                exporter=exporter,
                                table=TableReference(
                                    catalog_name=self._source_catalog,
                                    schema_name=self._source_schema,
                                    table_name=table_name,
                                ),
                            ),
                            Destination(
                                importer=importer,
                                table=TableReference(
                                    catalog_name=self._destination_catalog,
                                    schema_name=self._destination_schema,
                                    table_name=table_name,
                                ),
                            ),
                            log_override=context.log,
                        )
                        yield MaterializeResult(
                            asset_key=AssetKey(table_name).with_prefix(self._prefix)
                        )

        return trino_duckdb_export
