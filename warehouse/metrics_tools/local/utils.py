import logging
import os
import typing as t
from datetime import datetime, timedelta

import duckdb
import pyarrow as pa
from google.cloud import bigquery, bigquery_storage_v1
from oso_dagster.assets.defillama import DEFI_LLAMA_PROTOCOLS, defi_llama_slug_to_name
from pydantic import BaseModel
from sqlglot import exp
from sqlmesh.core.dialect import parse_one

logger = logging.getLogger(__name__)

PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID", "opensource-observer")

DUCKDB_SOURCES_SCHEMA_PREFIX = "sources"


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


class TableMappingDestination(BaseModel):
    row_restriction: str = ""
    destination: str = ""


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


def bq_read_with_options(
    source_table: str, dest: TableMappingDestination, project_id: str
):
    client = bigquery_storage_v1.BigQueryReadClient()
    source_table_split = source_table.split(".")
    table = "projects/{}/datasets/{}/tables/{}".format(
        source_table_split[0], source_table_split[1], source_table_split[2]
    )
    requested_session = bigquery_storage_v1.types.ReadSession()
    requested_session.table = table

    requested_session.data_format = bigquery_storage_v1.types.DataFormat.ARROW
    requested_session.read_options.row_restriction = dest.row_restriction

    parent = "projects/{}".format(project_id)
    session = client.create_read_session(
        parent=parent, read_session=requested_session, max_stream_count=1
    )
    reader = client.read_rows(session.streams[0].name)
    return reader.to_arrow(session)


def table_exists_in_duckdb(conn: duckdb.DuckDBPyConnection, table_name: str):
    logger.info(f"checking if {table_name} already exists")
    table_exp = exp.to_table(table_name)
    response = conn.query(
        f"""
        SELECT 1 
        FROM information_schema.tables 
        WHERE table_schema = '{table_exp.db}'
        AND table_name = '{table_exp.this}'
    """
    )
    return len(response.fetchall()) > 0


def bq_to_duckdb(
    table_mapping: t.Dict[str, str | TableMappingDestination],
    duckdb_path: str,
    max_results_per_query: int = 0,
):
    """Copies the tables in table_mapping to tables in duckdb

    The table_mapping is in the form:
        { "bigquery_table_fqn": "duckdb_table_fqn"}

    For JSON columns, bigquery stores them as a pyarrow string with a metadata
    extension. We convert these to JSON columns in duckdb.

    Args:
        table_mapping (t.Dict[str, str]): A dictionary of bigquery table names
            to duckdb table names
        duckdb_path (str): The path to the duckdb database
        max_results_per_query (int): The maximum number of results to return.
            Set to 0 to return all results

    Returns:
        None
    """
    logger.info("Copying tables from BigQuery to DuckDB")
    bqclient = bigquery.Client(project=PROJECT_ID)
    conn = duckdb.connect(duckdb_path)

    created_schemas = set()

    for bq_table, duckdb_table in table_mapping.items():
        table = bigquery.TableReference.from_string(bq_table)

        if isinstance(duckdb_table, TableMappingDestination):
            duckdb_table_name = duckdb_table.destination

            if table_exists_in_duckdb(conn, duckdb_table_name):
                logger.info(f"{duckdb_table_name} already exists, skipping")
                continue
            table_as_arrow = bq_read_with_options(bq_table, duckdb_table, PROJECT_ID)
        else:
            duckdb_table_name = duckdb_table
            logger.info(f"checking if {duckdb_table_name} already exists")
            if table_exists_in_duckdb(conn, duckdb_table_name):
                logger.info(f"{duckdb_table_name} already exists, skipping")
                continue

            logger.info(f"{bq_table}: copying to {duckdb_table}")

            if max_results_per_query:
                logger.info(f"Limiting results to {max_results_per_query}")
                rows = bqclient.list_rows(table)
                # COLLECT SOME NUMBER OF ROWS
                total_rows = 0
                to_concat: t.List[pa.RecordBatch] = []
                client = bigquery_storage_v1.BigQueryReadClient()
                for record_batch in rows.to_arrow_iterable(bqstorage_client=client):
                    to_concat.append(record_batch)
                    total_rows += record_batch.num_rows
                    if total_rows >= max_results_per_query:
                        break
                if total_rows == 0:
                    logger.info(
                        "No rows found when limiting rows, resorting to full copy to get schema"
                    )
                    rows = bqclient.list_rows(table)
                    table_as_arrow = rows.to_arrow(create_bqstorage_client=True)
                else:
                    table_as_arrow = pa.Table.from_batches(to_concat)
            else:
                rows = bqclient.list_rows(table)
                table_as_arrow = rows.to_arrow(
                    create_bqstorage_client=True
                )  # noqa: F841

        # Load the schema from bigquery
        table_schema = bqclient.get_table(table).schema

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
            conn.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")
            created_schemas.add(schema)

        if is_simple_copy:
            conn.execute(
                f"CREATE TABLE IF NOT EXISTS {duckdb_table_name} AS SELECT * FROM table_as_arrow"
            )
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
            conn.execute(create_query.sql(dialect="duckdb"))

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
            conn.execute(insert_query.sql(dialect="duckdb"))

    logger.info("...done")


