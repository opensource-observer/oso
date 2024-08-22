import os
import json
from pathlib import Path
from typing import Dict, List
import uuid
from ..constants import main_dbt_manifests, staging_bucket, PRODUCTION_DBT_TARGET
from dagster import AssetKey
from ..factories import (
    create_bq2clickhouse_asset,
    Bq2ClickhouseAssetConfig,
)
from ..factories.common import AssetFactoryResponse
from ..utils.bq import BigQueryTableConfig
from ..utils.common import SourceMode

MART_DIRECTORY = "marts"
INTERMEDIATE_DIRECTORY = "intermediate"
SYNC_KEY = "sync_to_db"


def clickhouse_assets_from_manifests_map(
    manifests: Dict[str, Path],
) -> AssetFactoryResponse:
    """Creates all Dagster assets from a map of manifests

    Parameters
    ----------
    manifests: Dict[str, Path]
        Result from `load_dbt_manifests()`
        dbt_target => manifest_path

    Returns
    -------
    AssetsFactoryResponse
        a list of Dagster assets
    """

    # We only care about mart models from production
    if PRODUCTION_DBT_TARGET not in manifests:
        raise Exception(
            f"Expected {PRODUCTION_DBT_TARGET} in dbt manifests({manifests.keys()})"
        )

    # Load the manifest
    manifest_path = manifests[PRODUCTION_DBT_TARGET]
    if not os.path.isfile(manifest_path):
        raise Exception(f"{manifest_path} does not exist")
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
        if "nodes" not in manifest:
            raise Exception(f"Expected nodes in {manifest_path}")
        nodes = manifest["nodes"].values()
        # Get manifests of mart models to copy
        marts = list(filter(lambda n: MART_DIRECTORY in n.get("fqn"), nodes))

        # TEMPORARY HACKY CHANGE TO GET INT_EVENTS COPIED TO CLICKHOUSE
        intermediates = list(
            filter(lambda n: INTERMEDIATE_DIRECTORY in n.get("fqn"), nodes)
        )
        marts.extend(intermediates)

        copied_mart_names: List[str] = []
        skipped_mart_names: List[str] = []
        result = AssetFactoryResponse([])
        for n in marts:
            table_name = n.get("name")
            # Only copy marts that are marked for sync
            if n.get("meta").get(SYNC_KEY, False):
                print(f"Queuing {table_name}")
                copied_mart_names.append(table_name)
                # Create an asset for each mart to copy
                result = result + create_bq2clickhouse_asset(
                    Bq2ClickhouseAssetConfig(
                        key_prefix="clickhouse",
                        asset_name=table_name,
                        deps=[AssetKey(["dbt", "production", table_name])],
                        sync_id=str(uuid.uuid4()),
                        source_config=BigQueryTableConfig(
                            project_id=n.get("database"),
                            dataset_name=n.get("schema"),
                            table_name=table_name,
                            service_account=None,
                        ),
                        staging_bucket=staging_bucket,
                        destination_table_name=table_name,
                        index=n.get("meta").get("index"),
                        order_by=n.get("meta").get("order_by"),
                        copy_mode=SourceMode.Overwrite,
                    ),
                )
            # Track which marts were skipped
            else:
                skipped_mart_names.append(table_name)
        print(
            f"...queued {str(len(copied_mart_names))} marts, skipping {str(len(skipped_mart_names))}"
        )
        # print(skipped_mart_names)
        return result


all_clickhouse_dbt_mart_assets = clickhouse_assets_from_manifests_map(
    main_dbt_manifests
)
