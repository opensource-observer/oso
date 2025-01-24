import logging
import typing as t
from datetime import datetime

import duckdb
import pyarrow as pa
from google.cloud import bigquery, bigquery_storage_v1
from metrics_tools.local.config import (
    Config,
    DestinationLoader,
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


def convert_bq_schema_to_duckdb_columns(
    column_ids: t.List[str], bq_schema: t.List[bigquery.SchemaField]
) -> t.List[t.Tuple[str, str]]:
    # Create a dictionary of the schema
    schema_dict = {field.name: field for field in bq_schema}
    columns: t.List[t.Tuple[str, str]] = []
    for column_id in column_ids:
        field = schema_dict[column_id]

        # force structs as json for trino later
        if field.field_type == "STRUCT":
            columns.append((field.name, "JSON"))
            continue

        columns.append(
            (
                field.name,
                parse_one(field.field_type, into=exp.DataType, dialect="bigquery").sql(
                    dialect="duckdb"
                ),
            )
        )
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
    reader = client.read_rows(session.streams[0].name)
    return reader.to_arrow(session)


class BaseDestinationLoader(DestinationLoader):
    def __init__(
        self,
        bqclient: bigquery.Client,
        duckdb_conn: duckdb.DuckDBPyConnection,
    ):
        self._duckdb_conn = duckdb_conn
        self._bqclient = bqclient

    def destination_table_exists(self, table: exp.Table) -> bool:
        raise NotImplementedError("table_exists not implemented")

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
        config: Config,
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

        if self.destination_table_exists(rewritten_destination):
            logger.info(
                f"{destination.table} already exists at destination as {rewritten_destination}, skipping"
            )
            return
        if destination.has_restriction():
            logger.info(f"Table {destination.table} has restrictions")
            table_as_arrow = bq_read_with_options(
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

        # Load the schema from bigqouery
        table_schema = self._bqclient.get_table(source_table).schema

        # If there are no special metadata fields in a schema we can just do a
        # straight copy into duckdb
        is_simple_copy = True
        column_ids = [field.name for field in table_as_arrow.schema]
        columns = convert_bq_schema_to_duckdb_columns(column_ids, table_schema)
        column_types = set([column[1] for column in columns])

        if "JSON" in column_types:
            is_simple_copy = False

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

        if is_simple_copy:
            query = f"CREATE TABLE IF NOT EXISTS {duckdb_table_name} AS SELECT * FROM table_as_arrow"
            logger.debug(f"EXECUTING={query}")
            self._duckdb_conn.execute(query)
        else:
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

    def destination_table_rewrite(self, table_fqn: str) -> exp.Table:
        return oso_source_rewrite(DUCKDB_REWRITE_RULES, table_fqn)

    def commit_to_destination(self, duckdb_table_name: str, destination: exp.Table):
        self._duckdb_conn.execute(f"CREATE SCHEMA IF NOT EXISTS {destination.db}")
        self._duckdb_conn.execute(
            f"CREATE TABLE {destination.sql(dialect='duckdb')} AS SELECT * FROM {duckdb_table_name}"
        )
        # Drop the temporary table
        self._duckdb_conn.execute(f"DROP TABLE {duckdb_table_name}")


class PostgresDestinationLoader(BaseDestinationLoader):
    def __init__(
        self,
        bqclient: bigquery.Client,
        duckdb_conn: duckdb.DuckDBPyConnection,
        postgres_conn: pg_connection,
        postgres_host: str,
        postgres_port: int,
        postgres_db: str,
        postgres_user: str,
        postgres_password: str,
    ):
        super().__init__(bqclient, duckdb_conn)
        self._postgres_conn = postgres_conn
        self._connected_to_postgres = False
        self._postgres_host = postgres_host
        self._postgres_port = postgres_port
        self._postgres_db = postgres_db
        self._postgres_user = postgres_user
        self._postgres_password = postgres_password

    def _connect_to_postgres(self):
        if not self._connected_to_postgres:
            self._duckdb_conn.execute(
                f"""
                INSTALL postgres;
                LOAD postgres;
                ATTACH 'dbname={self._postgres_db} user={self._postgres_user} password={self._postgres_password} host={self._postgres_host}' AS postgres_db (TYPE POSTGRES)
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

    def destination_table_rewrite(self, table_fqn: str) -> exp.Table:
        table = exp.to_table(table_fqn)
        return exp.to_table(f"postgres_db.{table.db}.{table.this}")

    def commit_to_destination(self, duckdb_table_name: str, destination: exp.Table):
        self._connect_to_postgres()
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
            elif "[]" in column[1]:
                column_select.append(f"{column[0]}::JSON as {column[0]}")
            else:
                column_select.append(column[0])
        all_columns = ", ".join(column_select)

        self._duckdb_conn.execute(
            f"CREATE TABLE {destination.sql(dialect='postgres')} AS SELECT {all_columns} FROM {duckdb_table_name}"
        )
        # Drop the temporary table
        self._duckdb_conn.execute(f"DROP TABLE {duckdb_table_name}")
