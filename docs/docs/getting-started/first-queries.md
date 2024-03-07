---
title: Write Your First Queries
sidebar_position: 3
---

:::info
OSO's data warehouse is located on BigQuery and is available publicly by
referencing it as `opensource-observer.oso`. If you're looking to explore the
data, or to contribute to our public set of models you will need to have an
account with GCP (Google Cloud).
:::

## Getting tarted with GCP

If this is your first time getting into GCP, you can do so by going
[here](https://cloud.google.com/).

From there you'll want to click on "Try it free" or "Start free".
Either option will initialize your GCP account and ask for a payment method.
You can use the free trial, but that is only for limited usage.
However, it is possible to stay in the free tier if you stay under the
1TB free tier limit for BigQuery data processed (more on that later).

Once you've completed those steps, you will then want to create a new project.
Feel free to name this GCP project anything you'd like.

## Querying the `oso_playground` dataset

Once you've setup your GCP account and project, you can simply go to the BigQuery Console and start querying. Access it [here](https://console.cloud.google.com/bigquery).

From here click on `Create SQL Query`. Once you've done this a new tab will appear inside the BigQuery Console. From here you will be able to write any SQL you'd like against the OSO dataset. For example, you can query the `oso_playground` dataset for all the collections in that dataset like this:

```sql
SELECT *
FROM `opensource-observer.oso_playground.collections`
```

To explore the datasets available, see [here](https://console.cloud.google.com/bigquery?project=opensource-observer).

## Setting up your own copy of the `oso_playground` dataset

For those of you that would like to test/develop your own models on the data we
have available publicly, you can instantiate your own datasets in BigQuery and
configure a dbt profile that will automatically copy the same data used in the
"playground" into your own dataset.

In the future we will make it easy to use our terraform module to make
initialize the dataset (even if you don't want it to be publicly available). For
now, because that module also sets up other parts of our infrastructure the
easiest method is to create a dataset in BigQuery UI.

To do this:

1. Go to the [BigQuery UI](https://console.cloud.google.com/bigquery).
2. Click on the vertical '...' near the name of your Project.
3. Click `Create Dataset`
4. Create a dataset in the US Multi-region (or anywhere but beaware that other
   regions will incur further charges for egressing data). Be sure to remember
   the dataset ID you used. We will use it soon.

Once that's completed you can then create an authentication profile for dbt to
connect to your dataset like the one below (replace the `dataset` and `project`
sections with your own dataset ID and project ID):

```yml
opensource_observer:
  outputs:
    dev:
      type: bigquery
      # REPLACE
      dataset: YOUR_DATA_SET_NAME
      job_execution_time_seconds: 300
      job_retries: 1
      location: US
      method: oauth
      project: YOUR_PROJECT_ID
      threads: 1
  target: dev
```

_Note: For this guide to work you must use the `dev` target_

Now that you have this you can log in to google:

```bash
$ gcloud auth application-default login
```

And from within the root of the oso repository you could run the dbt models to
fill your profile:

```bash
$ poetry shell # this gets you into the right python environment
$ dbt run
```

Once this is completed, you'll have a full "playground" of your own. Happy data sciencing!
