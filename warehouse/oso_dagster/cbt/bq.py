# Query tools for bigquery tables
from typing import List
from google.cloud.bigquery import Client, Table, TableReference


class TableLoader:
    def __init__(self, bq: Client):
        self.bq = bq

    def __call__(self, table_ref: TableReference | Table | str):
        return BigQueryTableQueryHelper.load_by_table(self.bq, table_ref)


class BigQueryTableQueryHelper:
    @classmethod
    def load_by_table(cls, bq: Client, table_ref: TableReference | Table | str):
        helper = cls(bq, bq.get_table(table_ref))
        helper._load()
        return helper

    def __init__(self, bq: Client, table: Table):
        self._bq = bq
        self._table = table
        self._column_list = []

    def sql_from(self):
        return f"{self._table.project}.{self._table.dataset_id}.{self._table.table_id}"

    def sql_columns(
        self, prefix: str = "", exclude: List[str] = None, include: List[str] = None
    ):
        exclude = exclude or []
        include = include or []

        if include and exclude:
            raise Exception("can only have include or exclude")

        all_columns = list(map(lambda c: c.column_name, self._column_list))
        columns_set = set(all_columns)
        if include:
            include_set = set(include)
            if include_set.intersection(all_columns) != include_set:
                raise Exception("include lists non-existent columns")
        if exclude:
            columns_set = columns_set - set(exclude)

        ordered_columns = filter(lambda a: a in columns_set, all_columns)
        if prefix != "":
            ordered_columns = map(lambda a: f"{prefix}.{a}", ordered_columns)

        return ", ".join(ordered_columns)

    @property
    def name(self):
        return self._table.table_id

    def _load(self):
        column_list_query = f"""
        SELECT column_name, data_type
        FROM `{self._table.project}`.`{self._table.dataset_id}`.INFORMATION_SCHEMA.COLUMNS
        WHERE table_name = '{self.name}'
        """

        result = self._bq.query_and_wait(column_list_query)
        self._column_list = list(result)
