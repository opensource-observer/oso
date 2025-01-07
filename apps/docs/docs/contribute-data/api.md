---
title: Crawl an API
sidebar_position: 4
---

## What Are We Trying to Achieve?

At OSO, many teams need to connect a public API to their pipelines so the data
can be analyzed, shared, or enriched further. Doing this in a consistent,
reliable way can be tricky if you have to manually code each endpoint. Our
solution is to use a configuration object that defines all your endpoints, then
let our pipeline handle the rest.

Here are a few reasons why this is helpful:

- **Minimal boilerplate**: All you do is list which endpoints you are pulling data
  from.
- **Automatic asset creation**: Each endpoint becomes its own asset, ready to be
  materialized in Dagster.
- **Easy integration with the OSO environment**: Everything is built to fit into our
  approach to data ingestion.

---

## Step by Step: Defining Your API Crawler

Below is a sample showing how you can ingest data from the
[DefiLlama](https://defillama.com/) API. It retrieves data on various DeFi
protocols such as Uniswap, Aave, etc.

### 1. List the Protocols

Pick the protocols you want. Each entry in this list represents one endpoint you
will fetch.

```python
DEFI_LLAMA_PROTOCOLS = [
    "aave-v1",
    "aave-v2",
    "aave-v3",
    "uniswap",
    "velodrome",
    "origin-protocol",
    # ...others...
]
```

### 2. Create a Configuration Object

:::tip
For the full `config` spec, see
[`dlt docs`](https://dlthub.com/docs/dlt-ecosystem/verified-sources/rest_api/basic).
The following is a simplified version of the config.
:::

The configuration object has three main parts:

- A `client` object, which contains the base URL and any other client-level
  settings.
- A `resource_defaults` object, which contains default settings for all
  resources.
- A list of `resources`, each describing a single endpoint, with a name and
  endpoint details.

```python
from dlt.sources.rest_api.typing import RESTAPIConfig

config: RESTAPIConfig = {
    "client": {
        "base_url": "https://api.llama.fi/"
    },
    "resource_defaults": {
        "primary_key": "id",
        "write_disposition": "merge",
    },
    "resources": [
        {
            "name": f"{protocol.replace('-', '_').replace(".", '__dot__')}_protocol",
            "endpoint": {
                "path": f"protocol/{protocol}",
                "data_selector": "$"
            }
        }
        for protocol in DEFI_LLAMA_PROTOCOLS
    ],
}
```

### 3. Use the Factory Function

We have a handy factory function called `create_rest_factory_asset` that takes
your configuration and returns a callable **factory**. The only thing left is to
call that factory with a `key_prefix` so OSO knows how to group these assets.

Under the hood, the returned `factory` will create a set of Dagster assets,
managing all of our infrastructure-specific details for you. Therefore, you can
easily configure all of them in one go. For the full reference, check
[`dagster asset documentation`](https://docs.dagster.io/_apidocs/assets#dagster.asset).

```python
from ..factories.rest import create_rest_factory_asset

# ... config definition ...

dlt_assets = create_rest_factory_asset(config=config)
defillama_tvl_assets = dlt_assets(key_prefix=["defillama", "tvl"])
```

That is it. These few lines produce a set of Dagster assets, each one pulling
data from a distinct DefiLlama endpoint. When you run your Dagster job or
pipeline, the data will be ingested into your OSO warehouse.

---

## How to Run and View Results

1. **Add Your Asset Code to OSO**\
   Put the snippet above in an appropriate location in your repository, for
   example, our `defillama` asset is located in `warehouse/oso_dagster/assets/defillama.py`.

2. **Run Dagster**\
   Simply start it up (`dagster dev`) and you will see assets for
   each protocol listed. Or schedule a job in your deployment that includes
   these assets.

3. **Verify Your Tables**\
   Once the assets have been materialized, check your database or data
   warehouse. Each endpoint you defined in the config will appear as a table.

---

## Expanding Your Crawler

In practice, you may do more than just retrieve data:

- **Pagination**: dlt supports adding a paginator if you have large result sets.
- **Transformations**: You can add transformations before loading, such as
  cleaning up invalid fields or renaming columns.

Our tooling is flexible enough to let you customize these details without losing
the simplicity of the factory approach.

---

## Conclusion

With just a few lines of code, you can connect OSO to any public API. This
method removes repetitive tasks and helps you maintain a consistent approach to
ingestion. Whenever you need to add or remove endpoints, you simply update your
configuration object.

**Happy data crawling!**
