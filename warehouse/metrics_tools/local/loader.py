import json
import logging
import os
import re
import typing as t
from datetime import datetime, timedelta

import duckdb
import pyarrow as pa
from google.cloud import bigquery, bigquery_storage_v1
from kr8s.objects import Service
from metrics_tools.local.config import (
    Config,
    DestinationLoader,
    LocalTrinoLoaderConfig,
    TableMappingDestination,
)
from metrics_tools.source.rewrite import (
    DUCKDB_REWRITE_RULES,
    LOCAL_TRINO_REWRITE_RULES,
    oso_source_rewrite,
)
from minio import Minio
from pyiceberg.catalog import Catalog
from pyiceberg.typedef import Identifier
from sqlglot import exp
from sqlmesh.core.dialect import parse_one

logger = logging.getLogger(__name__)


def remove_metadata_from_schema(schema: pa.Schema) -> pa.Schema:
    """Remove metadata from a schema

    Duckdb sometimes has issues with metadata in the schema. This function
    removes all metadata
    """
    fields_without_metadata = [
        pa.field(field.name, field.type)  # Create fields without metadata
        for field in schema
    ]
    return pa.schema(fields_without_metadata)


def filter_columns(
    column_ids: t.List[str], columns: t.List[t.Tuple[str, str]]
) -> t.List[t.Tuple[str, str]]:
    # Create a dictionary of the columns by id
    schema_dict = {column[0]: column[1] for column in columns}
    new_columns: t.List[t.Tuple[str, str]] = []
    for column_id in column_ids:
        field = schema_dict[column_id]
        new_columns.append(
            (
                column_id,
                field,
            )
        )
    return new_columns


DUCKDB_TYPES_MAPPING: t.Dict[str, str] = {
    "REAL": "DOUBLE",
    "INT": "BIGINT",
}


# When converting to duckdb, some types are automatically changed for bigger precision.
# We also remove the struct information and just keep the struct type.
def map_type_to_duckdb_type(original_type: str) -> str:
    result_type = original_type
    # Because types can be nested (e.g. STRUCT<STRUCT<n INT>>),
    # we brute force replace, but only on word boundaries to avoid
    # substring issues, e.g: BIGINT -> BIGBIGINT
    for from_type, to_type in DUCKDB_TYPES_MAPPING.items():
        result_type = re.sub(r"\b" + from_type + r"\b", to_type, result_type)
    # remove quotes for easier comparison
    return result_type.replace('"', "")


def convert_bq_schema_to_bq_columns(
    bq_schema: t.Iterable[bigquery.SchemaField],
) -> t.List[t.Tuple[str, str]]:
    # Create a dictionary of the schema
    schema_dict = {field.name: field for field in bq_schema}
    columns: t.List[t.Tuple[str, str]] = []
    for field_name, field in schema_dict.items():
        field_type = field.field_type
        assert field_type is not None, f"Field type is None for {field_name}"

        if field_type == "RECORD" or field_type == "STRUCT":
            inner_fields = convert_bq_schema_to_bq_columns(field.fields)
            # [(name1, type1), (name1, type2)] => ["name1 type1", "name2 type2"]
            flattened_fields = [f"{f[0]} {f[1]}" for f in inner_fields]
            # ["name1 type1", "name2 type2"] => ""name1 type1, name2 type2"
            field_type = f"STRUCT<{', '.join(flattened_fields)}>"
        if field.mode == "REPEATED":
            field_type = f"ARRAY<{field_type}>"

        columns.append(
            (
                field_name,
                field_type,
            )
        )
    return columns


def convert_bq_schema_to_duckdb_columns(
    bq_schema: t.Iterable[bigquery.SchemaField],
) -> t.List[t.Tuple[str, str]]:
    bq_columns = convert_bq_schema_to_bq_columns(bq_schema)
    result = [
        (
            item[0],
            map_type_to_duckdb_type(
                parse_one(item[1], into=exp.DataType, dialect="bigquery").sql(
                    dialect="duckdb"
                )
            ),
        )
        for item in bq_columns
    ]

    return result


