import typing as t

from oso_dagster.factories.common import (
    AssetFactoryResponse,
    EarlyResourcesAssetFactory,
    FactoryJobDefinition,
    early_resources_asset_factory,
)


def discoverable_jobs(dependencies: t.Optional[t.List[t.Any]] = None):
    """A decorator for defining a set of automatically loaded jobs.

    This does this by generating an AssetFactoryResponse with the jobs
    configured. This is useful if you need to create jobs that span multiple
    assets that aren't all created from a single factory"""
    dependencies = dependencies or []
    for dep in dependencies:
        assert isinstance(dep, EarlyResourcesAssetFactory)

    def _decorated(f: t.Callable[..., t.Iterable[FactoryJobDefinition]]):
        @early_resources_asset_factory(caller_depth=2, dependencies=dependencies)
        def _jobs(dependencies: t.List[AssetFactoryResponse]):
            if dependencies:
                jobs = list(f(dependencies=dependencies))
            else:
                jobs = list(f())
            return AssetFactoryResponse(assets=[], jobs=jobs)

        return _jobs

    return _decorated
