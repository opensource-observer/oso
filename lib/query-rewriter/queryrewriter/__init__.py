# ruff: noqa: F401
from .dialect import extend_sqlglot
from .rewrite import rewrite_query

extension_run = False

if not extension_run:
    from sqlglot import parse_one
    from sqlglot.errors import ParseError

    try:
        mf = parse_one("@fake_macro('what')")
        if mf.__class__.__name__ != "MacroFunc":
            extend_sqlglot()
    except ParseError:
        extend_sqlglot()
    extension_run = True
