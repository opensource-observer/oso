"""

Attempt that works:

with projects as (
  select
    project_id,
    websites,
    social,
    github,
    npm,
    blockchain
  from bigquery.oso.stg_ossd__current_projects
)
select * from projects
cross join unnest(
cast(
		json_extract(
			json_query(
				json_format(websites), 
				'lax $[*].url' with array wrapper
			), '$'
		) as array<JSON>)
) as t(web);




"""

from sqlglot import expressions as exp
from sqlmesh import macro
from sqlmesh.core.macros import MacroEvaluator


@macro()
def json_extract_from_array(
    evaluator: MacroEvaluator,
    json_expression: exp.Expression,
    key: str,
):
    """Convert a unix epoch timestamp to a date or timestamp."""

    if evaluator.runtime_stage in ["loading"]:
        return exp.Array(this=[])

    if evaluator.engine_adapter.dialect == "duckdb":
        result = exp.JSONExtract(
            this=json_expression,
            expressions=exp.Literal(this=key, is_string=True),
        )
    elif evaluator.engine_adapter.dialect == "trino":
        result = exp.JSONExtract(
            this=exp.JSONExtract(
                this=json_expression,
                expression=exp.Literal(this=f"strict {key}", is_string=True),
                option=exp.Var(this="WITH UNCONDITIONAL ARRAY WRAPPER"),
                json_query=True,
            ),
            expression=exp.Literal(this="$", is_string=True),
        )
    else:
        raise NotImplementedError(
            f"from_unix_timestamp not implemented for {evaluator.engine_adapter.dialect}"
        )
    return exp.Cast(
        this=result,
        to=exp.DataType(
            this=exp.DataType.Type.ARRAY,
            expressions=[
                exp.DataType(
                    this=exp.DataType.Type.JSON,
                    nested=False,
                )
            ],
            nested=True,
        ),
    )
