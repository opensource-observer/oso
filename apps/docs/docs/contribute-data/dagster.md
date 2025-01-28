---
title: Write a Custom Dagster Asset
sidebar_position: 6
---

Before writing a fully custom Dagster asset,
we recommend you first see if the previous guides on
[BigQuery datasets](./bigquery.md),
[database replication](./database.md),
[API crawling](./api-crawling/index.md)
may be a better fit.
This guide should only be used in the rare cases where you cannot
use the other methods.

## Write your Dagster asset

Dagster provides a great
[tutorial](https://docs.dagster.io/integrations/bigquery/using-bigquery-with-dagster)
on writing Dagster assets that write to BigQuery.

At a high-level, there are 2 possible pathways:

- [**Option 1**: Using the BigQuery resource](https://docs.dagster.io/integrations/bigquery/using-bigquery-with-dagster#option-1-using-the-bigquery-resource)  
  By using the BigQuery resource directly, you'll execute SQL queries directly on BigQuery
  to create and interact with tables. This is ideal for large datasets where you do not
  want the Dagster process to be in the critical path of dataflow.
  Rather, Dagster orchestrates jobs remotely out-of-band.

- [**Option 2**: BigQuery I/O Manager](https://docs.dagster.io/integrations/bigquery/using-bigquery-with-dagster#option-2-using-the-bigquery-io-manager)  
  This method offers significantly more control, by loading data into a DataFrame
  on the Dagster process for arbitrary computation.
  However because Dagster is now on the critical path computing on data,
  it can lead to performance issues, especially if the data does not
  easily fit in memory.

Assets should be added to `warehouse/oso_dagster/assets/`. All assets defined in
this package are automatically loaded into Dagster from the main branch of the
git repository.

For an example of a custom Dagster asset, check out the
[asset for oss-directory](https://github.com/opensource-observer/oso/blob/main/warehouse/oso_dagster/assets/ossd.py),
where we use the `oss-directory` Python package
to fetch data from the
[oss-directory repo](https://github.com/opensource-observer/oss-directory/)
and load it into BigQuery using the I/O manager approach.

## Creating an asset factory (optional)

If your asset represents a common pattern,
we encourage that you turn this into a factory.
For example, our
[tutorial on Google Cloud Storage-based assets](./gcs.md)
is an example of a factory pattern.

:::tip
We suggest creating a vanilla asset and see it work in production
before abstracting it out into a factory
:::

In order to create a factory, add it to the
`warehouse/oso_dagster/factories/` directory.
The factory needs to return a `AssetFactoryResponse`
that represents the different aspects of an asset,
including sensors, jobs, and checks.

```python
# warehouse/oso_dagster/factories/common.py
@dataclass
class AssetFactoryResponse:
    assets: List[AssetsDefinition]
    sensors: List[SensorDefinition] = field(default_factory=lambda: [])
    jobs: List[JobDefinition] = field(default_factory=lambda: [])
    checks: List[AssetChecksDefinition] = field(default_factory=lambda: [])
```

For example, below we share the method signature
of the GCS factory:

```python
# warehouse/oso_dagster/factories/gcs.py

## Factory configuration
@dataclass(kw_only=True)
class IntervalGCSAsset(BaseGCSAsset):
    interval: Interval
    mode: SourceMode
    retention_days: int

## Factory function
def interval_gcs_import_asset(config: IntervalGCSAsset):

    # Asset definition
    @asset(name=config.name, key_prefix=config.key_prefix, **config.asset_kwargs)
    def gcs_asset(
        context: AssetExecutionContext, bigquery: BigQueryResource, gcs: GCSResource
    ) -> MaterializeResult:
        # Load GCS files into BigQuery
        ...

    # Asset sensor definition
    @asset_sensor(
        asset_key=gcs_asset.key,
        name=f"{config.name}_clean_up_sensor",
        job=gcs_clean_up_job,
        default_status=DefaultSensorStatus.STOPPED,
    )
    def gcs_clean_up_sensor(
        context: SensorEvaluationContext, gcs: GCSResource, asset_event: EventLogEntry
    ):
        # Detect when we can cleanup old data files on GCS
        ...

    # Asset cleanup job
    @job(name=f"{config.name}_clean_up_job")
    def gcs_clean_up_job():
        # Delete old files on GCS
        ...

    # Return an instance
    return AssetFactoryResponse([gcs_asset], [gcs_clean_up_sensor], [gcs_clean_up_job])
```

Then you can instantiate the asset with the factory
in `warehouse/oso_dagster/assets/`.
For example, we get periodic Parquet file dumps
from Gitcoin Passport into the GCS bucket named
`oso-dataset-transfer-bucket`.
Using the GCS factory,
we load the data into the BigQuery table named
`gitcoin.passport_scores`.

```python
# warehouse/oso_dagster/assets/gitcoin.py
gitcoin_passport_scores = interval_gcs_import_asset(
    IntervalGCSAsset(
        key_prefix="gitcoin",
        name="passport_scores",
        project_id="opensource-observer",
        bucket_name="oso-dataset-transfer-bucket",
        path_base="passport",
        file_match=r"(?P<interval_timestamp>\d\d\d\d-\d\d-\d\d)/scores.parquet",
        destination_table="passport_scores",
        raw_dataset_name="oso_raw_sources",
        clean_dataset_name="gitcoin",
        interval=Interval.Daily,
        mode=SourceMode.Overwrite,
        retention_days=10,
        format="PARQUET",
    ),
)
```
