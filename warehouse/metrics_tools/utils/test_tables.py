from unittest.mock import MagicMock

from metrics_tools.utils.tables import create_dependent_tables_map


def test_create_dependent_tables_map():
    mock = MagicMock(name="context")
    mock.table.return_value = "test_table"

    actual_tables_map = create_dependent_tables_map(mock, "select * from foo")
    expected_tables_map = {
        "foo": "test_table",
    }
    assert actual_tables_map == expected_tables_map
