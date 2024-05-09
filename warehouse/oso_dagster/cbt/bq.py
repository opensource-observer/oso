# Query tools for bigquery tables
from typing import List
from functools import cache
from dataclasses import dataclass

from google.cloud.bigquery import Client, Table, TableReference


class TableLoader:
    def __init__(self, bq: Client):
        self.bq = bq

    def __call__(self, table_ref: TableReference | Table | str):
        return BigQueryTableQueryHelper.load_by_table(self.bq, table_ref)


class BigQueryTableQueryHelper:
    @classmethod
    def load_by_table(cls, bq: Client, table_ref: TableReference | Table | str):
        if type(table_ref) == str:
            table_ref = TableReference.from_string(table_ref)
        helper = cls(bq, table_ref)
        return helper

    def __init__(self, bq: Client, table_ref: TableReference):
        self._bq = bq
        self._table_ref = table_ref
        self._column_list = None

    def select_columns(
        self, prefix: str = "", exclude: List[str] = None, include: List[str] = None
    ):
        columns = self.filtered_columns(exclude=exclude, include=include)
        ordered_columns = map(lambda c: c.column_name, columns)
        if prefix != "":
            ordered_columns = map(lambda a: f"`{prefix}`.`{a}`", ordered_columns)
        else:
            ordered_columns = map(lambda a: f"`{a}`", ordered_columns)

        return ", ".join(ordered_columns)

    @property
    def columns(self):
        if self._column_list is not None:
            return self._column_list

        column_list_query = f"""
        SELECT column_name, data_type
        FROM `{self._table_ref.project}`.`{self._table_ref.dataset_id}`.INFORMATION_SCHEMA.COLUMNS
        WHERE table_name = '{self.name}'
        """

        result = self._bq.query_and_wait(column_list_query)
        self._column_list = list(result)
        return self._column_list

    def filtered_columns(self, exclude: List[str] = None, include: List[str] = None):
        exclude = exclude or []
        include = include or []

        if include and exclude:
            raise Exception("can only have include or exclude")

        all_columns = set(map(lambda c: c.column_name, self.columns))
        if include:
            include_set = set(include)
            if include_set.intersection(all_columns) != include_set:
                raise Exception("include lists non-existent columns")
            return filter(lambda a: a.column_name in include_set, self.columns)
        if exclude:
            exclude_set = set(exclude)
            if exclude_set.intersection(all_columns) != exclude_set:
                raise Exception("exclude lists non-existent columns")
            return filter(lambda a: a.column_name not in exclude_set, self.columns)
        return self.columns

    @property
    def name(self):
        return self._table_ref.table_id

    @property
    def fqdn(self):
        return f"{self._table_ref.project}.{self._table_ref.dataset_id}.{self._table_ref.table_id}"

    def _load(self):
        # Lazily load the table columns
        if self._column_list is not None:
            return

        column_list_query = f"""
        SELECT column_name, data_type
        FROM `{self._table_ref.project}`.`{self._table_ref.dataset_id}`.INFORMATION_SCHEMA.COLUMNS
        WHERE table_name = '{self.name}'
        """

        result = self._bq.query_and_wait(column_list_query)
        self._column_list = list(result)

    def update_columns_with(
        self,
        self_prefix: str,
        other_prefix: str,
        exclude: List[str] = None,
        include: List[str] = None,
    ):
        columns = self.filtered_columns(exclude=exclude, include=include)
        ordered_columns = map(lambda c: c.column_name, columns)

        set_columns = map(
            lambda c: f"`{self_prefix}`.`{c}` = `{other_prefix}`.`{c}`", ordered_columns
        )
        return ", ".join(set_columns)
