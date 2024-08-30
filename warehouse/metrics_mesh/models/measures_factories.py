# """
# MODEL (
#   name metrics.testing_metrics,
#   kind INCREMENTAL_BY_TIME_RANGE (
#     time_column bucket_day,
#     batch_size 1
#   ),
#   start '2024-08-01',
#   cron '@daily',
#   dialect 'clickhouse',
#   grain (bucket_day, event_source, to_artifact_id, metric),
#   -- For now it seems clickhouse _must_ have the columns and their types
#   -- explicitly set.
#   columns (
#     bucket_day Date,
#     event_source String,
#     to_artifact_id String,
#     from_artifact_id String,
#     amount Int64
#   )
# );

# select
#   bucket_day,
#   event_source,
#   to_artifact_id,
#   from_artifact_id,
#   METRIC(active_days) as amount
# from metrics.int_events_daily_to_artifact
# where event_type = 'COMMIT_CODE' and
#   bucket_day BETWEEN (@end_date - INTERVAL @VAR('activity_window') DAY) AND @end_date
# group by
#   from_artifact_id,
#   to_artifact_id,
#   event_source,
#   bucket_day
# """

# from sqlglot import exp, parse

# from sqlmesh.core.model import model, ModelKindName
# from sqlmesh.core.macros import MacroEvaluator
# from sqlmesh import ExecutionContext


# @model(
#     "metrics.testing_metrics",
#     is_sql=True,
#     kind={
#         "name": ModelKindName.INCREMENTAL_BY_TIME_RANGE,
#         "time_column": "bucket_day",
#         "batch_size": 1,
#         # "name": ModelKindName.CUSTOM,
#         # "materialization": "METRICS_INCREMENTAL",
#         # "materialization_properties": {
#         #     "time_column": "bucket_day",
#         #     "batch_size": 1,
#         # },
#     },
#     dialect="clickhouse",
#     columns={
#         "bucket_day": "Date",
#         "event_source": "String",
#         "to_artifact_id": "String",
#         "from_artifact_id": "String",
#         "active_days": "Int64",
#     },
# )
# def entrypoint(evaluator: MacroEvaluator, **kwargs) -> str | exp.Expression:
#     parsed = parse(
#         """
#     @DEF(boop, 'bop');
#     @DEF(whoa, coa);
#     SELECT bam as woo from beep.foo as bar
#     UNION ALL
#     SELECT koop as woo from beep.koop
#     UNION ALL
#     SELECT kap as woo from beep.kap
#     """
#     )
#     print(repr(parsed))
#     for ex in parsed:
#         if ex:
#             print(evaluator.transform(ex))
#     evaluator.transform(evaluator.parse_one("@DEF(boop, bom)"))
#     print(evaluator.transform(evaluator.parse_one("select @boop from test")))

#     evaluator.transform
#     evaluated = evaluator.transform(
#         evaluator.parse_one(
#             evaluator.template(
#                 """
#             select
#                 bucket_day,
#                 event_source,
#                 to_artifact_id,
#                 from_artifact_id,
#                 @test_var as test_var,
#                 COUNT(DISTINCT bucket_day) amount,
#             from metrics.int_events_daily_to_artifact
#             where event_type = 'COMMIT_CODE' and
#                 bucket_day BETWEEN (@end_date - INTERVAL @VAR('activity_window') DAY) AND @end_date
#             group by
#                 from_artifact_id,
#                 to_artifact_id,
#                 event_source,
#                 bucket_day
#             """,
#                 {"test_var": 1},
#             ),
#         )
#     )
#     if not evaluated:
#         return ""
#     if isinstance(evaluated, list):
#         return evaluated[0]
#     return evaluated
