---
title: Connect Pyoso to Google Sheets
description: Guide to creating a Google Sheets connector on OSO and querying sheet data via pyoso
sidebar_position: 3
---

This guide shows you how to set up a Google Sheets connector in the Open Source Observer (OSO) app and then use [pyoso](../get-started/python.md) to query that sheet. We'll cover:

1. Enabling the Google Sheets API and creating a service account in Google Cloud.
2. Creating a metadata sheet with the correct format.
3. Configuring the Google Sheets connection in OSO.
4. Querying your sheet from a Jupyter notebook using pyoso.

## Prerequisites

- An active OSO account with access to the Organization & Connections page.
- A Google Cloud project where you can create a service account.
- A Google Sheet to serve as the metadata index and one or more data sheets.
- Python (Jupyter or your environment of choice) with `pyoso` installed.

## Step 0: Enable Google Sheets API

Before creating a service account, you must enable the Google Sheets API in your Google Cloud project.

1. Go to the [Google Cloud Console](https://console.cloud.google.com/) and select (or create) the project you'll use.
2. Navigate to **APIs & Services → Library**.
3. Search for "Google Sheets API".
4. Click on **Google Sheets API** and then click **Enable**.
5. Wait for the API to be enabled (usually takes a few seconds).

## Step 1: Create a Service Account

1. In the Google Cloud Console, navigate to **IAM & Admin → Service Accounts**.
2. Click **Create Service Account**, give it a descriptive name (e.g., `oso-sheets-connector`), and finish.
   - No special permissions are required for basic read-only access.
3. After creating the service account, click **Actions → Manage Keys → Add Key → Create New Key (JSON)**.
4. Select **JSON** format and click **Create**.
5. Download and save the JSON key file securely.

:::warning Security Note
This JSON file contains sensitive credentials. Never commit it to version control or share it publicly. Consider rotating keys every 90 days as a security best practice.
:::

### Finding Your Service Account Email

Your service account email follows this format: `service-account-name@project-id.iam.gserviceaccount.com`

To find it:
1. Go to **IAM & Admin → Service Accounts** in the Google Cloud Console.
2. Your service account is listed with its email address.
3. Copy this email - you'll need it to share your Google Sheets.

## Step 2: Create a Metadata Sheet

The metadata sheet tells Trino where to find your data sheets and how to map them to SQL table names.

### Create the Metadata Sheet

1. In Google Sheets, create a new spreadsheet that will serve as the "metadata sheet."
2. **Important**: The first row must have these exact column headers (with capital letters and spaces):
   - `Table Name`
   - `Sheet ID`
   - `Owner`
   - `Notes` _(optional)_

:::caution Column Header Format
The column headers must match exactly as shown above, including capitalization and spaces. Using lowercase or underscores (e.g., `table_name`) will cause errors.
:::

### Populate the Metadata Sheet

3. In row 2 and beyond, add entries for each data sheet you want to query:

   | Table Name      | Sheet ID                                | Owner                          | Notes           |
   | --------------- | --------------------------------------- | ------------------------------ | --------------- |
   | `my_test_sheet` | `1A2B3C4D5E6F7G8H9I#Sheet1`             | service-account@project.iam... | "Demo metadata" |
   | `sales_data`    | `1X2Y3Z4A5B6C7D8E9F#Q1_Sales!A1:Z1000` | service-account@project.iam... | "Q1 sales"      |

   **Column descriptions:**
   - **Table Name**: How the sheet will appear when you query via SQL (e.g., `my_test_sheet`). Use lowercase with underscores.
   - **Sheet ID**: The spreadsheet's ID with optional tab and range specifier (see format guide below).
   - **Owner**: Your email or the service account's email.
   - **Notes**: Optional description for documentation.

### Sheet ID Format Guide

The Sheet ID can be specified in several ways:

**1. Entire spreadsheet (all tabs):**
```
1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms
```

**2. Specific tab (entire tab):**
```
1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms#Sheet1
```

**3. Specific tab with range:**
```
1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms#Users!A1:E100
```

**How to find the Sheet ID:**
From the Google Sheets URL: `https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit`

:::tip Performance Tip
Using specific ranges (option 3) is recommended for large sheets as it reduces API calls and improves query performance.
:::

### Understanding Two Types of Sheet IDs

It's important to distinguish between:
- **Metadata Sheet ID**: The ID of your metadata sheet - this goes in the OSO connector form (Step 3)
- **Data Sheet IDs**: IDs of your actual data sheets - these go INSIDE the metadata sheet's `Sheet ID` column

### Share Your Sheets

4. Share the **metadata sheet** with your service account's email:
   - Click the **Share** button in Google Sheets
   - Paste your service account email (e.g., `oso-sheets-connector@project-id.iam.gserviceaccount.com`)
   - Set permission to **Viewer** (or **Editor** if you need write access)
   - **Uncheck** "Notify people" (service accounts don't need notifications)
   - Click **Share**

5. Repeat the sharing process for **each data sheet** listed in your metadata sheet.

:::info Permission Requirements
- **Viewer**: Required for read-only queries (SELECT statements)
- **Editor**: Required if you plan to write data back to sheets (INSERT/UPDATE)
:::

## Step 3: Configure the Google Sheets Connector in OSO

1. In the OSO web app, go to **Organization → Connections**.
2. Click **Add Connection** and choose **Google Sheets** from the connector type dropdown.
3. Fill out the form:

   **Connector Name:**
   - Must start with a lowercase letter
   - Can only contain lowercase letters, numbers, and underscores
   - Pattern: `^[a-z][a-z0-9_]*$`
   - Examples: ✅ `marketing_data`, `project_metrics_2024`
   - Invalid: ❌ `Marketing-Data`, `2024_metrics`, `my.sheets`

   **Metadata Sheet ID:**
   - The Sheet ID of your metadata sheet (not the data sheets)
   - Find this in the metadata sheet's URL
   - Example: `1A2B3C4D5E6F7G8H9I`

   **JSON Credentials:**
   - ⚠️ **Important**: Paste the ENTIRE contents of your JSON key file directly
   - Do NOT Base64-encode it yourself - the system will encode it automatically
   - The JSON should start with `{` and end with `}`

4. Click **Submit**.

If everything is configured correctly, OSO will register your Google Sheets connector and create a schema named `[your_org_name]__gsheets.default`.

:::note Schema Naming
The schema name will be based on your organization name with double underscores. For example, if your organization is named "acme", the schema would be `acme__gsheets.default`. Replace `[your_org_name]` in the queries below with your actual organization name.
:::

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

### List Available Tables

First, verify that your connector is working by listing all available tables:

```python
# List all tables in your connector
df_tables = client.to_pandas("""
SHOW TABLES FROM [your_org_name]__gsheets.default
""")
df_tables
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

### Understanding Data Types

:::warning Data Type Limitation
All data from Google Sheets is read as TEXT (VARCHAR). Numbers, dates, and booleans are all returned as strings. You must cast values in your SQL queries to use them as numeric or date types.
:::

**Example with type casting:**

```python
df_typed = client.to_pandas("""
SELECT
  project_name,
  CAST(amount AS DOUBLE) as amount_numeric,
  CAST(date_column AS DATE) as date_parsed,
  CAST(is_active AS BOOLEAN) as is_active_bool
FROM [your_org_name]__gsheets.default.my_test_sheet
LIMIT 10
""")
df_typed
```

### Join the Sheet Data with OSO Projects

This query will return rows where the `oso_slug` from your Google Sheet matches a `project_name` in OSO's `projects_v1` table.

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

That query will return rows where the `oso_slug` from your Google Sheet matches a `project_name` in OSO's `projects_v1` table. Example output:

|     | project_id                              | oso_slug        | application_name           | some_value |
| --- | --------------------------------------- | --------------- | -------------------------- | ---------- |
| 395 | abc123XYZ456ghi789JKLmnOPqrsTTuvWXy0123 | example-project | Example Project Name       | DemoValue  |
| 396 | def456ABC123stu789VWXyzLMNoPQRjkl345    | another-project | Another Project Example    | DemoValue2 |
| 397 | ghi789DEF456klm123OPQrst456UVWxYZ789    | sample-project  | Sample Project for Testing | DemoValue3 |
| 398 | jkl012GHI789nop345RSTuvw012XYZabc678    | test-project    | Test Project in OSO        | DemoValue4 |
| 399 | mno345JKL012qrs678TUVwxy901ABCdef234    | pilot-project   | Pilot Project Data         | DemoValue5 |

_(The actual values will depend on your sheet's contents and matching OSO projects.)_

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
FROM [your_org_name]__gsheets.default.my_test_sheet AS sheet
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

## Common Query Patterns

### Check table schema
```python
df_schema = client.to_pandas("""
DESCRIBE [your_org_name]__gsheets.default.my_test_sheet
""")
df_schema
```

### Count rows
```python
df_count = client.to_pandas("""
SELECT COUNT(*) as total_rows
FROM [your_org_name]__gsheets.default.my_test_sheet
""")
df_count
```

### Join multiple sheets
```python
df_multi = client.to_pandas("""
SELECT
  a.project_name,
  a.metrics,
  b.details
FROM [your_org_name]__gsheets.default.sheet_a a
JOIN [your_org_name]__gsheets.default.sheet_b b
  ON a.project_id = b.project_id
""")
df_multi
```

## Step 5: Make Updates to the Sheet

You can make updates to the sheet and they will be reflected in pyoso. For example, if you add a new row to the sheet, it will be reflected in the `df_projects` DataFrame. You can even change column names.

:::info Cache Timing
Updates to your spreadsheet might take up to 10 minutes to be reflected in pyoso due to caching. This helps prevent hitting Google Sheets API rate limits.
:::

## Performance Optimization

### Cache Behavior
- Data is cached for up to 10 minutes
- First query after cache expiration will be slower
- Subsequent queries use cached data for better performance

### Best Practices
- ✅ Use specific ranges in Sheet ID: `SheetID#Tab!A1:E1000` (better than querying the entire sheet)
- ✅ Keep metadata sheet small and focused
- ✅ Limit row count when possible to reduce API calls
- ✅ Add column headers to all data sheets for better SQL querying
- ❌ Avoid querying entire large sheets repeatedly
- ❌ Don't use `SELECT *` on sheets with many columns unless necessary

## Advanced: Multiple Connectors

You can create multiple Google Sheets connectors for different purposes:

**Example organization:**
- `finance_sheets` → Finance metadata sheet → Finance data sheets
- `marketing_sheets` → Marketing metadata sheet → Marketing data sheets
- `engineering_sheets` → Engineering metadata sheet → Engineering data sheets

Each connector gets its own schema:
- `[org_name]__finance_sheets.default`
- `[org_name]__marketing_sheets.default`
- `[org_name]__engineering_sheets.default`

This approach helps organize data by department or project while maintaining proper access control.

## Troubleshooting

### Permission Denied
- Ensure you shared both the metadata sheet and each data sheet with your service account email.
- Verify the service account email is exactly as shown in Google Cloud Console.
- Check that permissions are set to at least "Viewer" (or "Editor" for write operations).

### Connector Not Found
- Check that you used the exact Sheet ID (not the full URL) in the metadata sheet's `Sheet ID` column.
- Verify the `#TabName` suffix matches a tab that actually exists in the spreadsheet.
- Tab names are case-sensitive - ensure exact match.

### Table Not Found
- Verify the metadata sheet has the exact column headers: `Table Name`, `Sheet ID`, `Owner`, `Notes`
- Check for extra spaces in column headers
- Ensure there are no empty rows between the header row and data rows
- Confirm the `Table Name` in your metadata sheet matches your SQL `FROM` clause (including case)

### Empty Results
- Double-check that the `Table Name` in your metadata sheet matches your SQL query exactly.
- Run `SHOW TABLES FROM [your_org_name]__gsheets.default` to list all available tables.
- Verify that your data sheets have a header row (first row with column names).
- Check that data exists in rows 2 and beyond in your data sheets.

### Invalid Credentials Error
- Ensure you pasted the complete JSON credentials file (from `{` to `}`).
- Verify the JSON is valid (no truncation or formatting errors).
- Try regenerating the service account key if the issue persists.

### Stale Data
- Data updates can take up to 10 minutes to appear due to caching.
- This is normal behavior to prevent hitting Google Sheets API rate limits.
- For immediate updates, consider creating a new query or waiting for cache expiration.

## Security Best Practices

### Service Account Management
- Use separate service accounts for different environments (dev/staging/prod)
- Grant minimal permissions (Viewer unless write access is specifically needed)
- Regularly review which sheets are shared with service accounts

### Credential Security
- Never commit JSON key files to version control
- Store credentials securely using environment variables or secrets management
- Rotate service account keys periodically (recommended: every 90 days)
- Delete old keys after rotation via Google Cloud Console

### Access Auditing
- Periodically review service account access in Google Cloud Console
- Monitor API usage to detect unexpected activity
- Remove access to sheets that are no longer needed

## Next Steps

- Explore other [pyoso tutorials](../tutorials/index.md) to learn more query patterns.
- See the official Trino docs on Google Sheets connector for advanced settings:
  [Trino: Google Sheets Connector](https://trino.io/docs/current/connector/googlesheets.html).
- Learn about [integrating with OSO](../integrate/index.md) to understand what data you can join with your sheets.

That's it! You've now connected a Google Sheet to OSO and pulled its data into Python via pyoso. Feel free to customize queries, join with other OSO tables, and build dashboards on top of your sheet data.
