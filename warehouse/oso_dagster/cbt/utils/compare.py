from sqlglot.optimizer.qualify import qualify
from sqlglot import expressions as exp


def is_same_identifier(a: exp.Identifier, b: exp.Identifier):
    return qualify(a) == qualify(b)


def is_same_source_table(a: exp.Table, b: exp.Table):
    return (
        is_same_identifier(a.catalog, b.catalog)
        and is_same_identifier(a.this, b.this)
        and is_same_identifier(a.db, b.db)
    )
