---
title: Connect Pyoso to Google Sheets
description: Guide to creating a Google Sheets connector on OSO and querying sheet data via pyoso
sidebar_position: 3
---

This guide shows you how to set up a Google Sheets connector in the Open Source Observer (OSO) app and then use [pyoso](../get-started/python.md) to query that sheet. We'll cover:

1. Creating a service account and metadata sheet in Google Cloud.
2. Configuring the Google Sheets connection in OSO.
3. Querying your sheet from a Jupyter notebook using pyoso.

## Prerequisites

- An active OSO account with access to the Organization & Connections page.
- A Google Cloud project where you can create a service account.
- A Google Sheet to serve as the metadata index and one or more data sheets.
- Python (Jupyter or your environment of choice) with `pyoso` installed.

## Step 1: Create a Service Account

1. Go to your Google Cloud Console and select (or create) the project you'll use.
2. Navigate to **IAM & Admin → Service Accounts**.
3. Click **Create Service Account**, give it any name (no special permissions required), and finish.
4. After creating the service account, click **Actions → Manage Keys → Add Key → Create New Key (JSON)**.
5. Download and save the JSON key file; you'll Base64-encode this in a later step.

## Step 2: Create a Metadata Sheet

1. In Google Sheets, create a new spreadsheet that will serve as the "metadata sheet."
2. The metadata sheet must have at least these columns (in row 1):
   - **table_name**
   - **sheet_id_and_tab**
   - **owner**
   - **notes** _(optional)_
3. Populate row 2 (and beyond) with entries like:

   | table_name      | sheet_id_and_tab            | owner        | notes           |
   | --------------- | --------------------------- | ------------ | --------------- |
   | `my_test_sheet` | `1A2B3C4D5E6F7G8H9I#Sheet1` | your-email@… | "Demo metadata" |

   - **table_name**: How the sheet will appear when you query via SQL (e.g., `my_test_sheet`).
   - **sheet_id_and_tab**: The spreadsheet’s ID (from its URL) followed by a `#` and the exact tab name.
   - **owner**: Your email (or the service account’s email).

4. Share this metadata sheet with your service account’s email (the one you just created). Grant at least **Viewer** access.
5. You will also need to share the spreadsheet you want to query with the service account email.

## Step 3: Configure the Google Sheets Connector in OSO

1. In the OSO web app, go to **Organization → Connections**.
2. Click **Add Connection** and choose **Google Sheets**.
3. Fill out the form:
   - **Name**: Any unique, descriptive name (e.g., `my-gsheets-connector`).
   - **Service Account Key (Base64)**:
     1. Open the JSON key file you downloaded in Step 1.
     2. Base64-encode its contents (for example, run `base64 service-account.json`).
     3. Copy the Base64 string and paste it into this field.
   - **Metadata Sheet ID and Tab**: Copy your metadata sheet’s ID and tab name (e.g., `1A2B3C4D5E6F7G8H9I#Sheet1`).
4. Click **Submit**. If everything is configured correctly, OSO will register your Google Sheets connector and create a schema named `[your_org_name]__gsheets.default`.

> **Note**: The schema name will be based on your organization name. For example, if your organization is named "acme", the schema would be `acme__gsheets.default` (note the double underscore). Replace `[your_org_name]` in the queries below with your actual organization name.

## Step 4: Verify in Pyoso

Below is a sample Jupyter notebook workflow to confirm your sheet is visible and to join it with OSO data. Make sure you have your `OSO_API_KEY` set in a `.env` file or environment variable.

```python
# Install dependencies (if you haven't already)
# pip install pyoso python-dotenv pandas
```

```python
from dotenv import load_dotenv
import os
import pandas as pd
from pyoso import Client

# Load your OSO_API_KEY from a .env file or environment
load_dotenv()
OSO_API_KEY = os.environ["OSO_API_KEY"]

client = Client(api_key=OSO_API_KEY)
```

### Check That the Sheet Is Present

Use a simple `SELECT` to preview up to 5 rows from your metadata-indexed sheet. Replace `my_test_sheet` with your `table_name` from the metadata sheet and `[your_org_name]` with your organization name.

```python
df_preview = client.to_pandas("""
SELECT *
FROM [your_org_name]__gsheets.default.my_test_sheet
LIMIT 5
""")
df_preview
```

### Join the Sheet Data with OSO Projects

This query will return rows where the `oso_slug` from your Google Sheet matches a `project_name` in OSO’s `projects_v1` table.

```python
df_projects = client.to_pandas("""
SELECT
  p.project_id,
  sheet.oso_slug,
  sheet.project_name AS application_name,
  sheet.season,
  sheet.op_total_amount
FROM [your_org_name]__gsheets.default.my_test_sheet AS sheet
JOIN oso.projects_v1 p
  ON sheet.oso_slug = p.project_name
WHERE sheet.oso_slug IS NOT NULL
""")
df_projects.tail()
```

That query will return rows where the `oso_slug` from your Google Sheet matches a `project_name` in OSO’s `projects_v1` table. Example output:

|     | project_id                              | oso_slug        | application_name           | some_value |
| --- | --------------------------------------- | --------------- | -------------------------- | ---------- |
| 395 | abc123XYZ456ghi789JKLmnOPqrsTTuvWXy0123 | example-project | Example Project Name       | DemoValue  |
| 396 | def456ABC123stu789VWXyzLMNoPQRjkl345    | another-project | Another Project Example    | DemoValue2 |
| 397 | ghi789DEF456klm123OPQrst456UVWxYZ789    | sample-project  | Sample Project for Testing | DemoValue3 |
| 398 | jkl012GHI789nop345RSTuvw012XYZabc678    | test-project    | Test Project in OSO        | DemoValue4 |
| 399 | mno345JKL012qrs678TUVwxy901ABCdef234    | pilot-project   | Pilot Project Data         | DemoValue5 |

