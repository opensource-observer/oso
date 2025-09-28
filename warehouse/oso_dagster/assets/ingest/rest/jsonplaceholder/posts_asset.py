import datetime as dt
import json
import pathlib

import requests
from dagster import AssetExecutionContext, MetadataValue, asset


@asset(group_name="rest_crawl")
def fetch_jsonplaceholder_posts(context: AssetExecutionContext) -> str:
    url = "https://jsonplaceholder.typicode.com/posts"
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    data = r.json()

    out = pathlib.Path("warehouse/oso_dagster/tmp/jsonplaceholder/posts")
    out.mkdir(parents=True, exist_ok=True)
    fp = out / f"{dt.date.today().isoformat()}.json"
    fp.write_text(json.dumps(data))

    context.add_output_metadata(
        {
            "rows": MetadataValue.int(len(data)),
            "path": MetadataValue.path(str(fp)),
        }
    )
    return str(fp)
