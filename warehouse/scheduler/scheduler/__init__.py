from sqlglot import expressions as exp
from sqlmesh.core.engine_adapter.base import EngineAdapter


def get_columns_for_table(
    engine_adapter: EngineAdapter, table_name: str
) -> dict[str, exp.DataType]:
    """Get the columns and their types for a given table.

    Args:
        engine_adapter: The engine adapter to use.
        table_name: The name of the table.

    Returns:
        A dictionary mapping column names to their data types.
    """
    return engine_adapter.columns(table_name)


# Load the latest sqlmesh models from the database
