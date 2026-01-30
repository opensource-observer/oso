---
title: "Access via Python"
sidebar_position: 1
---

The OSO API serves
queries on metrics and metadata about open source projects.
You can access the full data lake via our `pyoso` Python library.

Let's make your first query in under five minutes.

## Generate an API key

1. [Log in](https://www.oso.xyz/login) to your account
2. Navigate to your organization's **Settings → API Keys**
3. Click **"New Key +"** and give it a descriptive name
4. **Save your key immediately** - you won't see it again

<details>
<summary>Detailed step-by-step instructions</summary>

1. Go to [www.opensource.observer](https://www.oso.xyz/login) and log in
2. You'll be redirected to your organization dashboard
3. In the left sidebar, click the dropdown next to your organization name
4. Select **"Settings"**
5. Navigate to **"Organization" → "API Keys"**
6. Click **"New Key +"**
7. Enter a descriptive label (e.g., "Production API")
8. Copy and save your key immediately
9. Click **"Create"**

![generate API key](../integrate/generate-api-key.png)

</details>

## Install pyoso

You can install pyoso using pip:

```bash
pip install pyoso
```

## Issue your first query

Here is a basic example of how to use pyoso:

```python
from pyoso import Client

# Initialize the client
os.environ["OSO_API_KEY"] = 'your_api_key'
client = Client()

# Fetch artifacts
query = "SELECT * FROM artifacts_v1 LIMIT 5"
artifacts = client.to_pandas(query)

print(artifacts)
```
