---
title: Colab
sidebar_position: 2
---

Google Colab is a cloud-based Python notebook that allows you to run your analysis without having to install anything on your local machine.

## Authenticate

The fastest way to get started with data science on OSO is to copy one of our notebooks on [Google Colab](https://drive.google.com/drive/folders/1mzqrSToxPaWhsoGOR-UVldIsaX1gqP0F?usp=drive_link).

You can also create a new notebook from scratch and run it in the cloud. Here's how to get started:

1. Create a new Collab notebook [here](https://colab.research.google.com/#create=true).

2. Authenticate with BigQuery. In the first block at the top of the Colab notebook, copy and execute the following code:

   ```python
   # @title Setup
   from google.colab import auth
   from google.cloud import bigquery

   auth.authenticate_user()
   ```

   You will be prompted to give this notebook access to your Google account. Once you have authenticated, you can start querying the OSO data lake.

## Test the Connection

Create a new code block and run a test query. In this block, we will use the `%%bigquery` magic command to run a SQL query and store the results in a Pandas dataframe (named `df` in my example).

Here's an example of how to fetch the latest code metrics for all projects in the OSO data lake.

```python
# replace 'my-oso-playground' with your project id
%%bigquery df --project my-oso-playground

SELECT *
FROM `oso_playground.code_metrics_by_project_v1`
ORDER BY last_commit_date DESC
```

:::important
Remember to replace `my-oso-playground` with your project id. This will attach the query to your billing account.
:::

Execute the code block. The query will run in a few seconds and the results will be stored in the `df` dataframe.

The most common error you'll run into is that you don't have the right project id or you haven't subscribed to the right data set (`oso_playground` in this example).

If the query excecuted, then you can create a new code block to preview the first few rows of your dataframe:

```python
df.head()
```

## Explore the Production Data

Now it's time to move from the "playground" to the "production" dataset. Once you have a working query, you can replace `oso_playground` with `oso_production` to fetch all data available from the production dataset.

```python
# replace 'my-oso-playground' with your project id
%%bigquery df --project my-oso-playground

SELECT *
FROM `oso_production.code_metrics_by_project_v1`
ORDER BY last_commit_date DESC
```

That's it! You're ready to start analyzing the OSO dataset in a Google Colab notebook. Check out our [Tutorials](../../tutorials) for examples of how to analyze the data.

:::tip
You can also download your Colab notebooks to your local machine and run them in Jupyter.
:::
