import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


def create_table(
    client,
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
    result = client.command(command % params)
    return result


def drop_table(client, table_name: str):
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
    return client.command(f"DROP TABLE IF EXISTS {table_name}")


def rename_table(client, from_name: str, to_name: str):
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
    return client.command(f"RENAME TABLE {from_name} TO {to_name}")


def import_data(client, table_name: str, s3_uri: str, format: str = ""):
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

    Returns
    -------
    Any
        See https://clickhouse.com/docs/en/integrations/python#client-command-method
    """
    client.command("SET input_format_parquet_import_nested = 1;")
    client.command("SET parallel_distributed_insert_select = 1;")
    if not format:
        command = (
            "INSERT INTO %(table_name)s "
            "SELECT * "
            "FROM s3Cluster('default', '%(s3_uri)s')"
        )
    else:
        command = (
            "INSERT INTO %(table_name)s "
            "SELECT * "
            "FROM s3Cluster('default', '%(s3_uri)s', '%(format)s')"
        )
    params = {
        "table_name": table_name,
        "s3_uri": s3_uri,
        "format": format,
    }
    query = command % params

    logger.debug(f"Running query: {query}")
    result = client.command(command % params)
    return result