def initialize_local_duckdb(
    path: str, max_results_per_query: int = 0, max_days: int = 7
):
    # Use the oso_dagster assets as the source of truth for configured defi
    # llama protocols for now
    defi_llama_tables = {
        f"opensource-observer.defillama_tvl.{defi_llama_slug_to_name(slug)}": f"sources_defillama_tvl.{defi_llama_slug_to_name(slug)}"
        for slug in DEFI_LLAMA_PROTOCOLS
    }

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    # Get the last 30 days of data
    start_date = today - timedelta(days=max_days)
    end_date = today

    table_mapping: t.Dict[str, str | TableMappingDestination] = {
        "opensource-observer.oso_playground.int_deployers": "sources.int_deployers",
        "opensource-observer.oso_playground.int_deployers_by_project": "sources.int_deployers_by_project",
        "opensource-observer.oso_playground.int_events__blockchain": "sources.int_events__blockchain",
        "opensource-observer.oso_playground.int_events__github": "sources.int_events__github",
        "opensource-observer.oso_playground.int_events__dependencies": "sources.int_events__dependencies",
        "opensource-observer.oso_playground.int_events__open_collective": "sources.int_events__open_collective",
        "opensource-observer.oso_playground.int_first_time_addresses": "sources.int_first_time_addresses",
        "opensource-observer.oso_playground.int_factories": "sources.int_factories",
        "opensource-observer.oso_playground.int_proxies": "sources.int_proxies",
        "opensource-observer.oso_playground.int_superchain_potential_bots": "sources.int_superchain_potential_bots",
        "opensource-observer.oso_playground.stg_deps_dev__packages": "sources.stg_deps_dev__packages",
        "opensource-observer.oso_playground.stg_farcaster__addresses": "sources.stg_farcaster__addresses",
        "opensource-observer.oso_playground.stg_farcaster__profiles": "sources.stg_farcaster__profiles",
        "opensource-observer.oso_playground.stg_lens__owners": "sources.stg_lens__owners",
        "opensource-observer.oso_playground.stg_lens__profiles": "sources.stg_lens__profiles",
        "opensource-observer.oso_playground.stg_ossd__current_collections": "sources.stg_ossd__current_collections",
        "opensource-observer.oso_playground.stg_ossd__current_projects": "sources.stg_ossd__current_projects",
        "opensource-observer.oso_playground.stg_ossd__current_repositories": "sources.stg_ossd__current_repositories",
        "opensource-observer.oso_playground.timeseries_events_aux_issues_by_artifact_v0": "sources.timeseries_events_aux_issues_by_artifact_v0",
        "opensource-observer.ossd.sbom": "sources_ossd.sbom",
        # Only grab some data from frax for local testing
        "opensource-observer.optimism_superchain_raw_onchain_data.blocks": TableMappingDestination(
            row_restriction=f"dt >= '{start_date.strftime("%Y-%m-%d")}' AND dt < '{end_date.strftime("%Y-%m-%d")}' AND chain_id = 252",
            destination="sources_optimism_superchain_raw_onchain_data.blocks",
        ),
        "opensource-observer.optimism_superchain_raw_onchain_data.transactions": TableMappingDestination(
            row_restriction=f"dt >= '{start_date.strftime("%Y-%m-%d")}' AND dt < '{end_date.strftime("%Y-%m-%d")}' AND chain_id = 252",
            destination="sources_optimism_superchain_raw_onchain_data.transactions",
        ),
        "opensource-observer.optimism_superchain_raw_onchain_data.traces": TableMappingDestination(
            row_restriction=f"dt >= '{start_date.strftime("%Y-%m-%d")}' AND dt < '{end_date.strftime("%Y-%m-%d")}' AND chain_id = 252",
            destination="sources_optimism_superchain_raw_onchain_data.traces",
        ),
    }

    table_mapping.update(defi_llama_tables)

    bq_to_duckdb(
        table_mapping,
        path,
        max_results_per_query=max_results_per_query,
    )


def initialize_local_postgres():
    pass


def reset_local_duckdb(path: str):
    conn = duckdb.connect(path)
    response = conn.query("SHOW ALL TABLES")
    schema_names = response.df()["schema"].unique().tolist()
    for schema_name in schema_names:
        if not schema_name.startswith(DUCKDB_SOURCES_SCHEMA_PREFIX):
            logger.info(f"dropping schema {schema_name}")
            conn.query(f"DROP schema {schema_name} cascade")
