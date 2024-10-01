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

Write the data from the parquet files into iceberg

```sql
INSERT OVERWRITE TABLE "metrics"."default"."timeseries_events_by_artifact_v0"
SELECT * FROM "metrics"."default"."timeseries_events_by_artifact_v0_source";
```
