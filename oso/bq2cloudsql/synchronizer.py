import uuid
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import textwrap
from typing import List, Dict, Union, Tuple

import pendulum
from sqlalchemy import (MetaData, Table, 
                        Column, String, 
                        Double, BigInteger, 
                        DateTime, Date, 
                        Boolean, LargeBinary, 
                        Numeric, Time,
                        select, text
                        )
from sqlalchemy.dialects.postgresql import insert
from google.cloud import bigquery, storage
from google.cloud.bigquery import TableReference, ExtractJobConfig, Table as BQTable
from googleapiclient.discovery import build

from .cloudsql import CloudSQLClient


class UnsupportedTableColumn(Exception):
    pass


class UnsupportedIncrementalSettings(Exception):
    pass


COLUMN_MAP = {
    'STRING': String,
    'FLOAT': Double,
    'FLOAT64': Double,
    'INTEGER': BigInteger,
    'INT64': BigInteger,
    'TIMESTAMP': lambda: DateTime(timezone=True),
    'DATETIME': lambda: DateTime(timezone=True),
    'DATE': Date,
    'BYTES': LargeBinary,
    'BOOL': Boolean,
    'NUMERIC': lambda: Numeric(38,9),
    'DECIMAL': lambda: Numeric(38,9),
    'BIGNUMERIC': lambda: Numeric(77, 38),
    'BIGDECIMAL': lambda: Numeric(77, 38),
    'TIME': Time,
}

PARTITION_TYPE_STRING_PARSER = {
    'HOUR': lambda a: pendulum.from_format(a, 'YYYYMMDDHH'),
    'DAY': lambda a: pendulum.from_format(a, 'YYYYMMDD'),
    'MONTH': lambda a: pendulum.from_format(a, 'YYYYMM'),
    'YEAR': lambda a: pendulum.from_format(a, 'YYYY'),
}

class TableSyncMode(Enum):
    INCREMENTAL_BY_PARTITION = 1
    INCREMENTAL_BY_QUERY = 2
    OVERWRITE = 3

@dataclass
class TableSyncConfig:
    mode: TableSyncMode
    source_table: str
    destination_table: str


