from functools import cache
from typing import Callable, TypeVar, List, Sequence, Tuple, Optional, cast
from collections import OrderedDict

import sqlglot as sql
from sqlglot import expressions as exp


T = TypeVar("T")
ColumnList = List[Tuple[str, str]]


class Connector[T]:
    dialect: str

    def get_table_columns(self, table: exp.Table) -> ColumnList:
        raise NotImplementedError()

    def execute_expression(self, exp: exp.Expression) -> T:
        raise NotImplementedError()


ContextQuery = Callable[["DataContext"], exp.Expression]
Transformation = Callable[[ContextQuery], ContextQuery]


class Columns:
    def __init__(self, column_list: ColumnList):
        self._column_list = column_list
        self._column_dict = OrderedDict(self._column_list)

    def as_dict(self) -> OrderedDict:
        return self._column_dict

    def __contains__(self, key):
        return key in self.as_dict()

    def __iter__(self):
        for col in self._column_list:
            yield col


class DataContext[T]:
    def __init__(self, connector: Connector[T]):
        self._connector = connector

    def get_table_columns(self, table: exp.Table) -> Columns:
        return self._connector.get_table_columns(table)

    def get_table_columns_from_str(self, table_str: str):
        table_expr = sql.to_table(
            table_str,
            dialect=self._connector.dialect,
        )
        return self.get_table_columns(table_expr)

    def transform_query(
        self,
        query: ContextQuery | str | exp.Expression,
        transformations: Optional[Sequence[Transformation]] = None,
    ):
        transformations = transformations or []
        if type(query) == str:
            query = context_query_from_str(query)
        elif isinstance(query, exp.Expression):
            query = context_query_from_expr(query)
        for transformation in transformations:
            query = transformation(query)
        query = cast(ContextQuery, query)
        return query(self)

    def execute_query(
        self,
        query: ContextQuery | str | exp.Expression,
        transformations: Optional[Sequence[Transformation]] = None,
    ) -> T:
        exp = self.transform_query(query, transformations)
        print(exp.sql())
        return self._connector.execute_expression(exp)

    # def examine_query(self, query: ContextQuery):
    #     result = executor.execute(exp, self.schema)
    #     result.columns


def context_query_from_str(s: str):
    def _context(_ctx: ContextQuery):
        return sql.parse_one(s)

    return _context


def context_query_from_expr(e: exp.Expression):
    def _context(_ctx: ContextQuery):
        return e

    return _context
