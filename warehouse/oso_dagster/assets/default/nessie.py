from dagster import Config, RunConfig, asset, job
from oso_dagster.factories import AssetFactoryResponse, early_resources_asset_factory
from oso_dagster.resources import NessieResource


class NessieTagJobConfig(Config):
    # If provided, the `consumer` tag will be updated to point to this hash.
    # Defaults to the latest hash of `main`.
    to_hash: str = ""


default_config = RunConfig(ops={"nessie__assign_consumer_tag": NessieTagJobConfig()})


@early_resources_asset_factory()
def nessie_job() -> AssetFactoryResponse:
    @asset(key_prefix="nessie")
    def assign_consumer_tag(nessie: NessieResource, config: NessieTagJobConfig) -> None:
        client = nessie.get_client()
        main_ref = client.get_reference("main")
        consumer_ref = client.get_reference("consumer")

        to_hash = config.to_hash or main_ref.hash_
        client.assign_tag("consumer", main_ref.name, to_hash, consumer_ref.hash_)

    @job(config=default_config)
    def nessie_consumer_tag_job():
        assign_consumer_tag()

    return AssetFactoryResponse(
        assets=[assign_consumer_tag], jobs=[nessie_consumer_tag_job]
    )