class BigQueryCloudSQLSynchronizer(object):
    def __init__(self, 
                 bq: bigquery.Client, 
                 storage_client: storage.Client,
                 cloudsql: CloudSQLClient,
                 project: str, 
                 dataset_id: str, 
                 table_sync_configs: List[TableSyncConfig], 
                 bucket_name: str, 
                 path_prefix: str = 'bq2cloudsql',
                 sync_state_table_name: str = 'bq2cloudsql_state'):
        self._bq = bq
        self._storage = storage_client
        self._cloudsql = cloudsql
        self._project = project
        self._dataset_id = dataset_id
        self._configs = table_sync_configs
        self._bucket_name = bucket_name
        self._path_prefix = path_prefix
        self._now = pendulum.now(tz='UTC')
        self._sync_id = str(uuid.uuid4())
        self._metadata = MetaData()
        self._sync_state_table_name = sync_state_table_name
        self._sync_state_table = Table(
            self._sync_state_table_name, 
            self._metadata,
            Column('table_name', String(), primary_key=True, nullable=False),
            Column('last_sync_at', DateTime(), nullable=False),
            Column('is_incremental', Boolean(), nullable=False),
            Column('last_partition_date', DateTime(), nullable=True),
        )

    def initialize(self):
        self._metadata.create_all(self._cloudsql.sql_conn)

    @property
    def dataset_ref(self):
        return bigquery.DatasetReference(self._project, self._dataset_id)

    def sync(self, full_refresh=False):
        self.initialize()

        for config in self._configs:
            source_table_id = config.source_table
            dest_table_name = config.destination_table

            destination_prefix = "%s/%s/%s" % (
                self._path_prefix, 
                self._sync_id,
                source_table_id, 
            )
            table_ref = self.dataset_ref.table(source_table_id)
            table = self._bq.get_table(table_ref)

            queue = ['']
            latest_partition_date: datetime | None = None

            # Validate incremental settings and get the suffix for the table extraction
            if config.mode.name == 'INCREMENTAL_BY_PARTITION':
                if not table.time_partitioning:
                    print('Skipping table %s. Only time partitioning is supported for INCREMENTAL mode' % source_table_id)
                    continue
                else:
                    partitioning_type = table.time_partitioning.type_
                    queue, latest_partition_date = self.load_partition_queue(config.source_table, partitioning_type, full_refresh=full_refresh)

            if len(queue) == 0:
                print('skipping %s. nothing to copy', config.source_table)
                continue

            # Create a temporary table that we will use to write
            temp_dest = '%s_%s' % (dest_table_name, self._sync_id.replace('-', '_'))
            if len(temp_dest) > 63:
                temp_dest = temp_dest[0:63].rstrip('_')
            try:
                # Also ensure that the expected destination exists. Even if we
                # will delete this keeps the `OVERWRITE` mode logic simple
                self.ensure_table_on_cloudsql(config.destination_table, table)
                self.ensure_table_on_cloudsql(temp_dest, table)
            except UnsupportedTableColumn as e:
                print('Skipping table %s. It has unsupported columns %s' % (source_table_id, e))
                continue

            for partition in queue:
                self.extract_bq_table_to_gcs(destination_prefix, config.source_table, partition)

            # Import into the table on CloudSQL
            # List all of the files (in order)
            for csv in self.list_csvs(destination_prefix):
                uri = "gs://%s/%s" % (self._bucket_name, csv.name)
                self._cloudsql.import_csv(uri, temp_dest)

            # Delete the gcs files
            self._storage.bucket(self._bucket_name).delete_blobs(blobs=list(self.list_csvs(destination_prefix)))

            # Commit the table
            self.commit_table(temp_dest, config, latest_partition_date)

    def extract_bq_table_to_gcs(self, destination_prefix: str, source_table_id: str, partition_decorator: str = ''):
        table_id = source_table_id
        if partition_decorator != '':
            table_id = '%s$%s' % (source_table_id, partition_decorator)
            destination_prefix = "%s/%s" % (destination_prefix, partition_decorator)
        table_ref = self.dataset_ref.table(table_id)
            
        destination_base_uri = "gs://%s/%s" % (self._bucket_name, destination_prefix)

        destination_uri = "%s/export-*.csv" % destination_base_uri 

        extract_job = self._bq.extract_table(
            table_ref, 
            destination_uri,
            location="US",
            job_config=ExtractJobConfig(print_header=False),
        )
        extract_job.result()
            
        print(
            "Exported {}:{}.{} to {}".format(self._project, self._dataset_id, table_id, destination_uri)
        )

    def ensure_table_on_cloudsql(self, table_name: str, table: BQTable):
        columns: List[Column] = []

        for field in table.schema:
            field_type = field.field_type
            if field_type in ['RECORD', 'STRUCT']:
                raise UnsupportedTableColumn(
                    'Field "%s" has unsupported type "%s"' % (field.name, field_type)
                )
            column_type = COLUMN_MAP[field_type]()
            columns.append(Column(field.name, column_type))
        
        self._cloudsql.ensure_table(table_name, columns)

    def commit_table(self, temp_dest_table: str, config: TableSyncConfig, last_partition_date: pendulum.DateTime | None):
        getattr(self, 'commit_table_for_%s' % config.mode.name.lower())(temp_dest_table, config, last_partition_date)

    def commit_table_for_overwrite(self, temp_dest_table: str, config: TableSyncConfig, last_partition_date: pendulum.DateTime | None):
        # Creates a transaction to rename the new table to the old table.
        # Currently if there are schema changes those changes are simply forced
        with self._cloudsql.begin() as conn:
            update_data = dict(last_sync_at=pendulum.now('UTC'), is_incremental=False)
            insert_stmt = insert(self._sync_state_table).values(table_name=config.destination_table, **update_data)
            update_stmt = insert_stmt.on_conflict_do_update(
                index_elements=self._sync_state_table.primary_key.columns,
                #constraint=self._sync_state_table.c.table_name,
                set_=update_data,
            )
            result = conn.execute(update_stmt)

            conn.execute(text(f"DROP TABLE {config.destination_table}"))
            conn.execute(text(f"ALTER TABLE {temp_dest_table} RENAME TO {config.destination_table}"))

    def commit_table_for_incremental(self, temp_dest_table: str, config: TableSyncConfig, last_partition_date: pendulum.DateTime | None):
        # Creates a transaction to merge the new events into the old table. Does
        # not currently deduplicate. 
        with self._cloudsql.begin() as conn:
            update_data = dict(
                last_sync_at=pendulum.now('UTC'), 
                is_incremental=True, 
                last_partition_date=last_partition_date
            )
            insert_stmt = insert(self._sync_state_table).values(table_name=config.destination_table, **update_data)
            update_stmt = insert_stmt.on_conflict_do_update(
                index_elements=self._sync_state_table.primary_key.columns,
                #constraint=self._sync_state_table.c.table_name,
                set_=update_data,
            )
            result = conn.execute(update_stmt)

            conn.execute(text(textwrap.dedent(f"""
                INSERT INTO {config.destination_table} 
                SELECT * FROM {temp_dest_table}
            """)))

    def get_last_date_for_table(self, table_name: str) -> Union[None, pendulum.DateTime]:
        with self._cloudsql.conn() as conn:
            result = conn.execute(
                select(self._sync_state_table).where(self._sync_state_table.c.table_name == table_name)
            )
            
            rows = list(result.all())
            if len(rows) == 0:
                return None
            return pendulum.instance(result[0].last_partition_date)
        
    def load_partition_queue(self, table_name: str, partitioning_type: str, full_refresh: bool = False) -> Tuple[List[str], pendulum.DateTime | None]:
        # We limit to 1000 so we don't need to return too many. In general if
        # we're doing this incrementally and it's more than 1000 of whatever
        # time partition sections off we should likely just do a full refresh.
        last_date = self.get_last_date_for_table(table_name)

        query = textwrap.dedent(f"""
            SELECT partition_id
            FROM `{self._project}.{self._dataset_id}.INFORMATION_SCHEMA.PARTITIONS`
            WHERE table_name = '{table_name}'
            ORDER BY partition_id DESC
            LIMIT 1000
        """)

        query_job = self._bq.query(query)
        rows = query_job.result()

        if rows.total_rows == 0:
            return ([], None)
        
        parser = PARTITION_TYPE_STRING_PARSER[partitioning_type]

        # If there is no last date that means this is brand new and we should do a full refresh
        if not last_date:
            first_row = next(rows)
            latest_datetime = parser(first_row.partition_id)
            return ([''], latest_datetime)

        count = 0
        queue: List[str] = []
        latest_datetime = None
        for row in rows:
            dt = parser(row.partition_id)
            if count == 0:
                latest_datetime = dt
            if not last_date:
                queue.append('')
                break
            if dt == last_date:
                break
            queue.append(row.partition_id)
        return (queue, latest_datetime)
        

    def list_csvs(self, prefix: str):
        return self._storage.list_blobs(self._bucket_name, prefix=prefix)


        
