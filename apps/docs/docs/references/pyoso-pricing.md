---
title: Paid Tiers for API Access
sidebar_position: 99
draft: true
---

Pyoso is a powerful API wrapper that brings the full capabilities of the OSO data lake to your fingertips—now with LLM integration. Whether you're a casual explorer or building data-driven apps, we offer flexible pricing that scales with your usage and your needs.

## Monthly Subscription Tiers

Users can purchase a monthly subscription to get a certain number of OSO Query Tokens.

Unused tokens roll over to the next month.

The pricing is as follows:

| Tier           | Monthly Fee | Token Allowance | Additional Tokens |
| -------------- | ----------- | --------------- | ----------------- |
| **Free**       | $0          | 100             | $0.0400 per token |
| **Hobbyist**   | $20         | 1,000           | $0.0200 per token |
| **Pro**        | $400        | 25,000          | $0.0150 per token |
| **Enterprise** | $1000       | 100,000         | $0.0075 per token |

## OSO Query Tokens

OSO charges queries in terms of "OSO Query Tokens". The formula for computing the number of tokens is as follows:

```
tokens = wall_time * model_multiplier + data_volume + num_tokens_llm * llm_multiplier
```

Where:

- `wall_time` is the amount of time it takes for a query to complete, in minutes.
- `model_multiplier` is a multiplier that depends on whether the user is querying a mart model (3.0), a source model (2.0), or an intermediate model (1.0).
- `data_volume` is the amount of data returned by a query, in gigabytes.
- `num_tokens_llm` is the number of tokens in the LLM prompt.
- `llm_multiplier` is a multiplier that depends on the LLM model used (e.g., Claude 3.5 Sonnet is 2.0, Opus is 1.0, etc.)

### Example 1: Querying a staging model

Here's a simple query that returns a small amount of data from a staging model.

```sql
SELECT * FROM stg_op_atlas_project LIMIT 5
```

- `wall_time` = 432.81ms (0.0072135 minutes)
- `model_multiplier` = 2.0 (staging model)
- `data_volume` = 400 kb (0.0004GB)
- `num_tokens_llm` = 0
- `llm_multiplier` = 0

This would be

```
tokens = 0.0072135 * 2.0 + 0.0004 + 0 * 0 = 0.014827
```

### Example 2: Querying a mart and a staging model

Here's a computationally expensive query that returns a modest amount of data from a mart model and a staging model.

```sql
SELECT
    tx.from_address,
    tx.block_timestamp
FROM stg_superchain__transactions AS tx
JOIN artifacts_by_project_v1 AS abp ON tx.to_address = abp.artifact_name
WHERE
    abp.project_name = '{PROJECT}'
    AND tx.block_timestamp >= DATE '2024-09-01'
    AND (
        tx.from_address IN ({stringify(ADDRESSES)})
        OR tx.from_address IN (
            SELECT artifact_name
            FROM int_superchain_onchain_user_labels
            WHERE farcaster_id IN ({stringify(FIDS)})
        )
    )
```

- `wall_time` = 3.76 minutes
- `model_multiplier` = 3.0 (mart model)
- `data_volume` = 559 mb (0.559GB)
- `num_tokens_llm` = 0
- `llm_multiplier` = 0

This would be

```
tokens = 3.76 * 3.0 + 0.559 + 0 * 0 = 11.88 + 0.559 = 12.439
```

A hobbyist user would be charged approximately $0.25 for this query.

## Additional Notes

These values are subject to change.

Over time, we will adjust the pricing to reflect the actual costs of running the service. The `model_multiplier` coefficients will likely become more granular to reflect actual demand trends.
