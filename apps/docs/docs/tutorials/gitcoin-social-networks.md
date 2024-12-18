---
title: Funding in a Social Network
sidebar_position: 5
---

Analyze Gitcoin grants funding in a social network. New to OSO? Check out our [Getting Started guide](../get-started/index.md) to set up your BigQuery or API access.

This tutorial combines Farcaster and Gitcoin data to to identify popular projects within a social network.

## BigQuery

If you haven't already, then the first step is to subscribe to OSO public datasets in BigQuery. You can do this by clicking the "Subscribe" button on our [Datasets page](../integrate/datasets/#oso-production-data-pipeline). For this tutorial, you'll need to subscribe to the Gitcoin and Karma3/OpenRank datasets. (You can also use the Farcaster dataset in place of OpenRank.)

The following queries should work if you copy-paste them into your [BigQuery console](https://console.cloud.google.com/bigquery).

### Identify popular projects within your social network

```sql
select distinct
  donations.donor_address,
  users.user_source_id as fid,
  users.user_name as username,
  donations.project_name,
  amount_in_usd,
  timestamp
from `gitcoin.all_donations` as donations
join `oso_production.artifacts_by_user_v1` as users
  on lower(donations.donor_address) = users.artifact_name
where
  user_source = 'FARCASTER'
  and users.user_source_id in (
    with max_date as (
      select max(date) as last_date
      from `karma3.localtrust`
    )
    select cast(j as string) as fid
    from `karma3.localtrust`
    where i = 5650
    order by v desc
    limit 150
  )
```
