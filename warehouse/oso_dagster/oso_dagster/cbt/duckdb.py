from duckdb import DuckDBPyConnection, DuckDBPyRelation
from sqlglot import expressions as exp

from .context import ColumnList, Connector


class DuckDbConnector(Connector[DuckDBPyRelation]):
    dialect = "duckdb"

    def __init__(self, db: DuckDBPyConnection):
        self._db = db

    def get_table_columns(self, table: exp.Table) -> ColumnList:
        response = self._db.sql(f"DESCRIBE {table.name}")
        column_list: ColumnList = []
        for row in response.fetchall():
            column_name = row[0]
            column_type = row[1]
            column_list.append((column_name, column_type))
        return column_list

    def execute_expression(self, exp: exp.Expression) -> DuckDBPyRelation:
        query = exp.sql(self.dialect)
        return self._db.sql(query)
