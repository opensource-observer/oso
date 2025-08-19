import click
from dotenv import load_dotenv
from oso_dagster.config import DagsterConfig
from oso_dagster.factories.common import ResourcesContext, resource_factory
from oso_dagster.factories.loader import load_all_assets_from_package

load_dotenv()


@click.group()
def cli():
    pass


@cli.command("build")
def build():
    """Builds any early resources asset factories that have the `run_at_build`
    tag set to true."""

    from . import assets
    from .definitions.common import run_with_default_resources

    @resource_factory("global_config")
    def injected_dagster_config() -> DagsterConfig:
        return DagsterConfig(
            run_mode="build",
        )

    def run_build(resources: ResourcesContext):
        load_all_assets_from_package(
            assets, resources, include_tags={"run_at_build": "true"}
        )

    run_with_default_resources(run_build, override_resources=[injected_dagster_config])


if __name__ == "__main__":
    cli()