def bq_read_with_options(
    start: datetime,
    end: datetime,
    source_table: str,
    dest: TableMappingDestination,
    project_id: str,
):
    client = bigquery_storage_v1.BigQueryReadClient()
    source_table_split = source_table.split(".")
    table = "projects/{}/datasets/{}/tables/{}".format(
        source_table_split[0], source_table_split[1], source_table_split[2]
    )
    requested_session = bigquery_storage_v1.types.ReadSession()
    requested_session.table = table

    requested_session.data_format = bigquery_storage_v1.types.DataFormat.ARROW
    row_restrictions = dest.row_restriction.as_str(start, end)
    logger.info(f"Row restrictions: {row_restrictions}")
    requested_session.read_options.row_restriction = row_restrictions

    parent = "projects/{}".format(project_id)
    session = client.create_read_session(
        parent=parent, read_session=requested_session, max_stream_count=1
    )
    if len(session.streams) == 0:
        logger.info("No result found for the given restrictions")
        return None
    reader = client.read_rows(session.streams[0].name)
    return reader.to_arrow(session)


def bq_try_read_with_options(
    start: datetime,
    end: datetime,
    source_table: str,
    dest: TableMappingDestination,
    project_id: str,
    max_results_per_query: int,
):
    result = None
    increment = timedelta(days=1)
    # Exponential increments for reading from bigquery, in case the initial
    # restriction is too small
    while result is None:
        result = bq_read_with_options(start, end, source_table, dest, project_id)
        start = start - increment
        increment = increment * 2

    return result.slice(
        0,
        min(result.num_rows, max_results_per_query),
    )


class BaseDestinationLoader(DestinationLoader):
    def __init__(
        self,
        config: Config,
        bqclient: bigquery.Client,
        duckdb_conn: duckdb.DuckDBPyConnection,
    ):
        self._config = config
        self._duckdb_conn = duckdb_conn
        self._bqclient = bqclient
        self._created_schemas = set()

    def destination_table_exists(self, table: exp.Table) -> bool:
        raise NotImplementedError("table_exists not implemented")

    def destination_table_schema(self, table: exp.Table) -> t.List[t.Tuple[str, str]]:
        raise NotImplementedError("table_schema not implemented")

    def destination_table_rewrite(self, table_fqn: str) -> exp.Table:
        raise NotImplementedError("table_rewrite not implemented")

    def commit_table(
        self,
        source_name: str,
        destination: TableMappingDestination,
        rewritten_destination: exp.Table,
        table_as_arrow: pa.Table,
        table_schema: t.List[bigquery.SchemaField],
    ):
        raise NotImplementedError("save_pyarrow_table not implemented")

    def commit_to_destination(self, duckdb_table_name: str, destination: exp.Table):
        raise NotImplementedError("commit_to_destination not implemented")

    def drop_table(self, table: exp.Table):
        raise NotImplementedError("drop_table not implemented")

    def convert_bq_schema_to_columns(self, bq_schema: t.List[bigquery.SchemaField]):
        raise NotImplementedError("convert_bq_schema_to_columns not implemented")

    def has_schema_changed(
        self, destination: exp.Table, bq_schema: t.List[bigquery.SchemaField]
    ):
        columns = self.convert_bq_schema_to_columns(bq_schema)
        destination_table_schema = self.destination_table_schema(destination)
        result = set(columns) != set(destination_table_schema)
        if result:
            logger.debug(f"Schema for {destination} has changed:")
            logger.debug(destination_table_schema)
            logger.debug(columns)
        return result

    def load_from_bq(
        self,
        start: datetime,
        end: datetime,
        source_name: str,
        destination: TableMappingDestination,
    ):
        """Loading from bq happens first by loading into a temporary duckdb table"""
        logger.info(f"Loading {source_name} into {destination.table}")

        source_table = bigquery.TableReference.from_string(source_name)

        rewritten_destination = self.destination_table_rewrite(destination.table)
        config = self._config

        # Load the schema from bigqouery
        table_schema = self._bqclient.get_table(source_table).schema

        if self.destination_table_exists(rewritten_destination):
            if self.has_schema_changed(rewritten_destination, table_schema):
                logger.warning(
                    f"Schema mismatch for {destination.table}, dropping destination table"
                )
                self.drop_table(rewritten_destination)
            else:
                logger.info(
                    f"{destination.table} already exists at destination with the same schema as {rewritten_destination}, skipping"
                )
                return

        if destination.has_restriction():
            logger.info(f"Table {destination.table} has restrictions")
            table_as_arrow = bq_try_read_with_options(
                start,
                end,
                source_name,
                destination,
                config.project_id,
                config.max_results_per_query,
            )
        else:
            if config.max_results_per_query:
                logger.info(f"Limiting results to {config.max_results_per_query}")
                rows = self._bqclient.list_rows(source_table)
                # COLLECT SOME NUMBER OF ROWS
                total_rows = 0
                to_concat: t.List[pa.RecordBatch] = []
                client = bigquery_storage_v1.BigQueryReadClient()
                for record_batch in rows.to_arrow_iterable(bqstorage_client=client):
                    to_concat.append(record_batch)
                    total_rows += record_batch.num_rows
                    if total_rows >= config.max_results_per_query:
                        break
                if total_rows == 0:
                    logger.info(
                        "No rows found when limiting rows, resorting to full copy to get schema"
                    )
                    rows = self._bqclient.list_rows(source_table)
                    table_as_arrow = rows.to_arrow(create_bqstorage_client=True)
                else:
                    table_as_arrow = pa.Table.from_batches(to_concat)
                logger.info(f"Rows in arrow table {table_as_arrow.num_rows}")
            else:
                rows = self._bqclient.list_rows(source_table)
                table_as_arrow = rows.to_arrow(
                    create_bqstorage_client=True
                )  # noqa: F841

        # Load the table
        self.commit_table(
            source_name,
            destination,
            rewritten_destination,
            table_as_arrow,
            table_schema,
        )
        logger.info(f"Loaded {source_name} into {destination.table}")

    def drop_all(self):
        """Use this to drop all data in the duckdb database and start fresh"""
        return self.drop_like_schema_name("%")

    def drop_non_sources(self):
        return self.drop_like_schema_name("sources_%", not_like=True)

    def drop_like_schema_name(self, like_schema_name: str, not_like: bool = False):
        raise NotImplementedError("drop_like_schema_name not implemented")

    def sqlmesh_base_args(self):
        return ["sqlmesh"]

    def sqlmesh(self, extra_args: t.List[str], extra_env: t.Dict[str, str]):
        import subprocess

        if "SQLMESH_DUCKDB_LOCAL_PATH" not in extra_env:
            extra_env["SQLMESH_DUCKDB_LOCAL_PATH"] = (
                self._config.loader.config.duckdb_path
            )

        process = subprocess.Popen(
            [*self.sqlmesh_base_args(), *extra_args],
            cwd=os.path.join(self._config.repo_dir, "warehouse/oso_sqlmesh"),
            env={
                **os.environ,
                **extra_env,
            },
        )
        process.communicate()

    def close(self):
        self._duckdb_conn.close()


