# from sqlmesh import macro
# from sqlmesh.core.macros import MacroEvaluator
# from sqlmesh.core.dialect import parse_one
# from sqlglot import expressions as exp


# @macro()
# def rollup_bucket(evaluator: MacroEvaluator, timeExp: exp.Expression, rollup: str):
#     if evaluator.runtime_stage in ["loading", "creating"]:
#         return parse_one("STR_TO_DATE('1970-01-01', '%Y-%m-%d')")
#     if evaluator.engine_adapter.dialect == "duckdb":
#         rollup_to_interval = {
#             "daily": "DAY",
#             "weekly": "WEEK",
#             "monthly": "MONTH",
#         }
#         return exp.Anonymous(
#             this="TIME_BUCKET",
#             expressions=[
#                 exp.Interval(
#                     this=exp.Literal(this=1, is_string=False),
#                     unit=exp.Var(this=rollup_to_interval[rollup]),
#                 ),
#                 exp.Cast(
#                     this=timeExp,
#                     to=exp.DataType(this=exp.DataType.Type.DATE, nested=False),
#                 ),
#             ],
#         )
#     rollup_to_clickhouse_function = {
#         "daily": "toStartOfDay",
#         "weekly": "toStartOfWeek",
#         "monthly": "toStartOfMonth",
#     }
#     return exp.Anonymous(
#         this=rollup_to_clickhouse_function[rollup],
#         expressions=[
#             timeExp,
#         ],
#     )


# @macro()
# def weekly_bucket(evaluator: MacroEvaluator, timeExp: exp.Expression):
#     if evaluator.engine_adapter.dialect == "duckdb":
#         return exp.Anonymous(
#             this="TIME_BUCKET",
#             expressions=[
#                 exp.Interval(
#                     this=exp.Literal(this=1, is_string=True),
#                     unit=exp.Var(this="WEEK"),
#                 ),
#                 timeExp,
#             ],
#         )
#     return exp.Anonymous(
#         this="toStartOfWeek",
#         expressions=[
#             timeExp,
#         ],
#     )


# @macro()
# def monthly_bucket(evaluator: MacroEvaluator, timeExp: exp.Expression):
#     if evaluator.dialect == "duckdb":
#         return exp.Anonymous(
#             this="TIME_BUCKET",
#             expressions=[
#                 exp.Interval(
#                     this=exp.Literal(this=1, is_string=True),
#                     unit=exp.Var(this="MONTH"),
#                 ),
#                 timeExp,
#             ],
#         )
#     return exp.Anonymous(
#         this="toStartOfMonth",
#         expressions=[
#             timeExp,
#         ],
#     )
