import typing as t

from sqlglot import exp

TIME_AGGREGATION_TO_CRON = {
    "daily": "@daily",
    "monthly": "@monthly",
    "weekly": "@weekly",
    "quarterly": "@monthly",
    "biannually": "@monthly",
    "yearly": "@yearly",
}

TIME_AGGREGATION_TO_END = {
    "daily": "1 day ago",
    "monthly": "1 month ago",
    "weekly": "1 week ago",
    "quarterly": "3 months ago",
    "biannually": "6 months ago",
    "yearly": "1 year ago",
}

METRICS_COLUMNS_BY_ENTITY: t.Dict[str, t.Dict[str, exp.DataType]] = {
    "artifact": {
        "metrics_sample_date": exp.DataType.build("DATE", dialect="duckdb"),
        "event_source": exp.DataType.build("STRING", dialect="duckdb"),
        "to_artifact_id": exp.DataType.build("STRING", dialect="duckdb"),
        "from_artifact_id": exp.DataType.build("STRING", dialect="duckdb"),
        "metric": exp.DataType.build("STRING", dialect="duckdb"),
        "amount": exp.DataType.build("DOUBLE", dialect="duckdb"),
    },
    "project": {
        "metrics_sample_date": exp.DataType.build("DATE", dialect="duckdb"),
        "event_source": exp.DataType.build("STRING", dialect="duckdb"),
        "to_project_id": exp.DataType.build("STRING", dialect="duckdb"),
        "from_artifact_id": exp.DataType.build("STRING", dialect="duckdb"),
        "metric": exp.DataType.build("STRING", dialect="duckdb"),
        "amount": exp.DataType.build("DOUBLE", dialect="duckdb"),
    },
    "collection": {
        "metrics_sample_date": exp.DataType.build("DATE", dialect="duckdb"),
        "event_source": exp.DataType.build("STRING", dialect="duckdb"),
        "to_collection_id": exp.DataType.build("STRING", dialect="duckdb"),
        "from_artifact_id": exp.DataType.build("STRING", dialect="duckdb"),
        "metric": exp.DataType.build("STRING", dialect="duckdb"),
        "amount": exp.DataType.build("DOUBLE", dialect="duckdb"),
    },
}

METRIC_METADATA_COLUMNS: t.Dict[str, exp.DataType] = {
    "display_name": exp.DataType.build("STRING", dialect="duckdb"),
    "description": exp.DataType.build("STRING", dialect="duckdb"),
    "metric": exp.DataType.build("STRING", dialect="duckdb"),
    "sql_source_path": exp.DataType.build("STRING", dialect="duckdb"),
    "rendered_sql": exp.DataType.build("STRING[]", dialect="duckdb"),
}
