---
title: BigQuery Data Transfer Service
sidebar_position: 2
sidebar_class_name: hidden
---

BigQuery comes with a built-in data transfer service
for replicating datasets between BigQuery projects/regions,
from Amazon S3, and from various Google services.
In this guide, we'll copy an existing BigQuery dataset into the
`opensource-observer` Google Cloud project at a regular schedule.

If you already maintain a public dataset in
the US multi-region, you should simply make a dbt source
as shown in [this guide](../contribute-data/bigquery.md).

## Define the Dagster asset

Create a new asset file in
`warehouse/oso_dagster/assets/`.
This file should invoke the BigQuery Data Transfer asset factory.
For example, you can see this in action for
[Lens data](https://github.com/opensource-observer/oso/blob/main/warehouse/oso_dagster/assets/lens.py).
We make a copy of this data because the source dataset is not
in the US multi-region, which is required by our dbt pipeline.

```python
# warehouse/oso_dagster/assets/lens.py
from ..factories import (
    create_bq_dts_asset,
    BigQuerySourceConfig,
    BqDtsAssetConfig,
    SourceMode,
    TimeInterval,
)

lens_data = create_bq_dts_asset(
    BqDtsAssetConfig(
        name="lens",
        destination_project_id="opensource-observer",
        destination_dataset_name="lens_v2_polygon",
        source_config=BigQuerySourceConfig(
            source_project_id="lens-public-data",
            source_dataset_name="v2_polygon",
            service_account=None
        ),
        copy_interval=TimeInterval.Weekly,
        copy_mode=SourceMode.Overwrite,
    ),
)
```

For the latest documentation on configuration parameters,
check out the comments in the
[BigQuery Data Transfer factory](https://github.com/opensource-observer/oso/blob/main/warehouse/oso_dagster/factories/bq_dts.py).

For more details on defining Dagster assets,
see the [Dagster tutorial](https://docs.dagster.io/tutorial).

### BigQuery Data Transfer examples in OSO

In the
[OSO monorepo](https://github.com/opensource-observer/oso),
you will find a few examples of using the BigQuery Data Transfer asset factory:

- [Farcaster data](https://github.com/opensource-observer/oso/blob/main/warehouse/oso_dagster/assets/farcaster.py)
- [Lens data](https://github.com/opensource-observer/oso/blob/main/warehouse/oso_dagster/assets/lens.py)
