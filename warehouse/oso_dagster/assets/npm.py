from datetime import datetime, timedelta
from typing import Generator, List, Optional

import dlt
import requests
from dagster import AssetExecutionContext
from pydantic import BaseModel

from ..factories.dlt import pydantic_to_dlt_nullable_columns

# Host for the NPM registry
NPM_HOST = "https://api.npmjs.org"


class NPMPackageInfo(BaseModel):
    date: datetime
    name: str
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

        raise ValueError(f"Failed to fetch data for {package_name}: {response.text}")

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
                f"Unexpected date for {package_name}: {date_day} not in {days_between}"
            )

        days_between.remove(date_day)

        yield NPMPackageInfo(
            date=date_day,
            name=package_name,
            downloads=download["downloads"],
        )

    if len(days_between) > 0:
        raise ValueError(
            f"Missing data for {package_name} between {date_from} and {date_to}: {
                ", ".join(str(day) for day in days_between)
            }"
        )


@dlt.resource(
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

    Example:
        ```python
        # NPM was launched on January 12, 2010
        NPM_EPOCH = "2010-01-12T00:00:00Z"

        @dlt_factory(
            key_prefix="npm",
            partitions_def=WeeklyPartitionsDefinition(
                start_date=NPM_EPOCH.split("T", maxsplit=1)[0],
                end_offset=1,
            ),
        )
        def downloads(
            context: AssetExecutionContext,
        ):
            yield get_all_downloads(
                context,
                package_names=[
                    "@angular/core",
                    "react",
                    "vue",
                    # ...
                ],
            )
        ```
    """

    start = datetime.strptime(context.partition_key, "%Y-%m-%d")
    end = start + timedelta(weeks=1)

    yield from (
        get_npm_package_downloads(package_name, start, end)
        for package_name in package_names
    )
