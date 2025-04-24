import logging
from typing import Dict, List, Optional, Tuple

from clickhouse_connect.driver.client import Client

logger = logging.getLogger(__name__)


def create_table(
    client: Client,
    table_name: str,
    columns: List[Tuple[str, str]],
    index: Optional[Dict[str, List[str]]] = None,
    order_by: Optional[List[str]] = None,
    if_not_exists: bool = True,
):
    """
    Creates a Clickhouse table

    Parameters
    ----------
    client
        Clickhouse client
    table_name: str
        Table name
    columns: List[Tuple[str, str]]
        List of (name, type) pairs
        See https://clickhouse.com/docs/en/sql-reference/data-types
        e.g. [("id", "String"), ("name", "String")]
    index: Optional[Dict[str, List[str]]]
        Indices to create
        e.g. {"index_name": ["column1", "column2"]}
    order_by: Optional[List[str]]
        List of column names to order by
    if_not_exists: bool
        Create IF NOT EXISTS

    Returns
    -------
    Any
        See https://clickhouse.com/docs/en/integrations/python#client-command-method
    """
    # Python parameters don't work for this use case
    # https://clickhouse.com/docs/en/integrations/python#parameters-argument
    # Server-side parameters only work for SELECT
    # Client-side parameters don't work for table/column idontifiers
    command = (
        "CREATE TABLE %(if_not_exists)s %(table_name)s "
        "(%(columns)s, %(indices)s) "
        "ENGINE = MergeTree() "
        "ORDER BY (%(order_by)s) "
    )
    params = {
        "table_name": table_name,
        "if_not_exists": "IF NOT EXISTS" if if_not_exists else "",
        "columns": ", ".join([f"`{name}` {type}" for name, type in columns]),
        "indices": (
            ", ".join(
                [
                    f"INDEX `{name}` ({', '.join(columns)}) TYPE bloom_filter"
                    for name, columns in index.items()
                ]
            )
            if index
            else ""
        ),
        "order_by": ", ".join(order_by) if order_by else "",
    }

    # return command % params
    return execute_command(client, command % params)


def drop_table(client: Client, table_name: str):
    """
    Drops a Clickhouse table

    Parameters
    ----------
    client
        Clickhouse client
    table_name: str
        Table name

    Returns
    -------
    Any
        See https://clickhouse.com/docs/en/integrations/python#client-command-method
    """
    return execute_command(client, f"DROP TABLE IF EXISTS {table_name}")


def rename_table(client: Client, from_name: str, to_name: str):
    """
    Renames a Clickhouse table

    Parameters
    ----------
    client
        Clickhouse client
    from_name: str
        Original table name
    to_name: str
        New table name

    Returns
    -------
    Any
        See https://clickhouse.com/docs/en/integrations/python#client-command-method
    """
    return execute_command(client, f"RENAME TABLE {from_name} TO {to_name}")


def import_data(
    client: Client,
    table_name: str,
    s3_uri: str,
    format: str = "",
    access_key: str = "",
    secret_key: str = "",
):
    """
    Imports data into a Clickhouse table
    Clickhouse will automatically infer the data format and compression from the file extension
    See https://clickhouse.com/docs/en/sql-reference/table-functions/s3

    Parameters
    ----------
    client
        Clickhouse client
    table_name: str
        Table name
    s3_uri: str
        URI to S3 or GCS blob
        e.g. https://storage.googleapis.com/bucket_name/folder/*.parquet
    format: str
        Format of the data
        e.g. "Parquet"
    access_key: str
        S3 access key
    secret_key: str
        S3 secret key

    Returns
    -------
    Any
        See https://clickhouse.com/docs/en/integrations/python#client-command-method
    """
    execute_command(client, "SET input_format_parquet_import_nested = 1;")
    execute_command(client, "SET parallel_distributed_insert_select = 1;")
    command_options = ["default", s3_uri]
    if access_key and secret_key:
        command_options.extend([access_key, secret_key])
    if format:
        command_options.append(format)

    command_options_as_str = [f"'{option}'" for option in command_options]

    command = f"""
        INSERT INTO {table_name}
        SELECT * 
        FROM s3Cluster({', '.join(command_options_as_str)})
    """
    # query = command % params
    # just to be safe let's not log while we're passing in the access key
    # logger.debug(f"Running query: {query}")
    return execute_command(client, command)


def execute_command(client: Client, command: str):
    try:
        return client.command(command)
    except Exception as e:
        logger.error(f"Error executing command: {command}")
        raise Exception(f"Error executing command: {command}") from e
