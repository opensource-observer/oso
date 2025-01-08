"""
Auxiliary resources for sqlmesh
"""

import typing as t
from datetime import datetime

from dagster import AssetExecutionContext, AssetKey, AssetsDefinition, asset
from dagster_sqlmesh import SQLMeshDagsterTranslator
from dagster_sqlmesh.controller.base import SQLMeshInstance
from sqlglot import exp
from sqlmesh import Context
from sqlmesh.core.dialect import parse_one
from sqlmesh.core.model import Model


class SQLMeshExporter:
    name: str

    def create_export_asset(
        self, mesh: SQLMeshInstance, name: str, model: Model, key: AssetKey
    ) -> AssetsDefinition:
        raise NotImplementedError("Not implemented")


class PrefixedSQLMeshTranslator(SQLMeshDagsterTranslator):
    def __init__(self, prefix: str):
        self._prefix = prefix

    def get_asset_key_fqn(self, context: Context, fqn: str) -> AssetKey:
        key = super().get_asset_key_fqn(context, fqn)
        return key.with_prefix("production").with_prefix("dbt")

    def get_asset_key_from_model(self, context: Context, model: Model) -> AssetKey:
        key = super().get_asset_key_from_model(context, model)
        return key.with_prefix(self._prefix)


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

    def trino_destination_table(self, table_name: str):
        return f"{self._destination_catalog}.{self._destination_schema}.{table_name}"

    def clickhouse_destination_table(self, table_name: str):
        return f"{self._destination_schema}.{table_name}"

    def trino_source_table(self, table_name: str):
        return f"{self._source_catalog}.{self._source_schema}.{table_name}"

    def convert_model_key_to_clickhouse_key(self, key: AssetKey) -> AssetKey:
        return AssetKey(key.path[-1]).with_prefix(self._prefix)

    def create_export_asset(
        self, mesh: SQLMeshInstance, name: str, model: Model, key: AssetKey
    ) -> AssetsDefinition:
        from .clickhouse import ClickhouseResource
        from .trino import TrinoResource

        clickhouse_key = self.convert_model_key_to_clickhouse_key(key)

        @asset(
            key=clickhouse_key,
            deps=[key],
            compute_kind="sqlmesh-export",
        )
        async def export(
            context: AssetExecutionContext,
            trino: TrinoResource,
            clickhouse: ClickhouseResource,
        ) -> None:
            table_name = key.path[-1]
            async with trino.get_client(
                session_properties={
                    # Clickhouse doesn't support retries on trino so we _must_
                    # disable it for insert queries to work
                    "retry_policy": "None",
                    # For whatever reason this is also necessary, writes didn't
                    # work in manual testing without this set.
                    "clickhouse.non_transactional_insert": "true",
                }
            ) as connection:
                # Export the data from trino to clickhouse by creating a table
                # that has a suffix
                exported_table_name = f"{clickhouse_key.path[-1]}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                cursor = connection.cursor()
                context.log.info(f"Exporting {table_name} to {exported_table_name}")
                create_query = self.generate_create_table_query(
                    model,
                    self.trino_source_table(table_name),
                    self.trino_destination_table(exported_table_name),
                )
                context.log.info(f"executing sql: {create_query.sql(dialect='trino')}")
                cursor.execute(create_query.sql(dialect="trino"))
                # Insert the data into the new table
                insert_query = self.generate_insert_query(
                    model,
                    self.trino_source_table(table_name),
                    self.trino_destination_table(exported_table_name),
                )
                context.log.info(f"executing sql: {insert_query.sql(dialect='trino')}")
                cursor.execute(insert_query.sql(dialect="trino"))

            with clickhouse.get_client() as clickhouse_client:
                # Create the clickhouse table
                clickhouse_client.query(
                    f"""
                    CREATE OR REPLACE VIEW IF NOT EXISTS {self._destination_schema}.{table_name} AS
                    SELECT * FROM {self.clickhouse_destination_table(exported_table_name)}
                """
                )
            return None

        return export

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
