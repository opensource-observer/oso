from datetime import datetime, timedelta
from typing import Any, Dict, Generator, List, Optional

import dlt
import requests
from dagster import AssetExecutionContext, AssetKey, WeeklyPartitionsDefinition
from oso_dagster.cbt.cbt import CBTResource
from pydantic import BaseModel

from ..factories.dlt import dlt_factory, pydantic_to_dlt_nullable_columns

# Host for the NPM API
NPM_API_HOST = "https://api.npmjs.org"

# Host for the NPM registry
NPM_REGISTRY_HOST = "https://registry.npmjs.org"

# https://github.com/npm/registry/blob/main/docs/download-counts.md#limits
NPM_EPOCH = "2015-01-10T00:00:00Z"


class NPMPackageDownloadInfo(BaseModel):
    date: datetime
    artifact_name: str
    downloads: int


class NPMPackageManifest(BaseModel):
    name: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    keywords: Optional[List] = None
    homepage: Optional[str] = None
    bugs: Optional[Dict] = None
    license: Optional[Dict] = None
    author: Optional[Dict] = None
    contributors: Optional[List] = None
    funding: Optional[List] = None
    files: Optional[List] = None
    exports: Optional[Dict] = None
    main: Optional[str] = None
    browser: Optional[Dict] = None
    bin: Optional[Dict] = None
    man: Optional[List] = None
    directories: Optional[Dict] = None
    repository: Optional[Dict] = None
    scripts: Optional[Dict] = None
    config: Optional[Dict] = None
    dependencies: Optional[Dict] = None
    devDependencies: Optional[Dict] = None
    peerDependencies: Optional[Dict] = None
    peerDependenciesMeta: Optional[Dict] = None
    bundleDependencies: Optional[List] = None
    optionalDependencies: Optional[Dict] = None
    overrides: Optional[Dict] = None
    engines: Optional[Dict] = None
    os: Optional[List] = None
    cpu: Optional[List] = None
    devEngines: Optional[Dict] = None
    private: Optional[bool] = None
    publishConfig: Optional[Dict] = None
    workspaces: Optional[List] = None


# Some fields in the NPM manifest are not always in the same format
# This dictionary contains the transformations to apply to the data
# before creating the manifest object
TRANSFORMATIONS = {
    "bugs": lambda value: {"url": value} if isinstance(value, str) else value,
    "license": lambda value: {"type": value} if isinstance(value, str) else value,
    "author": lambda value: {"author": value} if isinstance(value, str) else value,
    "funding": lambda value: (
        [{"type": "url", "url": value}]
        if isinstance(value, str)
        else [value]
        if isinstance(value, dict)
        else value
    ),
    "exports": lambda value: {".": value} if isinstance(value, str) else value,
    "bin": lambda value: {"path": value} if isinstance(value, str) else value,
    "man": lambda value: [value] if isinstance(value, str) else value,
    "browser": lambda value: (
        {"browser": value} if isinstance(value, (str, bool)) else value
    ),
    "repository": lambda value: {"url": value} if isinstance(value, str) else value,
}


def flatten_manifest(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Applies transformations to the data before creating the manifest object.

    Args:
        data (Dict[str, Any]): The data to transform

    Returns:
        Dict[str, Any]: The transformed data
    """

    for key, transform in TRANSFORMATIONS.items():
        if key in data:
            data[key] = transform(data[key])
    return data


def get_npm_package_downloads(
    package_name: str, date_from: datetime, date_to: datetime
) -> Generator[Optional[NPMPackageDownloadInfo], None, None]:
    """
    Fetches the download count for an NPM package between two dates.

    Args:
        package_name (str): The NPM package name
        date_from (datetime): The start date
        date_to (datetime): The end date

    Yields:
        Optional[NPMPackageDownloadInfo]: The download count for the package
    """

    str_from = date_from.strftime("%Y-%m-%d")
    str_to = date_to.strftime("%Y-%m-%d")

    endpoint = f"{NPM_API_HOST}/downloads/range/{str_from}:{str_to}/{package_name}"
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
                ', '.join(str(day) for day in days_between)
            }"
        )

    total_downloads = sum(download["downloads"] for download in data["downloads"])

    yield (
        NPMPackageDownloadInfo(
            date=date_from,
            artifact_name=package_name,
            downloads=total_downloads,
        )
        if total_downloads > 0
        else None
    )


def get_npm_package_manifest(
    package_name: str,
) -> Generator[Optional[NPMPackageManifest], None, None]:
    """
    Fetches the manifest for an NPM package.

    Args:
        context (AssetExecutionContext): The asset execution context
        package_name (str): The NPM package name

    Yields:
        Optional[NPMPackageManifest]: The manifest for the package
    """

    endpoint = f"{NPM_REGISTRY_HOST}/{package_name}/latest"
    response = requests.get(
        endpoint,
        timeout=10,
        headers={
            "X-URL": "https://github.com/opensource-observer/oso",
            "X-Contact": "ops@karibalabs.co",
            "X-Purpose": "We are currently indexing NPM packages to provide dependency statistics. "
            "If you have any questions or concerns, please contact us",
        },
    )

    data = response.json()

    if not response.ok:
        raise ValueError(f"Failed to fetch data for {package_name}: {response.text}")

    yield NPMPackageManifest(**flatten_manifest(data))


@dlt.resource(
    primary_key="artifact_name",
    name="downloads",
    columns=pydantic_to_dlt_nullable_columns(NPMPackageDownloadInfo),
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
        List[NPMPackageDownloadInfo]: The download count for each package
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


@dlt.resource(
    primary_key="name",
    name="manifests",
    columns=pydantic_to_dlt_nullable_columns(NPMPackageManifest),
)
def get_all_manifests(
    context: AssetExecutionContext,
    package_names: List,
):
    """
    Fetches the manifest for a list of NPM packages.

    Args:
        context (AssetExecutionContext): The asset execution
        package_names (List): List of NPM package names to fetch

    Yields:
        List[NPMPackageManifest]: The manifest for each package
    """

    context.log.info(f"Processing NPM manifests for {len(package_names)} packages")

    yield from (
        get_npm_package_manifest(package_name) for package_name in package_names
    )


@dlt_factory(
    key_prefix="npm",
    partitions_def=WeeklyPartitionsDefinition(
        start_date=NPM_EPOCH.split("T", maxsplit=1)[0],
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


@dlt_factory(
    key_prefix="npm",
    deps=[AssetKey(["dbt", "production", "artifacts_v1"])],
)
def manifests(
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

    yield get_all_manifests(
        context,
        package_names=[
            row["artifact_name"]
            for row in client.query_with_string(unique_artifacts_query)
        ],
    )
