from sqlglot import exp

from sqlmesh.core.model import model
from sqlmesh.core.macros import MacroEvaluator


def model_factory(name: str):
    @model(
        f"sqlmesh_example.{name}",
        is_sql=True,
        kind="FULL",
    )
    def _model(evaluator: MacroEvaluator):
        # id,
        # item_id,
        # event_date,
        print(evaluator.columns_to_types("sqlmesh_example.seed_model"))
        return exp.select("id", "item_id", "event_date").from_(
            "sqlmesh_example.seed_model"
        )

    return _model


test1 = model_factory("test1")
test1 = model_factory("test2")