class DuckDbDestinationLoader(BaseDestinationLoader):
    def load_from_bq(
        self,
        start: datetime,
        end: datetime,
        source_name: str,
        destination: TableMappingDestination,
    ):
        return super().load_from_bq(start, end, source_name, destination)

    def convert_bq_schema_to_columns(self, bq_schema: t.List[bigquery.SchemaField]):
        return convert_bq_schema_to_duckdb_columns(bq_schema)

    def drop_table(self, table: exp.Table):
        self._duckdb_conn.execute(f"DROP TABLE IF EXISTS {table.sql(dialect='duckdb')}")

    def destination_table_exists(self, table: exp.Table) -> bool:
        table_name = table.sql(dialect="duckdb")
        logger.debug(f"Checking if {table_name} exists")
        response = self._duckdb_conn.query(
            f"""
            SELECT 1 
            FROM information_schema.tables 
            WHERE table_schema = '{table.db}'
            AND table_name = '{table.this}'
        """
        )
        return len(response.fetchall()) > 0

    def destination_table_schema(self, table: exp.Table) -> t.List[t.Tuple[str, str]]:
        table_name = table.sql(dialect="duckdb")
        response = self._duckdb_conn.query(
            f"""
            DESCRIBE {table_name}
        """
        )
        schema: t.List[t.Tuple[str, str]] = []
        for column in response.fetchall():
            schema.append(
                (
                    column[0],
                    map_type_to_duckdb_type(
                        parse_one(column[1], dialect="duckdb", into=exp.DataType).sql(
                            dialect="duckdb"
                        )
                    ),
                )
            )
        return schema

    def destination_table_rewrite(self, table_fqn: str) -> exp.Table:
        return oso_source_rewrite(DUCKDB_REWRITE_RULES, table_fqn)

    def commit_to_destination(self, duckdb_table_name: str, destination: exp.Table):
        self._duckdb_conn.execute(f"CREATE SCHEMA IF NOT EXISTS {destination.db}")
        self._duckdb_conn.execute(
            f"CREATE TABLE {destination.sql(dialect='duckdb')} AS SELECT * FROM {duckdb_table_name}"
        )
        # Drop the temporary table
        self._duckdb_conn.execute(f"DROP TABLE {duckdb_table_name}")

    def drop_like_schema_name(self, like_schema_name: str, not_like: bool = False):
        not_like_str = "NOT " if not_like else ""

        schemas = self._duckdb_conn.execute(
            f"""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name {not_like_str} LIKE '{like_schema_name}'
            AND schema_name NOT IN ('information_schema', 'duckdb', 'main', 'pg_catalog')
            """
        ).fetchall()

        for schema in schemas:
            schema_name = schema[0]
            logger.info(f"Dropping schema {schema_name}")
            self._duckdb_conn.execute(f"DROP SCHEMA {schema_name} CASCADE")

    def commit_table(
        self,
        source_name: str,
        destination: TableMappingDestination,
        rewritten_destination: exp.Table,
        table_as_arrow: pa.Table,
        table_schema: t.List[bigquery.SchemaField],
    ):
        duckdb_table_name = f"oso_local_temp.{rewritten_destination.this.sql(dialect="duckdb")}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        columns = self.convert_bq_schema_to_columns(table_schema)

        logger.debug(f"Column types: {table_schema}")

        # Remove all metadata from the schema
        new_schema = remove_metadata_from_schema(table_as_arrow.schema)
        table_as_arrow = table_as_arrow.cast(new_schema)

        duckdb_table_split = duckdb_table_name.split(".")
        schema = duckdb_table_split[0]

        logger.debug(f"copying {table_as_arrow.num_rows} rows to {duckdb_table_name}")
        if schema not in self._created_schemas:
            logger.info(f"Creating schema {schema}")
            self._duckdb_conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
            self._created_schemas.add(schema)

        create_query = parse_one(
            f"""
            CREATE TABLE IF NOT EXISTS {duckdb_table_name} (placeholder VARCHAR);
        """
        )
        create_query.this.set(
            "expressions",
            [
                exp.ColumnDef(
                    this=exp.Identifier(
                        this=column_name,
                        quoted=True,
                    ),
                    kind=parse_one(
                        data_type,
                        dialect="duckdb",
                        into=exp.DataType,
                    ),
                )
                for column_name, data_type in columns
            ],
        )
        logger.debug(f"EXECUTING={create_query.sql(dialect="duckdb")}")
        self._duckdb_conn.execute(create_query.sql(dialect="duckdb"))

        insert_query = parse_one(
            f"INSERT INTO {duckdb_table_name} (placeholder) SELECT placeholder FROM table_as_arrow"
        )
        insert_query.this.set(
            "expressions",
            [
                exp.Identifier(this=column_name, quoted=True)
                for column_name, _ in columns
            ],
        )
        insert_query.expression.set(
            "expressions",
            [exp.to_column(column_name, quoted=True) for column_name, _ in columns],
        )
        logger.debug(f"EXECUTING={insert_query.sql(dialect="duckdb")}")
        self._duckdb_conn.execute(insert_query.sql(dialect="duckdb"))

        self.commit_to_destination(duckdb_table_name, rewritten_destination)


