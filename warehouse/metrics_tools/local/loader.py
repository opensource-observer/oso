import logging
import os
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
from metrics_tools.source.rewrite import DUCKDB_REWRITE_RULES, oso_source_rewrite
from psycopg2._psycopg import connection as pg_connection
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
    "TEXT[]": "TEXT",
}

# When converting to duckdb, some types are automatically changed for bigger precision.
# We also remove the struct information and just keep the struct type.
def map_type_to_duckdb_type(type: str) -> str:
    if type.startswith("STRUCT"):
        return "STRUCT"
    if type in DUCKDB_TYPES_MAPPING:
        return DUCKDB_TYPES_MAPPING[type]
    return type

def convert_bq_schema_to_duckdb_columns(
    bq_schema: t.List[bigquery.SchemaField]
) -> t.List[t.Tuple[str, str]]:
    # Create a dictionary of the schema
    schema_dict = {field.name: field for field in bq_schema}
    columns: t.List[t.Tuple[str, str]] = []
    for _, field in schema_dict.items():
        field_type = field.field_type
        from_dialect = "bigquery"
        # force structs as json for trino later
        if field_type == "STRUCT":
            field_type = "JSON"
        elif field_type == "RECORD":
            field_type = "JSON"
        elif field_type == "INTEGER":
            field_type = "INT64"
            from_dialect = "duckdb"
        elif field_type == "FLOAT":
            field_type = "DOUBLE"
            from_dialect = "duckdb"

        if field.mode == "REPEATED":
            field_type = f"ARRAY<{field_type}>"
        # If the field is an integer, for some reason sqlglot doesn't properly
        # use int64 which is natively what integer is in bigquery. We need to manually set that type

        logger.info(f"Converting {field.name} from {field_type} in bigquery to duckdb")
        # Convert from bigquery to duckdb datatype
        duckdb_type = parse_one(
            field_type, into=exp.DataType, dialect=from_dialect
        ).sql(dialect="duckdb")

        duckdb_type =  map_type_to_duckdb_type(parse_one(field.field_type, into=exp.DataType, dialect="bigquery").sql(
                    dialect="duckdb"
                ))

        columns.append(
            (
                field.name,
                duckdb_type,
            )
        )
    logger.info(f"Columns: {columns}")
    return columns


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
):
    result = None
    increment = timedelta(days=1)
    # Exponential increments for reading from bigquery, in case the initial
    # restriction is too small
    while result is None:
        result = bq_read_with_options(start, end, source_table, dest, project_id)
        start = start - increment
        increment = increment * 2
        
    return result


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

    def destination_table_exists(self, table: exp.Table) -> bool:
        raise NotImplementedError("table_exists not implemented")
    
    def destination_table_schema(self, table: exp.Table) -> t.List[t.Tuple[str, str]]:
        raise NotImplementedError("table_schema not implemented")

    def destination_table_rewrite(self, table_fqn: str) -> exp.Table:
        raise NotImplementedError("table_rewrite not implemented")

    def commit_to_destination(self, duckdb_table_name: str, destination: exp.Table):
        raise NotImplementedError("commit_to_destination not implemented")

    def write_to_temp_duckdb(
        self, source_name: str, duckdb_table_name: str, table_as_arrow: pa.Table
    ):
        self._duckdb_conn.execute(f"CREATE TABLE {duckdb_table_name} AS {source_name}")

    def load_from_bq(
        self,
        start: datetime,
        end: datetime,
        source_name: str,
        destination: TableMappingDestination,
    ):
        """Loading from bq happens first by loading into a temporary duckdb table"""
        logger.info(f"Loading {source_name} into {destination.table}")

        created_schemas = set()
        source_table = bigquery.TableReference.from_string(source_name)

        rewritten_destination = self.destination_table_rewrite(destination.table)
        config = self._config
        
        # Load the schema from bigqouery
        table_schema = self._bqclient.get_table(source_table).schema
        columns = convert_bq_schema_to_duckdb_columns(table_schema)

        if self.destination_table_exists(rewritten_destination):
            destination_table_schema = self.destination_table_schema(rewritten_destination)
            if(set(columns) == set(destination_table_schema)):
                logger.info(
                    f"{destination.table} already exists at destination with the same schema as {rewritten_destination}, skipping"
                )
                return
            logger.info(f"Schema mismatch for {destination.table}, dropping destination table")
            self._duckdb_conn.execute(f"DROP TABLE {rewritten_destination.sql(dialect='duckdb')}")
            
        if destination.has_restriction():
            logger.info(f"Table {destination.table} has restrictions")
            table_as_arrow = bq_try_read_with_options(
                start,
                end,
                source_name,
                destination,
                config.project_id,
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
            else:
                rows = self._bqclient.list_rows(source_table)
                table_as_arrow = rows.to_arrow(
                    create_bqstorage_client=True
                )  # noqa: F841

        duckdb_table_name = f"oso_local_temp.{rewritten_destination.this.sql(dialect="duckdb")}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # If there are no special metadata fields in a schema we can just do a
        # straight copy into duckdb
        column_ids = [field.name for field in table_as_arrow.schema]
        columns = filter_columns(column_ids, columns)

        column_types = set([column[1] for column in columns])

        logger.debug(f"Column types: {table_schema}")

        # Remove all metadata from the schema
        new_schema = remove_metadata_from_schema(table_as_arrow.schema)
        table_as_arrow = table_as_arrow.cast(new_schema)

        duckdb_table_split = duckdb_table_name.split(".")
        schema = duckdb_table_split[0]

        logger.info(f"copying {table_as_arrow.num_rows} rows to {duckdb_table_name}")
        if schema not in created_schemas:
            logger.info(f"Creating schema {schema}")
            self._duckdb_conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
            created_schemas.add(schema)

        create_query = parse_one(
            f"""
            CREATE TABLE IF NOT EXISTS {duckdb_table_name} (placeholder VARCHAR);
        """
        )
        create_query.this.set(
            "expressions",
            [
                exp.ColumnDef(
                    this=exp.Identifier(this=column_name),
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
            [exp.Identifier(this=column_name) for column_name, _ in columns],
        )
        insert_query.expression.set(
            "expressions",
            [exp.to_column(column_name) for column_name, _ in columns],
        )
        logger.debug(f"EXECUTING={insert_query.sql(dialect="duckdb")}")
        self._duckdb_conn.execute(insert_query.sql(dialect="duckdb"))

        self.commit_to_destination(duckdb_table_name, rewritten_destination)
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
            cwd=os.path.join(self._config.repo_dir, "warehouse/metrics_mesh"),
            env={
                **os.environ,
                **extra_env,
            },
        )
        process.communicate()


class DuckDbDestinationLoader(BaseDestinationLoader):
    def destination_table_exists(self, table: exp.Table) -> bool:
        table_name = table.sql(dialect="duckdb")
        logger.info(f"checking if {table_name} exists")
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
            schema.append((column[0], map_type_to_duckdb_type(parse_one(column[1], dialect="duckdb", into=exp.DataType).sql(dialect="duckdb"))))
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


class LocalTrinoDestinationLoader(BaseDestinationLoader):
    def __init__(
        self,
        config: Config,
        bqclient: bigquery.Client,
        duckdb_conn: duckdb.DuckDBPyConnection,
        postgres_conn: pg_connection,
        postgres_host: str,
        postgres_port: int,
    ):
        super().__init__(config, bqclient, duckdb_conn)
        self._postgres_conn = postgres_conn
        self._postgres_host = postgres_host
        self._postgres_port = postgres_port
        self._connected_to_postgres = False

    @property
    def local_trino_loader_config(self) -> LocalTrinoLoaderConfig:
        assert isinstance(
            self._config.loader.config, LocalTrinoLoaderConfig
        ), "Loader config is not a LocalTrinoLoaderConfig"
        return self._config.loader.config

    def _connect_to_postgres(self):
        if not self._connected_to_postgres:
            assert (
                self._config.loader.type == "local-trino"
            ), "Somehow we are not using the local-trino loader"

            loader_config = self._config.loader.config
            assert isinstance(
                loader_config, LocalTrinoLoaderConfig
            ), "Loader config is not a LocalTrinoLoaderConfig"

            self._duckdb_conn.execute(
                f"""
                INSTALL postgres;
                LOAD postgres;
                ATTACH 'dbname={loader_config.postgres_db} user={loader_config.postgres_user} password={loader_config.postgres_password} host={self._postgres_host} port={self._postgres_port}' AS postgres_db (TYPE POSTGRES)
                """
            )
            self._connected_to_postgres = True

    def destination_table_exists(self, table: exp.Table) -> bool:
        table_name = table.sql(dialect="postgres")
        logger.info(f"checking if {table_name} exists")
        cursor = self._postgres_conn.cursor()
        cursor.execute(
            f"""
            SELECT 1 
            FROM information_schema.tables 
            WHERE table_schema = '{table.db}'
            AND table_name = '{table.this}'
        """
        )
        return len(cursor.fetchall()) > 0
    
    def destination_table_schema(self, table) -> t.List[t.Tuple[str, str]]:
        cursor = self._postgres_conn.cursor()
        cursor.execute(
            f"""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = '{table.db}'
            AND table_name = '{table.this}'
        """
        )
        schema: t.List[t.Tuple[str, str]] = []
        for column in cursor.fetchall():
            schema.append((column[0], map_type_to_duckdb_type(parse_one(column[1], dialect="postgres", into=exp.DataType).sql(dialect="duckdb"))))
        return schema

    def destination_table_rewrite(self, table_fqn: str) -> exp.Table:
        table = exp.to_table(table_fqn)
        return exp.to_table(f"postgres_db.{table.db}.{table.this}")

    def commit_to_destination(self, duckdb_table_name: str, destination: exp.Table):
        self._connect_to_postgres()
        logger.info("Committing to postgres")
        self._duckdb_conn.execute(
            f"CREATE SCHEMA IF NOT EXISTS postgres_db.{destination.db}"
        )

        # Check the schema of the table (column 0 is column number, 1 is column name, 2 is column type)
        schema = self._duckdb_conn.query(
            f"PRAGMA table_info('{duckdb_table_name}')"
        ).fetchall()
        columns = [(column[1], column[2]) for column in schema]

        column_select = []
        for column in columns:
            # Arrays and structs need to be cast to JSON
            if "STRUCT" in column[1]:
                column_select.append(f"{column[0]}::JSON as {column[0]}")
            else:
                column_select.append(column[0])
        all_columns = ", ".join(column_select)
        print(all_columns)

        create_query = f"CREATE TABLE {destination.sql(dialect='duckdb')} AS SELECT {all_columns} FROM {duckdb_table_name}"
        logger.info(f"EXECUTING={create_query}")

        self._duckdb_conn.execute(create_query)
        logger.debug(f"copy into {destination.sql(dialect="duckdb")} completed")
        # Drop the temporary table
        self._duckdb_conn.execute(f"DROP TABLE {duckdb_table_name}")

    def drop_like_schema_name(self, like_schema_name: str, not_like: bool = False):
        not_like_str = "NOT " if not_like else ""

        cursor = self._postgres_conn.cursor()
        cursor.execute(
            f"""
            SELECT schema_name 
            FROM information_schema.schemata 
            WHERE schema_name {not_like_str} LIKE '{like_schema_name}'
            AND schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
        """
        )
        schemas = cursor.fetchall()

        for schema in schemas:
            schema_name = schema[0]
            logger.info(f"Dropping schema {schema_name}")
            cursor.execute(f"DROP SCHEMA {schema_name} CASCADE")
        self._postgres_conn.commit()

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
