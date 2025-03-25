from typing import cast

from sqlglot import expressions as exp

from .compare import is_same_source_table


def replace_source_tables(search: exp.Table, replace: exp.Table):
    def _transform(expression: exp.Expression):
        if type(expression) not in [exp.Table]:
            return expression
        expression = cast(exp.Table, expression)
        if not is_same_source_table(search, expression):
            return expression
        replacement = replace.copy()
        if expression.alias:
            replacement = replacement.as_(expression.alias, table=True)
        return replacement

    return _transform