_(The actual values will depend on your sheet’s contents and matching OSO projects.)_

### Pull Key Metrics for Those Projects

If you want to enrich your sheet data with metrics from OSO, you can join to `key_metrics_by_project_v0`. For example, assuming your sheet again has `oso_slug` values:

```python
df_joined = client.to_pandas("""
SELECT
  p.project_id,
  sheet.oso_slug,
  sheet.project_name AS application_name,
  sheet.another_column AS some_value,
  m.display_name,
  km.amount
FROM [your_org_name]_gsheets.default.my_test_sheet AS sheet
JOIN oso.projects_v1 AS p
  ON sheet.oso_slug = p.project_name
JOIN oso.key_metrics_by_project_v0 AS km
  ON p.project_id = km.project_id
JOIN oso.metrics_v0 AS m
  ON km.metric_id = m.metric_id
WHERE
  sheet.oso_slug IS NOT NULL
  AND m.display_name IN (
    'Active Contracts',
    'Repositories',
    'Contributors',
    'Commits',
    'Contract Invocations',
    'Gas Fees'
  )
""")
df_joined
```

The result will list each matching project with its key metrics. Example:

|     | project_id                              | oso_slug        | application_name        | some_value | display_name     | amount  |
| --- | --------------------------------------- | --------------- | ----------------------- | ---------- | ---------------- | ------- |
| 0   | abc123XYZ456ghi789JKLmnOPqrsTTuvWXy0123 | example-project | Example Project Name    | DemoValue  | Commits          | 12345.0 |
| 1   | abc123XYZ456ghi789JKLmnOPqrsTTuvWXy0123 | example-project | Example Project Name    | DemoValue  | Contributors     | 200.0   |
| 2   | def456ABC123stu789VWXyzLMNoPQRjkl345    | another-project | Another Project Example | DemoValue2 | Active Contracts | 10.0    |
| 3   | def456ABC123stu789VWXyzLMNoPQRjkl345    | another-project | Another Project Example | DemoValue2 | Repositories     | 5.0     |
| 4   | ghi789DEF456klm123OPQrst456UVWxYZ789    | sample-project  | Sample Project for …    | DemoValue3 | Gas Fees         | 42.5    |
| …   | …                                       | …               | …                       | …          | …                | …       |

### Pivoting Metrics

To pivot this DataFrame so each project is one row and each metric gets its own column:

```python
df_pivot = df_joined.pivot_table(
    index=['project_id', 'oso_slug', 'application_name', 'some_value'],
    columns=['display_name'],
    values='amount',
    aggfunc='sum',
    fill_value=0
)

# Show top 5 by descending Gas Fees (if present)
df_pivot.sort_values(by='Gas Fees', ascending=False).head(5)
```

Example pivoted output:

| project_id                              | oso_slug        | application_name        | some_value | Active Contracts | Commits  | Contributors | Gas Fees | Repositories |
| --------------------------------------- | --------------- | ----------------------- | ---------- | ---------------- | -------- | ------------ | -------- | ------------ |
| abc123XYZ456ghi789JKLmnOPqrsTTuvWXy0123 | example-project | Example Project Name    | DemoValue  | 15               | 12,345.0 | 200          | 0        | 8            |
| def456ABC123stu789VWXyzLMNoPQRjkl345    | another-project | Another Project Example | DemoValue2 | 10               | 0        | 50           | 42.5     | 5            |
| ghi789DEF456klm123OPQrst456UVWxYZ789    | sample-project  | Sample Project for …    | DemoValue3 | 5                | 1,234.0  | 20           | 10.0     | 2            |
| jkl012GHI789nop345RSTuvw012XYZabc678    | test-project    | Test Project in OSO     | DemoValue4 | 0                | 0        | 5            | 0        | 1            |
| mno345JKL012qrs678TUVwxy901ABCdef234    | pilot-project   | Pilot Project Data      | DemoValue5 | 2                | 500.0    | 10           | 5.0      | 3            |

_(Actual values will align with your sheet and OSO metrics.)_

## Step 5: Make Updates to the Sheet

You can make updates to the sheet and they will be reflected in pyoso. For example, if you add a new row to the sheet, it will be reflected in the `df_projects` DataFrame. You can even change column names.

:::info
Updates to your spreadsheet might take up to 10 minutes to be reflected in pyoso.
:::

## Troubleshooting

- **Permission Denied**

  - Ensure you shared both the metadata sheet and each data sheet with your service account email.
  - Verify the Base64-encoded key matches the JSON key for that service account.

- **Connector Not Found**

  - Check that you used the exact sheet ID (not the full URL) when you created the metadata sheet entry.
  - Confirm the `#TabName` suffix matches a tab that actually exists in the spreadsheet.

- **Empty Results**
  - Double-check the `table_name` in your metadata sheet matches your SQL `FROM` clause (including capitalization).
  - Run `SELECT * FROM [your_org_name]__gsheets.default.__TABLES__` to list all available sheets.

## Next Steps

- Explore other [pyoso tutorials](../tutorials/index.mdx) to learn more query patterns.
- See the official Trino docs on Google Sheets connector for advanced settings:  
  [Trino: Google Sheets Connector](https://trino.io/docs/current/connector/googlesheets.html).

That's it! You’ve now connected a Google Sheet to OSO and pulled its data into Python via pyoso. Feel free to customize queries, join with other OSO tables, and build dashboards on top of your sheet data.
