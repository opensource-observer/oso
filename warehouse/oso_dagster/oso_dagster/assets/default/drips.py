from typing import Any, Dict, List

import dlt
import polars as pl
import requests
from dagster import AssetExecutionContext, AssetIn, asset
from oso_dagster.config import DagsterConfig
from oso_dagster.factories.dlt import dlt_factory
from oso_dagster.factories.graphql import (
    GraphQLResourceConfig,
    RetryConfig,
    graphql_factory,
)

DRIPS_REST_API = "https://rpgf-api.drips.network"
DRIPS_GRAPHQL_API = "https://drips-multichain-api-staging.up.railway.app/graphql"
FIL_RPGF_3_ROUND_ID = "a4d12d71-37a2-45c7-b823-3389637ec03c"


def fetch_applications_rest(
    context: AssetExecutionContext, round_id: str
) -> List[Dict[str, Any]]:
    """Fetch all applications from REST API with pagination. Raises on any error."""
    all_apps = []
    offset = 0
    limit = 500

    while True:
        url = f"{DRIPS_REST_API}/api/rounds/{round_id}/applications"
        params = {"limit": limit, "offset": offset}

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        apps = response.json()

        if not isinstance(apps, list):
            raise ValueError(
                f"Expected list response at offset {offset}, got {type(apps)}"
            )

        if not apps:
            break

        all_apps.extend(apps)

        if len(apps) < limit:
            break

        offset += limit

    context.log.info(f"Successfully fetched {len(all_apps)} applications")
    return all_apps


def fetch_application_details(
    round_id: str, application_id: str
) -> Dict[str, Any] | None:
    """Fetch full application details including dripsAccountId."""
    url = f"{DRIPS_REST_API}/api/rounds/{round_id}/applications/{application_id}"

    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


@asset(key_prefix="drips", compute_kind="dataframe")
def applications_df(context: AssetExecutionContext) -> pl.DataFrame:
    """Fetch all Filecoin RPGF round 3 applications with full details from REST API."""
    context.log.info(f"Fetching applications list for round {FIL_RPGF_3_ROUND_ID}")
    apps = fetch_applications_rest(context, FIL_RPGF_3_ROUND_ID)
    context.log.info(f"Fetched {len(apps)} applications, now fetching full details...")

    data = []
    for idx, app in enumerate(apps):
        app_id = app.get("id")
        if not app_id:
            continue

        if idx > 0 and idx % 10 == 0:
            context.log.info(f"Fetched details for {idx}/{len(apps)} applications")

        full_app = fetch_application_details(FIL_RPGF_3_ROUND_ID, app_id)
        if not full_app:
            continue

        drips_account_id = full_app.get("latestVersion", {}).get("dripsAccountId")

        if drips_account_id:
            data.append(full_app)
        else:
            context.log.warning(f"No dripsAccountId found for application {app_id}")

    context.log.info(
        f"Successfully processed {len(data)} applications with dripsAccountId"
    )
    return pl.DataFrame(data)


applications_df_key = applications_df.key


def project_details_by_account_id(
    context: AssetExecutionContext, global_config: DagsterConfig, data: Dict[str, Any]
):
    """Fetch full project details from GraphQL API for a given dripsAccountId."""

    def add_metadata(result: Dict[str, Any]) -> Dict[str, Any]:
        """Add application ID to enable joining with REST data."""
        project = result["projectById"]
        project["applicationId"] = data["id"]
        return project

    config = GraphQLResourceConfig(
        name=f"project_{data['id'].replace('-', '_')}",
        endpoint=DRIPS_GRAPHQL_API,
        target_type="Query",
        target_query="projectById",
        parameters={
            "id": {"type": "ID!", "value": data["latestVersion"]["dripsAccountId"]},
            "chains": {
                "type": "[SupportedChain!]",
                "value": ["FILECOIN"],
            },
        },
        transform_fn=add_metadata,
        max_depth=5,
        retry=RetryConfig(
            max_retries=3,
            initial_delay=1.0,
            max_delay=10.0,
            backoff_multiplier=2.0,
            jitter=True,
        ),
    )
    resource = graphql_factory(config, global_config, context)
    yield from resource()


# how much each project got and when did they get it


@dlt_factory(key_prefix="drips", ins={"apps_df": AssetIn(applications_df_key)})
def rpgf_applications(
    context: AssetExecutionContext,
    global_config: DagsterConfig,
    apps_df: pl.DataFrame,
):
    """Fetch detailed project information for RPGF applications using GraphQL."""

    @dlt.resource(
        name="rpgf_applications", write_disposition="replace", max_table_nesting=0
    )
    def fetch_details():
        apps = apps_df.to_dicts()
        context.log.info(f"Fetching GraphQL details for {len(apps)} applications")

        for app in apps:
            yield from project_details_by_account_id(context, global_config, app)

    yield fetch_details()
