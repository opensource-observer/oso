# OSO Table Naming Conventions

OSO uses prefixes and suffixes to indicate the data pipeline stage:

## Staging Tables

**Pattern:** `oso.stg_[source]__[table]`

- Prefix: `stg_` indicates staging layer
- Contains raw data from external sources
- Double underscore separates source from table name

**Examples:**

- `oso.stg_github__events` - Raw GitHub events
- `oso.stg_github__repos` - Raw GitHub repositories
- `oso.stg_ossd__projects` - Raw OSS Directory projects
- `oso.stg_defillama__protocols` - Raw DefiLlama protocol data

## Intermediate Tables

**Pattern:** `oso.int_[model_name]`

- Prefix: `int_` indicates intermediate/transformation layer
- Contains cleaned, transformed, or aggregated data
- Bridge between raw staging data and final marts

**Examples:**

- `oso.int_events_daily__github` - Daily aggregated GitHub events
- `oso.int_artifacts` - Cleaned and deduplicated artifacts

## Mart Tables

**Pattern:** `oso.[model_name]_v0` or `oso.[model_name]_v1`

- Suffix: `_v0` or `_v1` indicates mart model version
- Contains final, production-ready analytics tables
- Versioned for breaking changes (v0 → v1)

**Examples:**

- `oso.projects_v1` - Project metadata (current version)
- `oso.artifacts_by_project_v1` - Repos and packages by project
- `oso.timeseries_metrics_by_project_v0` - Time-series metrics
- `oso.metrics_v0` - Metric definitions

## Pipeline Flow

```
oso.stg_github__events (staging - raw data)
       ↓
oso.int_events_daily__github (intermediate - transformed)
       ↓
oso.timeseries_metrics_by_project_v0 (mart - final metrics)
```

## Quick Reference

| Stage        | Prefix/Suffix | Layer       | Example                                |
| ------------ | ------------- | ----------- | -------------------------------------- |
| Staging      | `stg_`        | Raw data    | `oso.stg_github__events`               |
| Intermediate | `int_`        | Transformed | `oso.int_events_daily__github`         |
| Mart         | `_v0`, `_v1`  | Final       | `oso.timeseries_metrics_by_project_v0` |
