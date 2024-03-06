---
title: Do Data Science
sidebar_position: 4
---

Share your analysis and visualizations with the OSO community.

Jupyter notebooks are a great way for data scientists to explore data, organize ad-hoc analysis, and share insights. We've included several template notebooks to help you get started working with OSO data. You can find these in the [community directory](https://github.com/opensource-observer/insights/tree/main/community/notebook_templates) of our insights repo.

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

We also recommend [dotenv](https://pypi.org/project/python-dotenv/) for managing environment variables such as API keys. We have included a `.env.example` file in the root of the insights repo that you can use as a template (see [here](https://github.com/opensource-observer/insights/blob/main/.env.example)).

In order to access OSO data directly, you will need an API key. Please apply to join our [Data Collective](https://www.opensource.observer/data-collective).

:::tip
If you need help getting started, check out the [Jupyter docs](https://jupyter-notebook-beginner-guide.readthedocs.io/en/latest/).
:::

## Conducting Analysis

---

Once you have your local environment set up, you can fork any of the notebooks in the [community directory](https://github.com/opensource-observer/insights/tree/main/community/notebook_templates).

These notebooks typiclaly have the following structure:

- **Setup**: Import dependencies and set up environment variables.
- **Query**: Fetch data from the OSO API or data warehouse.
- **Transform**: Clean and transform the data into a format that is ready for analysis.
- **Analyze**: Perform analysis and generate visualizations.
- **Export**: Export the results to a CSV or JSON file.

These notebooks also make use of OSO's Python client for making queries to the API and data warehouse. You can find the source code for the client [here](https://github.com/opensource-observer/insights/blob/main/scripts/oso_db.py).

Here's a sample query that fetches the number of active developers for all projects in the OSO data warehouse since 2014:

```python
result = execute_query(f"""
    WITH Devs AS (
        SELECT
            p."slug" AS "slug",
            e."fromId" AS "fromId",
            TO_CHAR(DATE_TRUNC('MONTH', e."time"), 'YYYY-MM') AS "month",
            CASE WHEN COUNT(DISTINCT e."time") >= 10 THEN 1 ELSE 0 END AS "full_time_developer",
            CASE WHEN COUNT(DISTINCT e."time") < 10 THEN 1 ELSE 0 END AS "part_time_developer"
        FROM event e
        JOIN project_artifacts_artifact paa ON e."toId" = paa."artifactId"
        JOIN project p ON paa."projectId" = p.id
        WHERE
            e."typeId" = 4 -- COMMIT CODE EVENTS ONLY
        GROUP BY
            p."slug",
            e."fromId",
            TO_CHAR(DATE_TRUNC('MONTH', e."time"), 'YYYY-MM')
    )
    SELECT
        slug,
        month,
        SUM("full_time_developer") AS "Full time developers",
        SUM("part_time_developer") AS "Part time developers"
    FROM Devs
    WHERE month >= '2014-01'
    GROUP BY slug, month
    ORDER BY slug, month;
""", col_names=True)
```

Here's a simpler query that creates a mapping of projects to collections:

```python
result = execute_query("""
    SELECT p."slug", c."slug"
    FROM project p
    JOIN collection_projects_project cpp ON p."id" = cpp."projectId"
    JOIN collection c ON cpp."collectionId" = c."id"
    WHERE c."typeId" = 1
""", col_names=False)
```

## Sharing Analysis

---

Once you have completed your analysis, you can share it with the community by submitting a PR to the [insights repo](https://github.com/opensource-observer/insights).

If you have ideas for analysis that you would like to see or receive help on, please [open an issue](https://github.com/opensource-observer/insights/issues) and tag one of the maintainers.

## Creating Impact Vectors

Run statistical analysis to identify top performing OSS projects.

An impact vector must meet the requirements in the [Impact Vector Specification](../resources/impact-vector-spec).

We would love to see people create their own impact vectors and distribution analyses!

---

Fork [this notebook](https://github.com/opensource-observer/insights/blob/main/community/datasets/retropgf3_results/ImpactVectors%20vs%20DistributionResults.ipynb) and submit a PR with your impact vector.
