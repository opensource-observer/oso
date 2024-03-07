---
title: Do Data Science
sidebar_position: 4
---

:::info
Jupyter notebooks are a great way for data scientists to explore data, organize ad-hoc analysis, and share insights. We've included several template notebooks to help you get started working with OSO data. You can find these in the [community directory](https://github.com/opensource-observer/insights/tree/main/community/notebook_templates) of our insights repo. We encourage you to share your analysis and visualizations with the OSO community.
:::

## Getting Started

---

We will assume you have some familiarity with setting up a local Python environment and running Jupyter notebooks.

In order to run the notebooks, you should have the following standard dependencies installed in your local environment:

- [pandas](https://pandas.pydata.org/)
- [networkx](https://networkx.org/)
- [matplotlib](https://matplotlib.org/)
- [seaborn](https://seaborn.pydata.org/)
- [plotly](https://plotly.com/python/)
- [numpy](https://numpy.org/)
- [scipy](https://www.scipy.org/)
- [scikit-learn](https://scikit-learn.org/stable/)

:::tip
If you need help getting started, check out the [Jupyter docs](https://jupyter-notebook-beginner-guide.readthedocs.io/en/latest/).
:::

## Structuring Your Analysis

---

Once you have your local environment set up, you can fork any of the notebooks in the [community directory](https://github.com/opensource-observer/insights/tree/main/community/notebooks).

These notebooks typically have the following structure:

- **Setup**: Import dependencies and set up environment variables.
- **Query**: Fetch data from the OSO data warehouse.
- **Transform**: Clean and transform the data into a format that is ready for analysis.
- **Analyze**: Perform analysis and generate visualizations.
- **Export**: Export the results to a CSV or JSON file.

## Fetching Data

---

In order to access OSO data directly, you will need access to BigQuery. See our guide for writing your first queries [here](../getting-started/first-queries).

Here's a sample BigQuery query that fetches the latest GitHub metrics for all projects in the OSO data warehouse:

```sql
SELECT *
FROM `opensource-observer.oso.github_metrics_by_project`
```

Here's a more complex query that fetches onchain user data:

```sql
SELECT
FROM placeholder
```

## Creating Impact Vectors

---

Run statistical analysis to identify top performing OSS projects.

An impact vector must meet the requirements in the [Impact Vector Specification](../resources/impact-vector-spec).

We would love to see people create their own impact vectors and distribution analyses!

Fork [this notebook](https://github.com/opensource-observer/insights/blob/main/community/datasets/retropgf3_results/ImpactVectors%20vs%20DistributionResults.ipynb) and submit a PR with your impact vector.

## Sharing Analysis

---

Once you have completed your analysis, you can share it with the community by submitting a PR to the [insights repo](https://github.com/opensource-observer/insights).

If you have ideas for analysis that you would like to see or receive help on, please [open an issue](https://github.com/opensource-observer/insights/issues) and tag one of the maintainers.
