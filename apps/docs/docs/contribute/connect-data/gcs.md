---
title: 🏗️ Connect via Google Cloud Storage (GCS)
sidebar_position: 4
---

import NextSteps from "./dagster-config.mdx"

Depending on the data, we may accept data dumps
into our Google Cloud Storage (GCS).
If you believe your data storage qualifies to be sponsored
by OSO, please reach out to us on
[Discord](https://www.opensource.observer/discord).

## Get write access

Coordinate with the OSO engineering team directly on
[Discord](https://www.opensource.observer/discord)
to give your Google service account write permissions to
our GCS bucket.

## Defining a Dagster Asset

:::warning
Coming soon... This section is a work in progress
and will be likely refactored soon.
:::

To see an example of this in action,
you can look into our Dagster asset for
[Gitcoin passport scores](https://github.com/opensource-observer/oso/blob/main/warehouse/oso_dagster/assets.py).

For more details on defining Dagster assets,
see the [Dagster tutorial](https://docs.dagster.io/tutorial).

## GCS import examples in OSO

- [Superchain data](https://github.com/opensource-observer/oso/blob/main/warehouse/oso_dagster/assets.py)
- [Gitcoin Passport scores](https://github.com/opensource-observer/oso/blob/main/warehouse/oso_dagster/assets.py)
- [OpenRank reputations on Farcaster](https://github.com/opensource-observer/oso/blob/main/warehouse/oso_dagster/assets.py)

<NextSteps components={props.components}/>
