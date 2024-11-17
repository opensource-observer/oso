---
slug: synthetic-controls
title: "Early experiments with synthetic controls and causal inference"
authors: [ccerv1]
tags: [featured, perspective, research, causal inference]
image: ./syncon.png
---

Over the last few months, we've been exploring frameworks for computing [advanced metrics](./war-for-public-goods) that can offer insights into how specific interventions impact the public goods ecosystem.

For instance, we might want to measure how a group of projects or users that received token incentives performed relative to a similar group that did not receive any incentive.

However, unlike A/B testing in a research setting, we are dealing with a real world economy here. We can't simply randomize the treatment and control groups.

Instead, we need to use advanced statistical methods to estimate the causal effect of the treatment on the target cohort and control for other factors (eg, market conditions, competing incentive programs, elections, etc) that might influence the outcome.

<!-- truncate -->

## A primer on synthetic controls

The [synthetic control method](https://en.wikipedia.org/wiki/Synthetic_control_method) is frequently used for modeling the effects of interventions in complex systems:

> A synthetic control is a weighted average of several units combined to recreate the trajectory that the outcome of a treated unit would have followed in the absence of the intervention. The weights are selected in a data-driven manner to ensure that the resulting synthetic control closely resembles the treated unit in terms of key predictors of the outcome variable. Unlike difference-in-differences approaches, this method can account for the effects of confounders changing over time, by weighting the control group to better match the treatment group before the intervention.

Research econometricians have been using synthetic controls for decades to understand the impact of policy interventions that they can't test in a lab. For example, [Abadie and Gardeazabal](https://pubs.aeaweb.org/doi/10.1257/000282803321455188) used synthetic controls to estimate the impact of the Basque separatist movement on the Basque economy.

At OSO, we are applying these same techniques to network economies. We want to use synthetic controls to measure the impact of grants and other incentive programs on outcomes like retained developers, users, and network TVL.

![dencun](./syncon-base.png)

Another important advantage of the synthetic control method is that it allows analysts to systematically select comparison groups. In our case, we are especially interested in comparing cohorts of grant recipients to similar projects that did not receive grants.

## Leveraging timeseries metrics

Our work on synthetic controls is part of a broader effort to build a flexible engine for conducting advanced analysis on pretty much anything.

Over the past few months, we've been working hard on "timeseries metrics". These models can be used to calculate any metric for any cohort over any timeframe on a rolling basis. They are powerful because they allow you to time travel to any date in history and see how a project or cohort performed.

For example, this simple query will give you every metric for every collection on OSO for every available date:

```sql
select
  t.sample_date,
  m.metric_name,
  c.collection_name,
  t.amount
from timeseries_metrics_by_collection_v0 as t
join metrics_v0 as m
  on t.metric_id = m.metric_id
join collections_v1 as c
  on t.collection_id = c.collection_id
```

Most of timeseries metrics models we're building are computed on rolling windows, bucketed daily. For instance, instead of just measuring monthly active developers by grouping data by month, we now calculate monthly active developers on 30 and 90-day rolling windows (e.g., the trailing average over the previous 30 or 90 days).

These metrics will give us a granular view on how a project or cohort is performing over time.

## Early results

With inspiration from our friends at [Counterfactual Labs](https://github.com/counterfactual-labs), we’ve been using the [pysyncon package](https://sdfordham.github.io/pysyncon/) to estimate the treatment effect.

For example, the model below looks at monthly active developers over a 90-day rolling window for a cohort of projects that received Retro Funding in January 2024 from Optimism. We can compare this cohort to a synthetic control group of similar projects that did not receive Retro Funding.

```python
SynthControlRequest(
    time_predictors_prior_start=datetime(2022, 1, 1),
    time_predictors_prior_end=datetime(2024, 1, 1),
    time_optimize_ssr_start=datetime(2023, 10, 1),
    time_optimize_ssr_end=datetime(2024, 10, 1),
    dependent='active_developers_over_90_day',
    treatment_identifier='op-rpgf3',
    controls_identifier=['ecosystem-x', 'ecosystem-y', 'ecosystem-z'],
    predictors=[
        'new_contributors_over_90_day',
        'commits_over_90_day',
        'issues_opened_over_90_day'
    ]
)
```

Here's a visualization of the treatment group versus the synthetic control group:

![developers](./syncon-devs.png)

The difference between the treatment and synthetic control groups is the estimated treatment effect. In this case, the treatment effect is the difference between the two lines in the chart above (about 150-200 monthly active developers over a 90-day rolling average).

## What's next

As George Box famously said, "all models are wrong, but some are useful."

We're just getting started with this work, but we're excited about the potential to use synthetic controls to better model the effects of incentives on crypto networks. We'll be sharing more results in the days ahead.

In the meantime, you can see some examples of the synthetic control models in our [insights repo](https://github.com/opensource-observer/insights/tree/main/analysis/optimism/syncon) and reach out on [Discord](https://www.opensource.observer/discord) if you want to collaborate.
