import datetime as dt
import json
import pathlib

import requests
from dagster import AssetExecutionContext, MetadataValue, asset


@asset(group_name="graphql_crawl")
def fetch_countries_countries(context: AssetExecutionContext) -> str:
    url = "https://countries.trevorblades.com/"
    q = """
    query {
      countries { code name capital }
    }
    """
    r = requests.post(url, json={"query": q}, timeout=60)
    r.raise_for_status()
    data = r.json()["data"]["countries"]

    out = pathlib.Path("warehouse/oso_dagster/tmp/countries/countries")
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
