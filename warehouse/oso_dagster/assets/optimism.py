from ..factories.goldsky import goldsky_asset, traces_checks, traces_extensions
from ..constants import staging_bucket
from oso_dagster.utils import gcs_to_bucket_name


transactions_table_fqn = (
    "bigquery-public-data.goog_blockchain_optimism_mainnet_us.transactions"
)
staging_bucket_name = gcs_to_bucket_name(staging_bucket)

optimism_traces = goldsky_asset(
    key_prefix="optimism",
    name="traces",
    source_name="optimism-traces",
    project_id="opensource-observer",
    destination_table_name="optimism_traces",
    working_destination_dataset_name="oso_raw_sources",
    destination_dataset_name="superchain",
    partition_column_name="block_timestamp",
    dedupe_model="optimism_dedupe.sql",
    source_bucket_name=staging_bucket_name,
    destination_bucket_name=staging_bucket_name,
    additional_factories=[
        traces_checks(
            transactions_table_fqn,
            transactions_transaction_hash_column_name="transaction_hash",
        ),
        traces_extensions(
            transactions_table_fqn=transactions_table_fqn,
            transactions_transaction_hash_column_name="transaction_hash",
        ),
    ],
    # uncomment the following value to test
    # max_objects_to_load=2000,
)
