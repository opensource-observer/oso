from typing import Dict, List, Optional

import duckdb
import pandas


class DuckDbFixture:
    """Provides an easy interface to creating a duckdb test fixture"""

    @classmethod
    def setup(cls, tables: Optional[Dict[str, List[List]]] = None):
        tables = tables or dict()
        db = duckdb.connect()
        fixture = cls(db)
        fixture.set_timezone()
        fixture.add_tables(tables)
        fixture.set_memory_limit("2MB")
        return fixture

    def __init__(self, db: duckdb.DuckDBPyConnection):
        self._db = db

    def teardown(self):
        self._db.close()

    def add_tables(self, tables: Dict[str, List]):
        for table_name, table in tables.items():
            columns = table[0]
            rows = table[1:]
            df = pandas.DataFrame(rows, columns=columns)  # noqa: F841
            self._db.sql(
                f"""
            CREATE TABLE {table_name} AS SELECT * FROM df
            """
            )

    def set_memory_limit(self, limit: str):
        self._db.sql(f"SET memory_limit = '{limit}';")

    def set_timezone(self):
        self._db.sql("SET TimeZone = 'UTC';")

    @property
    def db(self):
        return self._db
