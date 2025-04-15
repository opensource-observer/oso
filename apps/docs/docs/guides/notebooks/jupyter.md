---
title: Jupyter
sidebar_position: 3
---

Jupyter is a Python notebook that you can run on your local machine. This section will walk you through setting up a local Jupyter notebook environment and connecting to the OSO data lake using pyoso.

**If you already have Jupyter installed, you can skip the first section.**

## Installation (via Anaconda)

For new users, we recommend [installing Anaconda](https://www.anaconda.com/download). Anaconda conveniently installs Python, the Jupyter Notebook, and other commonly used packages for working with data.

1. Download [Anaconda](https://www.anaconda.com/download). We recommend downloading Anaconda’s latest Python 3 version.

2. Install the version of Anaconda which you downloaded, following the instructions on the download page.

3. After the installation is completed, you are ready to run the notebook server. Open the terminal and execute:

```bash
jupyter notebook
```

4. This will print some information about the notebook server in your terminal, including the URL of the web application (by default, `http://localhost:8888)`). Then, your default web browser should open with a list of files in your current directory. Navigate to **new** and select the option to create a **Python 3 (ipykernel)** Notebook.

![jupyter](./jupyter.png)

Congratulations! You're in. You should have an empty Jupyter notebook on your computer, ready for data sciencing.

:::tip
If you run into issues getting set up with Jupyter, check out the [Jupyter docs](https://docs.jupyter.org/en/latest/install.html).
:::

## Authentication

To access the OSO data lake, you'll need to generate an API key.

1. Go to [www.opensource.observer](https://www.opensource.observer) and create a new account.
2. Log in and go to [Account settings](https://www.opensource.observer/app/settings).
3. In the "API Keys" section, click "+ New".
4. Give your key a label and click "Create".
5. Copy the key and store it securely. You won't be able to see it again.

## Connect to OSO with pyoso

Install the pyoso client:

```bash
pip install pyoso
```

Then start your notebook with the following:

```python
import os
import pandas as pd
from pyoso import Client

OSO_API_KEY = os.environ['OSO_API_KEY']
client = Client(api_key=OSO_API_KEY)
```

Now you're ready to query the OSO data lake. Here's an example:

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

That's it! You're ready to start analyzing the OSO dataset in a Jupyter notebook. Check out our [Tutorials](../../tutorials) for examples of how to analyze the data.
