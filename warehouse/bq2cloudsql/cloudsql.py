import time
import pprint
import ssl

import pg8000.native
import sqlalchemy
from sqlalchemy import Table, Column, MetaData, text
from google.cloud.sql.connector import Connector
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from typing import Callable, List, Dict, Optional

connector = Connector()
pp = pprint.PrettyPrinter(indent=4)

def get_connection(
    project_id: str,
    region: str,
    instance_id: str,
    db_user: str,
    db_password: str,
    db_name: str,
) -> Callable[[], pg8000.native.Connection]:
    def _get_conn():
        return connector.connect(
            "%s:%s:%s" % (project_id, region, instance_id),
            "pg8000",
            user=db_user,
            password=db_password,
            db=db_name,
        )

    return _get_conn

def retry(
    callable: Callable,
    check_success: Callable[[Optional[Exception], bool], bool] = lambda e, r: r,
    retries: int = 10,
    wait_time: int = 2,
    give_up_after_retry: bool = False,
) -> Callable:
    """Wraps a function in retry logic

    Parameters
    ----------
    callable: Callable
        The function to call
    check_success: Callable[[Optional[Exception], bool], bool]
        Pass in 2 parameters
        - most recently caught exception
        - boolean of whether the callable completed
        Returns whether we need to try again
    retries: int
        Max number of times to retry
    wait_time: int
        Time to wait in between first and second try (in seconds)
        This is doubled after every failed attempt
    give_up_after_retry: bool
        After all retries, should we just let it slide?
        If this is False, we raise an exception

    Returns
    -------
    Callable
        a callable function that embodies retry logic
    """
    def call(*args, **kwargs):
        last_exception = None
        last_result = None
        last_run_finished = False
        for i in range(retries):
            try:
                # Allow check_success to bypass the initial run
                if check_success(last_exception, last_run_finished):
                    return last_result
                print(f"{'' if i < 1 else 're'}trying attempt {i+1}...")
                last_run_finished = False
                last_result = callable(*args, **kwargs)
                last_run_finished = True
            except Exception as e:
                last_exception = e
            # Exponential back-off
            time.sleep(wait_time * (i+1))
        if check_success(last_exception, last_run_finished):
            # Check the last run
            return last_result
        elif give_up_after_retry:
            print(f"Exhausted retries, giving up")
            return last_result
        elif last_exception is not None:
            # Raise last known exception
            raise last_exception
        else:
            raise Exception(f"Failed {retries} retry attempts")

    return call

def cloudsql_check_success(e: Optional[Exception], run_success: bool):
    """ Generic check success handler for using `retry()` with CloudSQL
    Parameters
    ----------
    e: Exception
        The most recent exception
    run_success: bool
        Whether the last run was successful

    Returns
    -------
    bool
        True if we are safe to return
        False if we need to try again
    """
    # HttpError and SSLEOFError are worth trying again
    if isinstance(e, HttpError):
        return False
    if isinstance(e, ssl.SSLEOFError):
        return False
    # All other exceptions, treat as fatal
    if e is not None:
        raise e 
    return run_success

class CloudSQLClient(object):
    @classmethod
    def connect(
        cls,
        project_id: str,
        region: str,
        instance_id: str,
        db_user: str,
        db_password: str,
        db_name: str,
    ):
        pool = sqlalchemy.create_engine(
            "postgresql+pg8000://",
            creator=get_connection(
                project_id, region, instance_id, db_user, db_password, db_name
            ),
        )

        return cls(
            project_id, region, instance_id, db_name, build("sqladmin", "v1beta4"), pool
        )

    def __init__(
        self,
        project_id: str,
        region: str,
        instance_id: str,
        db_name: str,
        client,
        sql_conn: sqlalchemy.Engine,
    ):
        self._project_id = project_id
        self._region = region
        self._instance_id = instance_id
        self._client = client
        self._sql_conn = sql_conn
        self._db_name = db_name

    @property
    def sql_conn(self):
        return self._sql_conn

    def ensure_table(self, table_name: str, columns: List[Column]):
        if sqlalchemy.inspect(self.sql_conn).has_table(table_name):
            # Do nothing if the table exists
            return

        # We aren't actually using the orm so this object can be ephemeral
        metadata = MetaData()

        Table(table_name, metadata, *columns)
        metadata.create_all(self.sql_conn)

    def build_index(self, table_name: str, index_definitions: Optional[Dict[str, List[str]]]):
        print(f"Building indices for {table_name}:")

        # Check that the table exists
        if not sqlalchemy.inspect(self.sql_conn).has_table(table_name):
            raise Exception(f"Failed to build indices for {table_name}: the table does not exist")
        elif index_definitions is None:
            print(f"No indices found for {table_name}")
            return

        def create_single_index(index_name: str, column_names: List[str]):
            with self.begin() as conn:
                sql_str = f"CREATE INDEX {index_name} ON {table_name}({','.join(column_names)})"
                print(sql_str)
                conn.execute(text(sql_str))

        for key in index_definitions:
            print(f"- creating Index({key})")
            def index_check_success(e: Optional[Exception], run_success: bool):
                # First check if the index already exists, this is truth
                with self.begin() as conn:
                    sql_str = f"SELECT * FROM pg_indexes WHERE tablename = '{table_name}' AND indexname = '{key}'"
                    print(f"Checking if index exists: {sql_str}")
                    index_results = conn.execute(text(sql_str))
                    index_list = [*index_results]
                    #print(index_list)
                    if len(index_list) > 0:
                        print(f"Index {key} already exists! Skipping...")
                        return True
                # We don't actually care whether there's an exception or success
                # If the index doesn't exist, try again
                print(f"Index {key} is missing...")
                return False
            retry(create_single_index, index_check_success, retries=3, give_up_after_retry=True)(key, index_definitions[key])

    def import_csv(self, csv_uri: str, table: str, columns: None | List[str] = None):
        print("importing into %s" % table)
        csv_import_options = dict(table=table)
        if columns is not None:
            csv_import_options = columns

        body = dict(
            uri=csv_uri,
            database=self._db_name,
            kind="sql#importContext",
            fileType="CSV",
            importUser="postgres",
            csvImportOptions=csv_import_options,
        )
        request = self._client.instances().import_(
            project=self._project_id,
            instance=self._instance_id,
            body=dict(importContext=body),
        )
        response = retry(request.execute, cloudsql_check_success)()

        print("resp")
        pp.pprint(response)

        operation_id = response["name"]

        while True:
            req = self._client.operations().get(
                project=self._project_id, operation=operation_id
            )
            r = retry(req.execute, cloudsql_check_success)()
            pp.pprint(r)
            if r["status"] not in ["PENDING", "RUNNING"]:
                if r["status"] != "DONE":
                    raise Exception("An error occurred importing")
                print("done importing")
                return
            time.sleep(1)

    def begin(self):
        return self.sql_conn.begin()

    def conn(self):
        return self.sql_conn.connect()
