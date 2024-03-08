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

## Getting started with GCP

---

If this is your first time getting into GCP, you can do so by going
[here](https://cloud.google.com/).

From there you'll want to click on "Start free" or "Get started for free". You will then be prompted to login with your Google account.

![GCP Signup](./gcp_signup.png)

---

Once you're logged in, you can then proceed to setting up your account. First, select a country and agree to the terms of service. Then, you need to enter your payment information for verification.

![GCP Billing](./gcp_billing.png)

:::tip
GCP offers a free tier that includes $300 in credits. After that, it is easy to stay in the free tier provided you remain under the
1TB per month limit for BigQuery data processed (more on that later).
:::

---

After you've created your account, you will then be asked a few marketing questions from Google. Fill these out as appropriate.

Finally, you will be brought to the admin console where you can create a new project. Feel free to name this GCP project anything you'd like. (Or you can simply leave the default project name 'My First Project'.)

Navigate to **BigQuery** from the left-hand menu and then click on **BigQuery Studio** from the hover menu. This will take you to the BigQuery Console.

![GCP Admin](./gcp_admin.png)

---

The console features an **Explorer** frame on the left-hand side, which lists all the datasets available to you, and a **Studio Console** which has tabs for organizing your work. This will be your workspace for querying the OSO dataset. If this is your first time, you will likely see a welcome message on the first tab in the Studio Console. Now you're ready to start exploring OSO datasets!

![GCP Welcome](./gcp_welcome.png)

## Querying the `oso_playground` dataset

---

If you just created your GCP account by following the steps above, then you'll already be in the BigQuery Console. However, if you're just joining us because you already have an account, then go directly to the BigQuery Console by clicking [here](https://console.cloud.google.com/bigquery).

Close the first tab on the console or simply navigate to the second tab, which should display a blank query editor. Alternatively, you can open a new tab by clicking on the `+` icon on the top right of the console to `Create SQL Query`.

From here you will be able to write any SQL you'd like against the OSO dataset. For example, you can query the `oso_playground` dataset for all the collections in that dataset like this:

```sql
SELECT *
FROM `opensource-observer.oso_playground.collections`
```

Click **Run** to execute your query. The results will appear in a table at the bottom of the console.

![GCP Query](./gcp_query.png)

---

The console will help you complete your query as you type, and will also provide you with a preview of the results and computation time. You can save your queries, download the results, and even make simple visualizations directly from the console.

To explore all the OSO datasets available, see [here](https://console.cloud.google.com/bigquery?project=opensource-observer).

## Setting up your own copy of the `oso_playground` dataset

---

For advanced users that would like to test/develop your own models on the data we
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
