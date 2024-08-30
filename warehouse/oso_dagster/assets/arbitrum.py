from oso_dagster.utils import unpack_config, gcs_to_bucket_name
from ..factories.goldsky.config import GoldskyNetworkConfig, NetworkAssetSourceConfig
from ..factories.goldsky.assets import goldsky_asset
from ..factories.common import early_resources_asset_factory, AssetFactoryResponse
from ..factories.goldsky.additional import (
    blocks_extensions,
    transactions_extensions,
)


@unpack_config(GoldskyNetworkConfig)
def arbitrum_assets(config: GoldskyNetworkConfig):
    """TODO THIS IS A COPY PASTE HACK TO HAVE EVERYTHING BUT THE TRANSACTIONS."""

    @early_resources_asset_factory(caller_depth=2)
    def _factory(project_id: str, staging_bucket: str):
        staging_bucket_name = gcs_to_bucket_name(staging_bucket)

        blocks_asset_config = NetworkAssetSourceConfig.with_defaults(
            NetworkAssetSourceConfig(
                source_name=f"{config.network_name}-blocks",
                partition_column_name="timestamp",
                partition_column_transform=lambda t: f"TIMESTAMP_SECONDS(`{t}`)",
                schema_overrides=[],
                external_reference="",
            ),
            config.blocks_config,
        )

        blocks = AssetFactoryResponse([])

        if config.blocks_enabled:
            blocks = goldsky_asset(
                key_prefix=config.network_name,
                name="blocks",
                source_name=blocks_asset_config.source_name,
                project_id=project_id,
                destination_table_name=f"{config.network_name}_blocks",
                working_destination_dataset_name=config.working_destination_dataset_name,
                destination_dataset_name=config.destination_dataset_name,
                partition_column_name=blocks_asset_config.partition_column_name,
                partition_column_transform=blocks_asset_config.partition_column_transform,
                source_bucket_name=staging_bucket_name,
                destination_bucket_name=staging_bucket_name,
                # uncomment the following value to test
                # max_objects_to_load=1,
                additional_factories=[blocks_extensions()],
            )
            blocks_table_fqn = f"{project_id}.{config.destination_dataset_name}.{config.network_name}_blocks"
        else:
            blocks_table_fqn = blocks_asset_config.external_reference

        transactions_asset_config = NetworkAssetSourceConfig.with_defaults(
            NetworkAssetSourceConfig(
                source_name=f"{config.network_name}-enriched_transactions",
                partition_column_name="block_timestamp",
                partition_column_transform=lambda t: f"TIMESTAMP_SECONDS(`{t}`)",
                schema_overrides=[{"name": "value", "field_type": "BYTES"}],
                external_reference="",
            ),
            config.transactions_config,
        )

        transactions = AssetFactoryResponse([])

        if config.transactions_enabled:
            assert (
                blocks_table_fqn != ""
            ), "blocks table location cannot be derived. must not be empty"

            transactions = goldsky_asset(
                key_prefix=config.network_name,
                name="transactions",
                source_name=transactions_asset_config.source_name,
                project_id=project_id,
                destination_table_name=f"{config.network_name}_transactions",
                working_destination_dataset_name=config.working_destination_dataset_name,
                destination_dataset_name=config.destination_dataset_name,
                partition_column_name=transactions_asset_config.partition_column_name,
                partition_column_transform=transactions_asset_config.partition_column_transform,
                schema_overrides=transactions_asset_config.schema_overrides,
                source_bucket_name=staging_bucket_name,
                destination_bucket_name=staging_bucket_name,
                # uncomment the following value to test
                # max_objects_to_load=1,
                deps=blocks.filter_assets_by_name("blocks"),
                additional_factories=[
                    # transactions_checks(blocks_table_fqn=blocks_table_fqn),
                    transactions_extensions(
                        blocks_table_fqn=blocks_table_fqn,
                    ),
                ],
            )

        traces_asset_config = NetworkAssetSourceConfig.with_defaults(
            NetworkAssetSourceConfig(
                source_name=f"{config.network_name}-traces",
                partition_column_name="block_timestamp",
                partition_column_transform=lambda t: f"TIMESTAMP_SECONDS(`{t}`)",
                schema_overrides=[],
                external_reference="",
            ),
            config.traces_config,
        )

        traces = AssetFactoryResponse([])

        if config.traces_enabled:
            # assert (
            #     transactions_table_fqn != ""
            # ), "transactions table cannot be derived. must not be empty"

            traces = goldsky_asset(
                key_prefix=config.network_name,
                name="traces",
                source_name=traces_asset_config.source_name,
                project_id=project_id,
                destination_table_name=f"{config.network_name}_traces",
                working_destination_dataset_name=config.working_destination_dataset_name,
                destination_dataset_name=config.destination_dataset_name,
                partition_column_name=traces_asset_config.partition_column_name,
                partition_column_transform=traces_asset_config.partition_column_transform,
                source_bucket_name=staging_bucket_name,
                destination_bucket_name=staging_bucket_name,
                # uncomment the following value to test
                # max_objects_to_load=1,
                deps=transactions.filter_assets_by_name("transactions"),
                additional_factories=[
                    # traces_checks(transactions_table_fqn=transactions_table_fqn),
                    # traces_extensions(transactions_table_fqn=transactions_table_fqn),
                ],
            )

        return blocks + transactions + traces

    return _factory


arbitrum_network = arbitrum_assets(
    network_name="arbitrum",
    destination_dataset_name="arbitrum",
    working_destination_dataset_name="oso_raw_sources",
    transactions_enabled=False,
)
