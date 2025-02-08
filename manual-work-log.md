# Manual work

```sql
create table "source"."default"."artifacts_by_project_v1_source"(
	artifact_id VARCHAR,
	artifact_source_id VARCHAR,
	artifact_source VARCHAR,
	artifact_namespace VARCHAR,
	artifact_name VARCHAR,
	project_id VARCHAR,
	project_source VARCHAR,
	project_namespace VARCHAR,
	project_name VARCHAR
)
with (
	external_location = 'gs://oso-dataset-transfer-bucket/trino/20240930/artifacts_by_project_v1/',
	format = 'PARQUET'
);
```

```sql
create table "source"."default"."projects_by_collection_v1_source"(
	project_id VARCHAR,
	project_source VARCHAR,
	project_namespace VARCHAR,
	project_name VARCHAR,
	collection_id VARCHAR,
	collection_source VARCHAR,
	collection_namespace VARCHAR,
	collection_name VARCHAR
)
with (
	external_location = 'gs://oso-dataset-transfer-bucket/trino/20240930/projects_by_collection_v1/',
	format = 'PARQUET'
);
```

```sql
create table "source"."default"."timeseries_events_by_artifact_v0_source"(
	time TIMESTAMP,
	to_artifact_id VARCHAR,
	from_artifact_id VARCHAR,
	event_type VARCHAR,
	event_source_id VARCHAR,
	event_source VARCHAR,
	amount DOUBLE
)
with (
	external_location = 'gs://oso-dataset-transfer-bucket/trino/20240930/timeseries_events_by_artifact_v0/',
	format = 'PARQUET'
);
```

```sql
create table "metrics"."default"."timeseries_events_by_artifact_v0"(
	time TIMESTAMP,
	to_artifact_id VARCHAR,
	from_artifact_id VARCHAR,
	event_type VARCHAR,
	event_source_id VARCHAR,
	event_source VARCHAR,
	amount DOUBLE
)
with (partitioning = array['day(time)', 'event_type'])
```

```sql
create table "metrics"."default"."projects_by_collection_v1"(
	project_id VARCHAR,
	project_source VARCHAR,
	project_namespace VARCHAR,
	project_name VARCHAR,
	collection_id VARCHAR,
	collection_source VARCHAR,
	collection_namespace VARCHAR,
	collection_name VARCHAR
)
```

```sql
create table "metrics"."default"."artifacts_by_project_v1"(
	artifact_id VARCHAR,
	artifact_source_id VARCHAR,
	artifact_source VARCHAR,
	artifact_namespace VARCHAR,
	artifact_name VARCHAR,
	project_id VARCHAR,
	project_source VARCHAR,
	project_namespace VARCHAR,
	project_name VARCHAR
)
```

Write the data from the parquet files into iceberg

```sql
INSERT INTO "metrics"."default"."timeseries_events_by_artifact_v0"
SELECT * FROM "source"."default"."timeseries_events_by_artifact_v0_source";
```

```sql
INSERT INTO "metrics"."default"."projects_by_collection_v1"
SELECT * FROM "source"."default"."projects_by_collection_v1_source";
```

```sql
INSERT INTO "metrics"."default"."artifacts_by_project_v1"
SELECT * FROM "source"."default"."artifacts_by_project_v1_source";
```

## Metrics manual import into Clickhouse (Ray)

