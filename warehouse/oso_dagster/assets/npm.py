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
    response = requests.get(endpoint, timeout=10)

    if not response.ok:
        if response.status_code == 400 and "end date > start date" in response.text:
            yield None

        raise ValueError(
            f"Failed to fetch data for {
                package_name}: {response.text}"
        )

    data = response.json()

    if data["package"] != package_name:
        raise ValueError(
            f"Unexpected package name: {data['package']} != {package_name}"
        )

    days_between = [
        date_from + timedelta(days=i) for i in range((date_to - date_from).days + 1)
    ]

    for download in data["downloads"]:
        date_day = datetime.strptime(download["day"], "%Y-%m-%d")

        if date_day not in days_between:
            raise ValueError(
                f"Unexpected date for {package_name}: {date_day.strftime('%Y-%m-%d')} not in "
                f"{days_between[0].strftime('%Y-%m-%d')} => {days_between[-1].strftime('%Y-%m-%d')}"
            )

        days_between.remove(date_day)

        yield NPMPackageInfo(
            date=date_day,
            artifact_name=package_name,
            downloads=download["downloads"],
        )

    if len(days_between) > 0:
        raise ValueError(
            f"Missing data for {package_name} between {date_from} and {date_to}: {
                ", ".join(str(day) for day in days_between)
            }"
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
    end = start + timedelta(weeks=1)

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