class SerializedBqSchema(t.TypedDict):
    field_type: str
    is_nullable: bool
    max_length: t.NotRequired[int]
    mode: t.NotRequired[str]
    name: str
    precision: t.NotRequired[int]
    scale: t.NotRequired[int]
    fields: t.NotRequired[t.List["SerializedBqSchema"]]


class LocalTrinoDestinationLoader(BaseDestinationLoader):
    def __init__(
        self,
        config: Config,
        bqclient: bigquery.Client,
        duckdb_conn: duckdb.DuckDBPyConnection,
        minio_client: Minio,
        iceberg_catalog: Catalog,
        minio_url: str,
        iceberg_properties: t.Dict[str, str],
        schema_table_schema="oso_local_state",
        schema_table_name="bq_schema",
    ):
        super().__init__(config, bqclient, duckdb_conn)
        self._minio_client = minio_client
        self._iceberg_catalog = iceberg_catalog
        self._minio_url = minio_url
        self._iceberg_properties = iceberg_properties
        self._schema_table_schema = schema_table_schema
        self._schema_table_name = schema_table_name

    @property
    def local_trino_loader_config(self) -> LocalTrinoLoaderConfig:
        assert isinstance(
            self._config.loader.config, LocalTrinoLoaderConfig
        ), "Loader config is not a LocalTrinoLoaderConfig"
        return self._config.loader.config

    def destination_table_exists(self, table: exp.Table) -> bool:
        logger.debug(f"Checking if {table} exists")
        return self._iceberg_catalog.table_exists(f"{table.db}.{table.this}")

    def destination_table_rewrite(self, table_fqn: str) -> exp.Table:
        """Due to the `oso` name being in conflict we force the schema to add `bq_` as a prefix"""

        return oso_source_rewrite(LOCAL_TRINO_REWRITE_RULES, table_fqn)

    def has_schema_changed(
        self, destination: exp.Table, bq_schema: t.List[bigquery.SchemaField]
    ):
        # We don't have a reliable way of checking if the schema has changed in trino
        # Instead we store the schema in a duckdb table and compare the schema there
        current_schema = self.load_bigquery_schema(destination)
        serialized_bq_schema = self.serialize_bigquery_schema(bq_schema)
        return json.dumps(serialized_bq_schema) != json.dumps(current_schema)

    def drop_like_schema_name(self, like_schema_name: str, not_like: bool = False):
        like_regex = re.compile(f"^{like_schema_name.replace("%", ".*")}$")
        namespaces = self._iceberg_catalog.list_namespaces()
        for namespace_identifier in namespaces:
            namespace = namespace_identifier[0]
            if not not_like:
                if like_regex.match(namespace):
                    logger.info(f"Dropping namespace {namespace}")
                    self.drop_all_in_namespace(namespace)
                    try:
                        self._iceberg_catalog.drop_namespace(namespace)
                    except Exception as e:
                        logger.warning(f"Failed to drop namespace {namespace}")
                        logger.error(e)
            else:
                if not like_regex.match(namespace):
                    logger.info(f"Dropping namespace {namespace}")
                    self.drop_all_in_namespace(namespace)
                    try:
                        self._iceberg_catalog.drop_namespace(namespace)
                    except Exception as e:
                        logger.warning(f"Failed to drop namespace {namespace}")
                        logger.error(e)

    def drop_all_in_namespace(self, namespace: str):
        tables = self._iceberg_catalog.list_tables(namespace)
        for table in tables:
            logger.info(f"Dropping table {table}")
            self._iceberg_catalog.drop_table(table)

        views = self._iceberg_catalog.list_views(namespace)
        for view in views:
            logger.info(f"Dropping view {view}")
            self._iceberg_catalog.drop_view(view)

    def sqlmesh_base_args(self):
        return ["sqlmesh", "--gateway", "local-trino"]

    def sqlmesh(self, extra_args: t.List[str], extra_env: t.Dict[str, str]):
        trino_service = Service.get(
            namespace=self.local_trino_loader_config.trino_k8s_namespace,
            name=self.local_trino_loader_config.trino_k8s_service,
        )
        with trino_service.portforward(remote_port="8080") as local_port:  # type: ignore
            logger.info(f"Proxied trino to port {local_port} for sqlmesh")

            env = {
                **extra_env,
                "SQLMESH_DUCKDB_LOCAL_PATH": self.local_trino_loader_config.duckdb_path,
                "SQLMESH_TRINO_HOST": "localhost",
                "SQLMESH_TRINO_PORT": str(local_port),
                "SQLMESH_TRINO_CONCURRENT_TASKS": "1",
                "SQLMESH_MCS_ENABLED": "0",
                # We set this variable to ensure that we run the minimal
                # amount of data. By default this ensure that we only
                # calculate metrics from 2024-12-01. For now this is only
                # set for trino but must be explicitly set for duckdb
                "SQLMESH_TIMESERIES_METRICS_START": self._config.timeseries_start,
            }

            super().sqlmesh(extra_args, env)

    @property
    def schema_table(self):
        return f"{self._schema_table_schema}.{self._schema_table_name}"

    def save_bigquery_schema(
        self, table: exp.Table, schema: t.List[bigquery.SchemaField]
    ):
        self._duckdb_conn.execute(
            f"CREATE SCHEMA IF NOT EXISTS {self._schema_table_schema}"
        )
        self._duckdb_conn.execute(
            f"CREATE TABLE IF NOT EXISTS {self.schema_table} (table_name VARCHAR, serialized_schema JSON)"
        )

        serialized_schema = json.dumps(self.serialize_bigquery_schema(schema))

        self._duckdb_conn.execute(
            f"INSERT INTO {self.schema_table} VALUES ('{table.sql(dialect="trino")}', '{serialized_schema}')"
        )

    def load_bigquery_schema(self, table: exp.Table) -> t.List[bigquery.SchemaField]:
        try:
            response = self._duckdb_conn.query(
                f"SELECT serialized_schema FROM {self.schema_table} WHERE table_name = '{table.sql(dialect='trino')}'"
            )
        except duckdb.CatalogException:
            return []

        raw_serialized_schema = response.fetchone()
        if raw_serialized_schema is None:
            return []

        serialized_schema = json.loads(raw_serialized_schema[0])
        return t.cast(t.List[bigquery.SchemaField], serialized_schema)

    def serialize_bigquery_schema(
        self, schema: t.List[bigquery.SchemaField]
    ) -> t.List[SerializedBqSchema]:
        """A hacky way to serialize the bq schema for schema comparison"""
        sorted_schema = sorted(schema, key=lambda x: x.name)

        serialized_schema_fields: t.List[SerializedBqSchema] = []
        for field in sorted_schema:
            field_type = field.field_type
            assert field_type is not None, f"Field type for {field.name} cannot be None"
            serialized_field: SerializedBqSchema = {
                "field_type": field_type,
                "is_nullable": field.is_nullable,
                "name": field.name,
            }
            if field.mode:
                serialized_field["mode"] = field.mode
            if field.max_length:
                serialized_field["max_length"] = field.max_length
            if field.precision:
                serialized_field["precision"] = field.precision
            if field.scale:
                serialized_field["scale"] = field.scale
            if field.fields:
                serialized_field["fields"] = self.serialize_bigquery_schema(
                    list(field.fields)
                )
            serialized_schema_fields.append(serialized_field)
        return serialized_schema_fields

    def drop_table(self, table: exp.Table):
        logger.info(f"dropping {table.db}.{table.this} table on iceberg ")
        self._iceberg_catalog.drop_table(f"{table.db}.{table.this}")

    def commit_table(
        self,
        source_name: str,
        destination: TableMappingDestination,
        rewritten_destination: exp.Table,
        table_as_arrow: pa.Table,
        table_schema: t.List[bigquery.SchemaField],
    ):
        logger.info(f"Committing {rewritten_destination} to iceberg")
        self._iceberg_catalog.create_namespace_if_not_exists(rewritten_destination.db)
        table = self._iceberg_catalog.create_table_if_not_exists(
            f"{rewritten_destination.db}.{rewritten_destination.this}",
            schema=table_as_arrow.schema,
        )

        logger.info("Storing bigquery schema in duckdb")
        self.save_bigquery_schema(rewritten_destination, table_schema)

        # This seems to be necessary to rewrite the minio url because pyiceberg
        # ignores the initial config. Likely, it reads the minio url from
        # the catalog.
        table.io.properties["s3.endpoint"] = self._minio_url
        try:
            table.append(table_as_arrow)
        except Exception as e:
            logger.error(f"Failed to append data to {rewritten_destination}")
            logger.error(e)
            return
        logger.debug(f"Committed {rewritten_destination} to iceberg")

    def list_namespaces(self):
        return self._iceberg_catalog.list_namespaces()

    def list_all_tables(self) -> t.List[exp.Table]:
        tables: t.List[exp.Table] = []
        for namespace in self.list_namespaces():
            tables.extend(self.list_tables(namespace))
        return tables

    def list_tables(self, namespace: str | Identifier) -> t.List[exp.Table]:
        table_ids = self._iceberg_catalog.list_tables(namespace)
        tables: t.List[exp.Table] = []
        for table in table_ids:
            tables.append(exp.to_table(f"{table[0]}.{table[1]}"))
        return tables

    def drop_non_sources(self):
        # This won't work if we include multiple bigquery project sources (and
        # therefore multiple bigquery connectors)
        config = self._config

        table_mapping = config.table_mapping
        for table in self.list_all_tables():
            # Hacky rewrite for the playground dataset
            if table.db == "oso":
                table_as_source_name = (
                    f"opensource-observer.oso_playground.{table.this}"
                )
            else:
                table_as_source_name = (
                    f"opensource-observer.{table.sql(dialect='trino')}"
                )
            if table_as_source_name not in table_mapping:
                self.drop_table(table)
