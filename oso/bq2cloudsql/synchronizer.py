import pendulum
from sqlalchemy import Column, String, Double, BigInteger, DateTime, Date, Boolean, LargeBinary, Numeric, Time
from google.cloud import bigquery, storage
from google.cloud.bigquery import TableReference, ExtractJobConfig
from typing import List, Dict
from googleapiclient.discovery import build

from .cloudsql import CloudSQLClient


class UnsupportedTableColumn(Exception):
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


class BigQueryCloudSQLSynchronizer(object):
    def __init__(self, 
                 bq: bigquery.Client, 
                 storage_client: storage.Client,
                 cloudsql: CloudSQLClient,
                 project: str, 
                 dataset_id: str, 
                 table_ids: Dict[str, str], 
                 bucket_name: str, 
                 path_prefix: str = 'bq2cloudsql'):
        self._bq = bq
        self._storage = storage_client
        self._cloudsql = cloudsql
        self._project = project
        self._dataset_id = dataset_id
        self._table_ids = table_ids
        self._bucket_name = bucket_name
        self._path_prefix = path_prefix
        self._now = pendulum.now(tz='UTC')

    def sync(self):
        project = self._project
        dataset_id = self._dataset_id
        for source_table_id, dest_table_name in self._table_ids.items():
            destination_prefix = "%s/%s/%s" % (
                self._path_prefix, 
                source_table_id, 
                self._now.format('YYYY-MM-DD-HH-mm-ss'),
            )
            destination_base_uri = "gs://%s/%s" % (self._bucket_name, destination_prefix)
            destination_uri = "%s/export-*.csv" % destination_base_uri
            dataset_ref = bigquery.DatasetReference(project, dataset_id)
            table_ref = dataset_ref.table(source_table_id)
            
            # Ensure that the table exists on CloudSQL
            try:
                self.ensure_table_on_cloudsql(dest_table_name, table_ref)
            except UnsupportedTableColumn as e:
                print('Skipping table %s. It has unsupported columns %s' % (source_table_id, e))
                continue

            # Copy the table to gcs
            extract_job = self._bq.extract_table(
                table_ref,
                destination_uri,
                location="US",
                job_config=ExtractJobConfig(print_header=False),
            )  # API request
            extract_job.result()  # Waits for job to complete.

            print(
                "Exported {}:{}.{} to {}".format(project, dataset_id, source_table_id, destination_uri)
            )

            # Import into the table on CloudSQL

            # List all of the files (in order)
            for csv in self.list_csvs(destination_prefix):
                uri = "gs://%s/%s" % (self._bucket_name, csv.name)
                self._cloudsql.import_csv(uri, dest_table_name)

            # Delete the gcs files
            self._storage.bucket(self._bucket_name).delete_blobs(blobs=list(self.list_csvs(destination_prefix)))

    def ensure_table_on_cloudsql(self, table_name: str, table_ref: TableReference):
        table = self._bq.get_table(table_ref)

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

    def list_csvs(self, prefix: str):
        return self._storage.list_blobs(self._bucket_name, prefix=prefix)


        