```sql

CREATE OR REPLACE TABLE contracts_v0_import
(
    deployment_date Date,
    contract_address String,
    contract_namespace String,
    originating_address String,
    factory_address String,
    root_deployer_address String,
    sort_weight Int
)
ENGINE = MergeTree()
ORDER BY deployment_date;

INSERT INTO contracts_v0_import
  SELECT *
  FROM s3Cluster('default', 'gs://oso-dataset-transfer-bucket/trino-export/2025/02/07/19/export_contracts_v0_tester/20250207_192340_07703_6f5mp_281dd1c6-8077-40c4-9ea5-04e8a07b8558');


CREATE OR REPLACE TABLE timeseries_metrics_to_artifact
(
    metrics_sample_date Date,
	event_source String,
	to_artifact_id String,
	from_artifact_id String,
	metric String,
	amount Float64
)
ENGINE = MergeTree()
ORDER BY metrics_sample_date;

INSERT INTO timeseries_metrics_to_artifact
	SELECT *
    FROM s3Cluster('default', 'gs://oso-dataset-transfer-bucket/metrics-testing/2024-10-24/exports/timeseries_metrics_to_artifact.parquet');

CREATE OR REPLACE TABLE timeseries_metrics_to_project
(
    metrics_sample_date Date,
	event_source String,
	to_project_id String,
	from_artifact_id String,
	metric String,
	amount Float64
)
ENGINE = MergeTree()
ORDER BY metrics_sample_date;

INSERT INTO timeseries_metrics_to_project
	SELECT *
    FROM s3Cluster('default', 'gs://oso-dataset-transfer-bucket/metrics-testing/2024-10-24/exports/timeseries_metrics_to_project.parquet');


CREATE OR REPLACE TABLE timeseries_metrics_to_collection
(
    metrics_sample_date Date,
	event_source String,
	to_collection_id String,
	from_artifact_id String,
	metric String,
	amount Float64
)
ENGINE = MergeTree()
ORDER BY metrics_sample_date;

INSERT INTO timeseries_metrics_to_collection
	SELECT *
    FROM s3Cluster('default', 'gs://oso-dataset-transfer-bucket/metrics-testing/2024-10-24/exports/timeseries_metrics_to_collection.parquet');

```

```sql
CREATE OR REPLACE TABLE metrics_v0
(
	metric_id String,
  	metric_source String,
  	metric_namespace String,
  	metric_name String,
  	display_name String,
  	description String,
  	raw_definition String,
  	definition_ref String,
  	aggregation_function String,
	INDEX idx_metric_id (metric_id) TYPE bloom_filter,
	INDEX idx_metric_name (metric_source, metric_namespace, metric_name) TYPE bloom_filter
)
ENGINE = MergeTree()
ORDER BY (metric_source, metric_namespace, metric_name);


INSERT INTO metrics_v0
WITH unioned_metric_names AS (
  SELECT DISTINCT metric, event_source
  FROM timeseries_metrics_to_artifact
  UNION ALL
  SELECT DISTINCT metric, event_source
  FROM timeseries_metrics_to_project
  UNION ALL
  SELECT DISTINCT metric, event_source
  FROM timeseries_metrics_to_collection
),
all_timeseries_metric_names AS (
  SELECT DISTINCT metric, event_source
  FROM unioned_metric_names
),
metrics_v0_no_casting AS (
  SELECT TO_BASE64(SHA256(CONCAT(event_source, 'OSO', 'oso', metric))) AS metric_id,
    'OSO' AS metric_source,
    'oso' AS metric_namespace,
    metric AS metric_name,
    metric AS display_name,
    metric AS description,
    NULL AS raw_definition,
    'TODO' AS definition_ref,
    'UNKNOWN' AS aggregation_function
  FROM all_timeseries_metric_names
)
select metric_id::String AS metric_id,
  metric_source::String AS metric_source,
  metric_namespace::String AS metric_namespace,
  metric_name::String AS metric_name,
  display_name::String AS display_name,
  description::Nullable(String),
  raw_definition::Nullable(String),
  definition_ref::Nullable(String),
  aggregation_function::Nullable(String)
FROM metrics_v0_no_casting
```

```sql
CREATE OR REPLACE TABLE timeseries_metrics_by_artifact_v0
(
	metric_id String,
  	artifact_id String,
  	sample_date Date,
  	amount Float64,
  	unit Nullable(String)
)
ENGINE = MergeTree()
ORDER BY (metric_id, artifact_id, sample_date);

INSERT INTO timeseries_metrics_by_artifact_v0
WITH all_timeseries_metrics_by_artifact AS (
  SELECT TO_BASE64(SHA256(CONCAT(event_source, 'OSO', 'oso', metric))) AS metric_id,
    to_artifact_id AS artifact_id,
    metrics_sample_date AS sample_date,
    amount AS amount,
    NULL AS unit
  FROM timeseries_metrics_to_artifact
)
SELECT metric_id::String,
  artifact_id::String,
  sample_date::Date,
  amount::Float64,
  unit::Nullable(String)
FROM all_timeseries_metrics_by_artifact
```
