from datetime import datetime, timedelta
from typing import Generator, List, Optional

import dlt
import requests
from dagster import AssetExecutionContext, AssetKey, WeeklyPartitionsDefinition
from oso_dagster.cbt.cbt import CBTResource
from pydantic import BaseModel

from ..factories.dlt import dlt_factory, pydantic_to_dlt_nullable_columns

# Host for the NPM registry
NPM_HOST = "https://api.npmjs.org"

# NPM was launched on January 12, 2010
NPM_EPOCH = "2010-01-12T00:00:00Z"


class NPMPackageInfo(BaseModel):
    date: datetime
    artifact_name: str
    downloads: int


def get_npm_package_downloads(
    package_name: str, date_from: datetime, date_to: datetime
) -> Generator[Optional[NPMPackageInfo], None, None]:
    """
    Fetches the download count for an NPM package between two dates.

    Args:
        package_name (str): The NPM package name
        date_from (datetime): The start date
        date_to (datetime): The end date

    Yields:
        Optional[NPMPackageInfo]: The download count for the package
    """

    str_from = date_from.strftime("%Y-%m-%d")
    str_to = date_to.strftime("%Y-%m-%d")

    endpoint = f"{NPM_HOST}/downloads/range/{str_from}:{str_to}/{package_name}"
    response = requests.get(
        endpoint,
        timeout=10,
        headers={
            "X-URL": "https://github.com/opensource-observer/oso",
            "X-Contact": "ops@karibalabs.co",
            "X-Purpose": "We are currently indexing NPM packages to provide download statistics. "
            "If you have any questions or concerns, please contact us",
        },
    )

    data = response.json()

    if not response.ok:
        if data["error"] == "end date > start date":
            return
        raise ValueError(f"Failed to fetch data for {package_name}: {response.text}")

    if data["package"] != package_name:
        raise ValueError(
            f"Unexpected package name: {data['package']} != {package_name}"
        )

    days_between = [
        (date_from + timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range((date_to - date_from).days + 1)
    ]

    for download in data["downloads"]:
        date_day = download["day"]

        if date_day not in days_between:
            raise ValueError(
                f"Unexpected date for {package_name}: {date_day} not in {str_from} => {str_to}"
            )

        days_between.remove(date_day)

    if len(days_between) > 0:
        raise ValueError(
            f"Missing data for {package_name} between {date_from} and {date_to}: {
                ", ".join(str(day) for day in days_between)
            }"
        )

    total_downloads = sum(download["downloads"] for download in data["downloads"])

    yield (
        NPMPackageInfo(
            date=date_from,
            artifact_name=package_name,
            downloads=total_downloads,
        )
        if total_downloads > 0
        else None
    )


@dlt.resource(
    primary_key="artifact_name",
    name="downloads",
    columns=pydantic_to_dlt_nullable_columns(NPMPackageInfo),
)
def get_all_downloads(
    context: AssetExecutionContext,
    package_names: List[str],
):
    """
    Fetches the download count for a list of NPM packages for the week
    starting on the partition key date.

    Args:
        context (AssetExecutionContext): The asset execution
        package_names (List[str]): List of NPM package names to fetch

    Yields:
        List[NPMPackageInfo]: The download count for each package
    """

    start = datetime.strptime(context.partition_key, "%Y-%m-%d")
    end = start + timedelta(days=6)

    context.log.info(
        f"Processing NPM downloads for {len(package_names)} packages "
        f"between {start.strftime('%Y-%m-%d')} and {end.strftime('%Y-%m-%d')}"
    )

    yield from (
        get_npm_package_downloads(package_name, start, end)
        for package_name in package_names
    )


@dlt_factory(
    key_prefix="npm",
    partitions_def=WeeklyPartitionsDefinition(
        start_date=NPM_EPOCH.split("T", maxsplit=1)[0],
        end_offset=1,
    ),
    deps=[AssetKey(["dbt", "production", "artifacts_v1"])],
)
def downloads(
    context: AssetExecutionContext,
    cbt: CBTResource,
):
    unique_artifacts_query = """
        SELECT
          DISTINCT(artifact_name)
        FROM
          `oso.artifacts_v1`
        WHERE
          artifact_source = "NPM"
    """

    client = cbt.get(context.log)

    yield get_all_downloads(
        context,
        package_names=[
            row["artifact_name"]
            for row in client.query_with_string(unique_artifacts_query)
        ],
    )
