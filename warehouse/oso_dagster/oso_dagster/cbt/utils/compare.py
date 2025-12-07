from typing import cast

import sqlglot as sql
from sqlglot import expressions as exp
from sqlglot.diff import Keep
from sqlglot.optimizer.normalize import normalize
from sqlglot.optimizer.qualify import qualify


def is_same_identifier(a: exp.Identifier | str, b: exp.Identifier | str):
    if isinstance(a, str):
        a = sql.to_identifier(a)
    a = cast(exp.Identifier, a)

    if isinstance(b, str):
        b = sql.to_identifier(b)
    b = cast(exp.Identifier, b)

    return qualify(a) == qualify(b)


def is_same_source_table(a: exp.Table, b: exp.Table):
    return (
        is_same_identifier(a.catalog, b.catalog)
        and is_same_identifier(a.this, b.this)
        and is_same_identifier(a.db, b.db)
    )


def is_same_sql(a: exp.Expression, b: exp.Expression):
    diff = sql.diff(
        normalize(qualify(sql.parse_one(a.sql()))),
        normalize(qualify(sql.parse_one(b.sql()))),
    )
    for section in diff:
        if not isinstance(section, Keep):
            return False
    return True
