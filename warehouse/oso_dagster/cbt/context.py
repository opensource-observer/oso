import logging
from collections import OrderedDict
from typing import Callable, List, Optional, Sequence, Tuple, TypeVar, cast

import sqlglot as sql
from sqlglot import expressions as exp

logger = logging.getLogger(__name__)


T = TypeVar("T")
ColumnList = List[Tuple[str, str]]


class Connector[T]:
    dialect: str

    def get_table_columns(self, table: exp.Table) -> ColumnList:
        raise NotImplementedError()

    def execute_expression(self, exp: exp.Expression) -> T:
        raise NotImplementedError()


type ContextQuery[T] = Callable[["DataContext[T]"], exp.Expression]
type Transformation[T] = Callable[[ContextQuery[T]], ContextQuery[T]]


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

    def get_table_columns(self, table: exp.Table) -> ColumnList:
        return self._connector.get_table_columns(table)

    def get_table_columns_from_str(self, table_str: str):
        table_expr = sql.to_table(
            table_str,
            dialect=self._connector.dialect,
        )
        return self.get_table_columns(table_expr)

    def transform_query(
        self,
        query: ContextQuery[T] | str | exp.Expression,
        transformations: Optional[Sequence[Transformation]] = None,
        dialect: str = "bigquery",
    ):
        transformations = transformations or []
        if isinstance(query, str):
            query = cast(str, query)
            query = context_query_from_str(query, dialect=dialect)
        elif isinstance(query, exp.Expression):
            query = context_query_from_expr(query)

        for transformation in transformations:
            query = cast(ContextQuery[T], query)
            query = transformation(query)
        query = cast(ContextQuery[T], query)
        return query(self)

    def execute_query(
        self,
        query: ContextQuery[T] | str | exp.Expression,
        transformations: Optional[Sequence[Transformation]] = None,
        dialect: str = "bigquery",
    ) -> T:
        exp = self.transform_query(query, transformations, dialect=dialect)
        logger.debug(f"Executing query: {exp.sql()}")
        return self._connector.execute_expression(exp)

    # def examine_query(self, query: ContextQuery):
    #     result = executor.execute(exp, self.schema)
    #     result.columns


def context_query_from_str[T](s: str, dialect: str) -> ContextQuery[T]:
    def _context(_ctx: DataContext[T]):
        return sql.parse_one(s, dialect=dialect)

    return _context


def context_query_from_expr[T](e: exp.Expression) -> ContextQuery[T]:
    def _context(_ctx: DataContext[T]):
        return e

    return _context


def wrap_basic_transform[
    T
](transform: Callable[[exp.Expression], exp.Expression]) -> Transformation[T]:
    def _transform(query: ContextQuery[T]) -> ContextQuery[T]:
        def _cq(ctx: DataContext[T]):
            expression = query(ctx)
            return expression.transform(transform)

        return _cq

    return _transform
