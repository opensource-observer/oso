---
title: Do Data Science
sidebar_position: 4
---

:::info
Notebooks are a great way for data scientists to explore data, organize ad-hoc analysis, and share insights. We've included several template notebooks to help you get started working with OSO data. You can find these in the [community directory](https://github.com/opensource-observer/insights/tree/main/community/notebook_templates) of our insights repo. We encourage you to share your analysis and visualizations with the OSO community.
:::

## Setting Up Your Environment

---

We will assume you have some familiarity with setting up a local Python environment and running [Jupyter notebooks](https://jupyter.org/). We strongly recommend using Python >= 3.11. However, this guide should work for Python >= 3.7.

:::tip
If this is your first time setting up a data science workstation, we recommend [downloading Anaconda](https://www.anaconda.com/download) and following their instructions for installation. Then, check out the [Jupyter docs](https://jupyter-notebook-beginner-guide.readthedocs.io/en/latest/) to learn how to write your first notebooks.
:::

### Install Standard Dependencies

You should have the following standard dependencies installed in your local environment. It is a best practice to use a Python virtual environment tool such as [virtualenv](https://virtualenv.pypa.io/en/latest/) to manage dependencies.

#### For working with dataframes and vector operations

- [pandas](https://pandas.pydata.org/)
- [numpy](https://numpy.org/)

#### For graph and statistical analysis

- [networkx](https://networkx.org/)
- [scikit-learn](https://scikit-learn.org/stable/)
- [scipy](https://www.scipy.org/)

#### For charting and data visualization

- [matplotlib](https://matplotlib.org/)
- [seaborn](https://seaborn.pydata.org/)
- [plotly](https://plotly.com/python/)

### Install the BigQuery Python Client Library

From the command line, install **google-cloud-bigquery** either directly on your machine or in a new virtual environment:

```bash
$ pip install google-cloud-bigquery
```

## Connecting to GCP

---

This section will walk you through the process of obtaining a GCP service account key and connecting to BigQuery from a Jupyter notebook. If you don't have a GCP account, you will need to create one (see [here](../getting-started/first-queries) for instructions).

### Obtain a GCP Service Account Key

From the [GCP Console](https://console.cloud.google.com/), navigate to the BigQuery API page by clicking **API & Services** > **Enabled APIs & services** > **BigQuery API**.

You can also go there directly by following [this link](https://console.cloud.google.com/apis/api/bigquery.googleapis.com/).

![GCP APIs](./gcp_apis.png)

---

Click the **Create Credentials** button.

![GCP Credentials](./gcp_credentials.png)

---

You will prompted to configure your credentials:

- **Select an API**: BigQuery API
- **What data will you be accessing**: Application data (Note: this will create a service account)

Click **Next**.

---

You will be prompted to create a service account:

- **Service account name**: Add whatever name you want (eg, playground-service-account)
- **Service account ID**: This will autopopulate based on the name you entered and give you a service account email
- **Service account description**: Optional: describe the purpose of this service account

Click **Create and continue**.

---

You will be prompted to grant your service account access to your project.

- **Select a role**: BigQuery > BigQuery Admin

![GCP Service Account](./gcp_service_account.png)

Click **Continue**.

---

You can skip the final step by clicking **Done**. Or, you may grant additional users access to your service account by adding their emails (this is not required).

You should now see the new service account under the **Credentials** screen.

![GCP Credentials Keys](./gcp_credentials_keys.png)

---

Click the pencil icon under **Actions** in the **Service Accounts** table.

Then navigate to the **Keys** tab and click **Add Key** > **Create new key**.

![GCP Add Key](./gcp_add_key.png)

---

Choose **JSON** and click **Create**.

It will download the JSON file with your private key info. You should be able to find the file in your downloads folder.

Now you're ready to authenticate with BigQuery using your service account key.

### Connect to BigQuery from a Jupyter Notebook

From the command line, open a Jupyter notebook:

```bash
$ jupyter notebook
```

A Jupyter directory will open in your browser. Navigate to the directory where you want to store your notebook.

Click **New** > **Python 3** to open a new notebook. (Use your virtual environment if you have one.)

---

You should have a blank notebook open.

Import the BigQuery client library and authenticate with your service account key.

```python

from google.cloud import bigquery
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '' # path to your service account key in your downloads folder
client = bigquery.Client()
```

Try a sample query to test your connection:

```python
query = """
    SELECT *
    FROM `opensource-observer.oso_playground.collections`
"""
results = client.query(query)
results.to_dataframe()
```

If everything is working, you should see a dataframe with the results of your query.

### Safekeeping Your Service Account Key

You should never commit your service account key to a public repository. Instead, you can store it in a secure location on your local machine and reference it in your code using an environment variable.

If you plan on sharing your notebook with others, you can use a package like [python-dotenv](https://pypi.org/project/python-dotenv/) to load your environment variables from a `.env` file.

Always remember to add your `.env` or `credentials.json` file to your `.gitignore` file to prevent it from being committed to your repository.

## Running Your Own Analysis

---

Once you have your local environment set up, you can fork any of the notebooks in the [community directory](https://github.com/opensource-observer/insights/tree/main/community/notebooks).

These notebooks typically have the following structure:

- **Setup**: Import dependencies and set up environment variables.
- **Query**: Fetch data from the OSO data warehouse.
- **Transform**: Clean and transform the data into a format that is ready for analysis.
- **Analyze**: Perform analysis and generate visualizations.
- **Export**: Export the results to a CSV or JSON file.

This next section will help you create a notebook from scratch, performing each of these steps using the OSO playground dataset.

The example below fetches the latest code metrics for all projects in the OSO data warehouse and generates a scatter plot of the number of forks vs the number of stars for each project.

You can find the full notebook [here](https://github.com/opensource-observer/insights/blob/main/community/notebooks/oso_starter_tutorial.ipynb).

### Setup

From the command line, create a new Jupyter notebook:

```bash
$ jupyter notebook
```

A Jupyter directory will open in your browser. Navigate to the directory where you want to store your notebook. Create a new notebook.

Import the following dependencies:

```python
from google.cloud import bigquery
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
```

Authenticate with your service account key:

```python
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '' # path to your service account key in your downloads folder
client = bigquery.Client()
```

### Query

In this example, we will fetch the latest code metrics for all projects in the OSO data warehouse.

```python
query = """
    SELECT *
    FROM `opensource-observer.oso_playground.code_metrics_by_project`
    ORDER BY last_commit_date DESC
"""
results = client.query(query)
```

We recommend exploring the data in [the BigQuery console](https://console.cloud.google.com/bigquery) before running your query in your notebook. This will help you understand the structure of the data and the fields you want to fetch.

[![GCP Playground](./gcp_playground.png)](https://console.cloud.google.com/bigquery)

---

### Transform

Once you have fetched your data, you can transform it into a format that is ready for analysis.

Store the results of your query in a dataframe and preview the first few rows:

```python
df = results.to_dataframe()
df.head()
```

Next, we will apply some basic cleaning and transformation to the data:

- Remove any rows where the number of forks or stars is 0; copy to a new dataframe
- Create a new column to indicate whether the project has had recent activity (commits in the last 6 months)

```python
dff = df[(df['forks']>0) & (df['stars']>0)].copy()
dff['recent_activity'] = dff['commits_6_months'] > 0
```

### Analyze

Now that we have our data in a format that is ready for analysis, we can perform some basic analysis and generate visualizations.

We'll start by creating a logscale scatter plot of the number of forks vs the number of stars for each project.

```python
fig, ax = plt.subplots(figsize=(10,10))
sns.scatterplot(
    data=dff,
    x='stars',
    y='forks',
    hue='recent_activity',
    alpha=.5,
    ax=ax
)
ax.set(
    xscale='log',
    yscale='log',
    xlim=(.9,10_000),
    ylim=(.9,10_000)
)
ax.set_title("Ratio of stars to forks by project", loc='left')
```

Here's a preview of the scatter plot:

![Stars vs Forks](./stars_vs_forks.png)

We can continue the analysis by differentiating between projects that have a high ratio of stars to forks and those that have a low ratio. We'll borrow [Nadia Asparouhova](https://nadia.xyz/oss/)'s term "stadium" and simplistically apply it to any project that has a higher than average ratio of stars to forks.

```python
dff['stars_to_forks_ratio'] = dff['stars'] / dff['forks']
avg = dff['stars_to_forks_ratio'].mean()
dff['stadium_projects'] = dff['stars_to_forks_ratio'] >= avg
print(avg)
```

We can now perform further analysis to see how the distribution of stars to forks ratios is spread across the dataset, with a vertical line indicating the average ratio.

```python
fig, ax = plt.subplots(figsize=(15,5))
sns.histplot(dff['stars_to_forks_ratio'], ax=ax)
ax.axvline(avg, color='red')
```

Here's a preview of the histogram:

![Stars to Forks Ratio](./histogram.png)

Finally, we'll make a crosstab to see how many projects are classified as "stadium" and how many are not.

```python
pd.crosstab(dff['recent_activity'], dff['stadium_projects'])
```

At the time of writing, the crosstab shows 110 "stadium" projects with recent activity versus 829 non-stadium projects.

Some of the top projects in the OSO dataset by this categorization include [IPFS](https://github.com/ipfs), [Trail of Bits](https://github.com/trailofbits), and [Solidity](https://github.com/ethereum/solidity).

### Export

When working with smaller datasets like this one, it's helpful to export the results of your analysis to a CSV or JSON file. This preserves a snapshot of the data for further analysis or sharing with others.

```python
dff.to_csv('code_metrics.csv', index=False)
```

## Creating Impact Vectors

---

Run statistical analysis to identify top performing OSS projects.

An impact vector must meet the requirements in the [Impact Vector Specification](../how-oso-works/resources/impact-vector-spec).

We would love to see people create their own impact vectors and distribution analyses!

Fork [this notebook](https://github.com/opensource-observer/insights/blob/main/community/datasets/retropgf3_results/ImpactVectors%20vs%20DistributionResults.ipynb) and submit a PR with your impact vector.

## Sharing Analysis

---

Once you have completed your analysis, you can share it with the community by submitting a PR to the [insights repo](https://github.com/opensource-observer/insights).

If you have ideas for analysis that you would like to see or receive help on, please [open an issue](https://github.com/opensource-observer/insights/issues) and tag one of the maintainers.
