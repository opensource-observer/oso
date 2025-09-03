from dagster import (
    AssetExecutionContext,
    DynamicPartitionsDefinition,
    SensorEvaluationContext,
    SkipReason,
    sensor,
)
from dlt.sources.rest_api import rest_api_resources
from dlt.sources.rest_api.typing import RESTAPIConfig
from oso_dagster.factories import (
    AssetFactoryResponse,
    dlt_factory,
    early_resources_asset_factory,
)
from oso_dagster.resources import PostgresResource
from oso_dagster.utils import (
    ReplicationType,
    get_credentials,
    get_dynamic_replication,
    get_dynamic_replications_partition_for_type,
    parse_partition_key,
    sync_dynamic_partitions,
)
from oso_dagster.utils.secrets import SecretResolver

# Define a dynamic partitions definition.
# The partitions will be the IDs of the replication configurations.
rest_api_partitions = DynamicPartitionsDefinition(name="dynamic_rest_api")


# Use the dlt_factory to create a partitioned asset.
# The asset will be named 'replication' and have a key_prefix of 'dynamic_rest_api'.
# The job created by this factory will be named 'dynamic_rest_api_replication_job'.
@dlt_factory(
    key_prefix="dynamic",
    name="rest_api",
    partitions_def=rest_api_partitions,
    dataset_name=lambda ctx: parse_partition_key(ctx.partition_key)[0],
    log_intermediate_results=True,
    use_dynamic_project=True,
)
def dynamic_rest_asset(
    context: AssetExecutionContext,
    oso_app_db: PostgresResource,
    secrets: SecretResolver,
):
    """
    A dynamic partitioned asset that uses dlt's rest_api source to replicate data.
    Each partition corresponds to a row in the dynamic_replications table.
    Credentials for the database and the REST APIs are resolved via Dagster's
    SecretResolver resource, which is configured to use GCP Secret Manager.
    """
    with oso_app_db.get_connection() as conn:
        dynamic_replication = get_dynamic_replication(conn, context.partition_key)

    rest_api_config: RESTAPIConfig = dynamic_replication.config

    credentials = get_credentials(secrets, dynamic_replication.credentials_path)
    # If credentials_path is provided, resolve it as a secret and add it to the config
    if credentials:
        client = rest_api_config.setdefault("client", {}) or {}
        client["auth"] = credentials

    resources = rest_api_resources(rest_api_config)

    for resource in resources:
        resource.table_name = f"{dynamic_replication.name}_{resource.name}"

    # Create the dlt source
    yield from resources


@early_resources_asset_factory()
def create_rest_api_sensor():
    # A sensor to dynamically sync partitions based on the database state.
    @sensor(minimum_interval_seconds=1 * 60 * 60)
    def rest_api_sensor(
        context: SensorEvaluationContext,
        oso_app_db: PostgresResource,
    ):
        """
        A sensor that queries the dynamic_replications table to find new, updated,
        or removed replication configurations and updates Dagster partitions accordingly.
        """
        with oso_app_db.get_connection() as conn:
            all_partition_keys = get_dynamic_replications_partition_for_type(
                conn, ReplicationType.REST
            )

        sync_dynamic_partitions(
            context,
            rest_api_partitions,
            all_partition_keys,
        )

        return SkipReason("Synced dynamic REST API partitions")

    return AssetFactoryResponse(assets=[], sensors=[rest_api_sensor])
