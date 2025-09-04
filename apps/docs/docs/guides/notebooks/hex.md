---
title: Hex
sidebar_position: 4
---

Hex is a collaborative data notebook platform that supports Python and SQL. You can use pyoso in Hex to query the OSO data lake and build interactive analyses.

## Get Started

To get started with OSO in Hex:

1. Create a new Hex project or open an existing one.

2. Add your OSO API key as an environment variable:
   - Go to the **Environment** tab in your Hex project.
   - Click **+ Add environment variable**.
   - Name it `OSO_API_KEY` and paste your API key as the value.
   - Click **Save**.

3. In a new Python cell, run the following setup code:

   ```python
   import pandas as pd

   try:
       from pyoso import Client
   except:
       ! pip install pyoso
       from pyoso import Client

   client = Client(api_key=OSO_API_KEY)

   def stringify(arr):
       return "'" + "','".join(arr) + "'"
   ```

   :::tip
   We use the try/except block to check if the `pyoso` package is already installed. If not, it installs the package and then imports it. This way, you can run the code in a new cell without having to restart the kernel.
   :::

4. Run a test query:

   ```python
   query = """
   SELECT
   project_id,
   project_name,
   display_name
   FROM projects_v1
   WHERE lower(display_name) LIKE lower('%merkle%')
   """
   df = client.to_pandas(query)
   df.head()
   ```

That's it! You're ready to start analyzing the OSO dataset in Hex. Check out our [Tutorials](../../tutorials) for examples of how to analyze the data.
