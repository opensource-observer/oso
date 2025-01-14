---
title: Import from Google Cloud Storage (GCS)
sidebar_position: 5
---

We strongly prefer data partners that can provide
updated live datasets, over a static snapshot.
Datasets that use this method will require OSO sponsorship
for the storing the data, because we take on the costs
of converting it into a BigQuery dataset
and associated long-term storage costs.
If you believe your data storage qualifies to be sponsored
by OSO, please reach out to us on
[Discord](https://www.opensource.observer/discord).

If you prefer to handle the data storage yourself, check out the
[Connect via BigQuery guide](../guides/bq-data-transfer.md).

## Schedule periodic dumps to GCS

First, you can coordinate with the OSO engineering team directly on
[Discord](https://www.opensource.observer/discord)
to give your Google service account write permissions to
our GCS bucket.

With these access permissions, you should schedule a
cron job to regularly dump new time-partitioned data,
usually in daily or weekly jobs.

## Defining a Dagster Asset

Next, create a new asset file in
`warehouse/oso_dagster/assets/`.
This file should invoke the GCS asset factory.
For example, you can see this in action for
[Gitcoin passport scores](https://github.com/opensource-observer/oso/blob/main/warehouse/oso_dagster/assets/gitcoin.py):

```python
# warehouse/oso_dagster/assets/gitcoin.py
from ..factories import (
    interval_gcs_import_asset,
    SourceMode,
    TimeInterval,
    IntervalGCSAsset,
)

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
        interval=TimeInterval.Daily,
        mode=SourceMode.Overwrite,
        retention_days=10,
        format="PARQUET",
    ),
)
```

For the latest documentation on configuration parameters,
check out the comments in the
[GCS factory](https://github.com/opensource-observer/oso/blob/main/warehouse/oso_dagster/factories/gcs.py).

In order for our Dagster deployment to recognize this asset, you must ensure
that it is a python file in the directory `warehouse/oso_dagster/assets/`.

For more details on defining Dagster assets,
see the [Dagster tutorial](https://docs.dagster.io/tutorial).

### GCS examples in OSO

In the
[OSO monorepo](https://github.com/opensource-observer/oso),
you will find a few examples of using the GCS asset factory:

- [Superchain data](https://github.com/opensource-observer/oso/blob/main/warehouse/oso_dagster/assets/__init__.py)
- [Gitcoin Passport scores](https://github.com/opensource-observer/oso/blob/main/warehouse/oso_dagster/assets/gitcoin.py)
- [OpenRank reputations on Farcaster](https://github.com/opensource-observer/oso/blob/main/warehouse/oso_dagster/assets/karma3.py)
