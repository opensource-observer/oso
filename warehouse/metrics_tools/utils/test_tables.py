import typing as t
from unittest.mock import MagicMock

import pytest
from metrics_tools.utils.tables import create_dependent_tables_map


def test_create_dependent_tables_map():
    mock = MagicMock(name="context")
    mock.resolve_table.return_value = "test_table"

    actual_tables_map = create_dependent_tables_map(mock, "select * from foo")
    expected_tables_map = {
        "foo": "test_table",
    }
    assert actual_tables_map == expected_tables_map


@pytest.mark.parametrize(
    "input,expected",
    [
        ("select * from foo.bar", {"foo.bar": "test_table"}),
        ("select * from foo", {"foo": "test_table"}),
        (
            "select * from foo.bar, bar.foo",
            {"foo.bar": "test_table", "bar.foo": "test_table"},
        ),
        (
            """
            with foo as (
                select * from bar
            )
            select * from foo
            """,
            {"bar": "test_table"},
        ),
        (
            """
            with grandfoo as (
                select * from main.source
            )
            with foo as (
                select * from grandfoo
            )
            select * from foo
            """,
            {"main.source": "test_table"},
        ),
        (
            """
            select * from foo   
            union all
            select * from bar
            union all
            select * from baz
            """,
            {"foo": "test_table", "bar": "test_table", "baz": "test_table"},
        ),
        (
            """
            with foo as (
                select * from bar
            )
            select * from foo
            union all
            select * from baz
            """,
            {"bar": "test_table", "baz": "test_table"},
        ),
        (  # nested ctes, but I don't think any sql engine supports this
            """
            with foo as (
                with bar as (
                    select * from baz
                )
                select * from bar
            )
            select * from foo
            union all
            select * from baz
            """,
            {"baz": "test_table"},
        ),
        (
            """
            with foo as (
                select * from bar
            )
            select * from foo
            inner join baz on foo.id = baz.id
            """,
            {"bar": "test_table", "baz": "test_table"},
        ),
        (
            """
            select * from (
                select * from foo
            )
            """,
            {"foo": "test_table"},
        ),
        (
            """
            select * from (
                select * from foo
            )
            union all
            select * from (
                select * from bar
            )
            """,
            {"foo": "test_table", "bar": "test_table"},
        ),
        (
            """
            select * from foo
            inner join baz on foo.id = baz.id
            left join bar on foo.id = bar.id
            """,
            {"foo": "test_table", "baz": "test_table", "bar": "test_table"},
        ),
    ],
)
def test_create_dependent_tables_map_parameterized(
    input: str, expected: t.Dict[str, str]
):
    mock = MagicMock(name="context")
    mock.resolve_table.return_value = "test_table"

    actual_tables_map = create_dependent_tables_map(mock, input)
    assert actual_tables_map == expected
