# Ingest Assets – Contribution Rules (Copilot & Humans)

## Scope

Create Dagster assets for:

- REST crawling
- GraphQL crawling
- DB replication (incremental)

All work is isolated to the ingest sandbox and must not modify production defs.

## Locations

- REST: `warehouse/oso_dagster/assets/ingest/rest/<provider>/<entity>_asset.py`
- GraphQL: `warehouse/oso_dagster/assets/ingest/graphql/<provider>/<entity>_asset.py`
- DB: `warehouse/oso_dagster/assets/ingest/db/<engine>/<table>_replication_asset.py`
- Registry: `warehouse/oso_dagster/assets/ingest/defs_sandbox.py` (import new modules here)

## Naming rules (pinned)

- All names are **lower_snake_case**.
- **File ⇄ Function** must match:
  - REST/GraphQL file: `<entity>_asset.py` → function: `fetch_<provider>_<entity>`
  - DB file: `<table>_replication_asset.py` → function: `replicate_<engine>_<table>`
- Asset groups:
  - REST → `group_name="rest_crawl"`
  - GraphQL → `group_name="graphql_crawl"`
  - DB → `group_name="db_replication"`
- Resources: always declare `required_resource_keys={"secret_resolver"}`.
- Secrets: `context.resources.secret_resolver.resolve_as_str(SecretReference(group_name="<group>", key="<key>"))`.
- Output: return the file path string and add metadata: `rows`, `path`.

## Minimal templates

### REST (with/without auth)

```python
from dagster import asset, AssetExecutionContext, MetadataValue
from warehouse.oso_dagster.utils.secrets import SecretReference
import requests, json, pathlib, datetime as dt, time

@asset(group_name="rest_crawl", required_resource_keys={"secret_resolver"})
def fetch_<provider>_<entity>(context: AssetExecutionContext) -> str:
    headers = {}
    # If auth required:
    # token = context.resources.secret_resolver.resolve_as_str(SecretReference(group_name="<provider>", key="api_key"))
    # headers = {"Authorization": f"Bearer {token}"}

    url = "<https://api.example.com/...>"
    params, items, cursor = {"limit": 100}, [], None
    while True:
        if cursor:
            params["after"] = cursor
        r = requests.get(url, headers=headers, params=params, timeout=60)
        if r.status_code == 429:
            time.sleep(2); continue
        r.raise_for_status()
        d = r.json()
        items += d.get("results", d if isinstance(d, list) else [])
        cursor = (d.get("paging") or {}).get("next", {}).get("after")
        if not cursor:
            break

    out = pathlib.Path("warehouse/oso_dagster/tmp/<provider>/<entity>")
    out.mkdir(parents=True, exist_ok=True)
    fp = out / f"{dt.date.today().isoformat()}.json"
    fp.write_text(json.dumps(items))
    context.add_output_metadata({"rows": MetadataValue.int(len(items)), "path": MetadataValue.path(str(fp))})
    return str(fp)

```
