import time
import pprint

import pg8000.native
import sqlalchemy
from sqlalchemy import Table, Column, MetaData
from google.cloud.sql.connector import Connector
from googleapiclient.discovery import build
from typing import Callable, List

connector = Connector()

pp = pprint.PrettyPrinter(indent=4)


def get_connection(project_id: str, region: str, instance_id: str, db_user: str, db_password: str, db_name: str) -> Callable[[], pg8000.native.Connection]:
    def _get_conn():
        return connector.connect(
            '%s:%s:%s' % (project_id, region, instance_id),
            'pg8000',
            user=db_user,
            password=db_password,
            db=db_name,
        )
    return _get_conn    


class CloudSQLClient(object):
    @classmethod
    def connect(cls, project_id: str, region: str, instance_id: str, db_user: str, db_password: str, db_name: str):
        pool = sqlalchemy.create_engine(
            'postgresql+pg8000://', 
            creator=get_connection(project_id, region, instance_id, db_user, db_password, db_name)
        )

        return cls(project_id, region, instance_id, db_name, build('sqladmin', 'v1beta4'), pool)

    def __init__(self, project_id: str, region: str, instance_id: str, db_name: str, client, sql_conn: sqlalchemy.Engine):
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
        
    def import_csv(self, csv_uri: str, table: str, columns: None | List[str] = None):
        print("importing into %s" % table)
        csv_import_options = dict(
            table=table
        )
        if columns is not None:
            csv_import_options = columns
        
        body = dict(
            uri=csv_uri,
            database=self._db_name,
            kind='sql#importContext',
            fileType="CSV",
            importUser='postgres',
            csvImportOptions=csv_import_options,
        )
        request = self._client.instances().import_(project=self._project_id, instance=self._instance_id, body=dict(importContext=body))
        response = request.execute()

        print('resp')
        pp.pprint(response)

        operation_id = response['name']

        while True:
            req = self._client.operations().get(project=self._project_id, operation=operation_id)
            r = req.execute()
            pp.pprint(r)
            if r['status'] not in ['PENDING', 'RUNNING']:
                if r['status'] != 'DONE':
                    raise Exception('An error occured importing')
                print('done importing')
                return
            time.sleep(1)

    def begin(self):
        return self.sql_conn.begin()
    
    def conn(self):
        return self.sql_conn.connect()