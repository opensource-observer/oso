import inspect
import logging
import typing as t
from dataclasses import dataclass, field

from dagster import (
    AssetChecksDefinition,
    AssetsDefinition,
    AssetSpec,
    JobDefinition,
    SensorDefinition,
    SourceAsset,
)
from dagster._core.definitions.asset_dep import CoercibleToAssetDep
from dagster._core.definitions.asset_key import CoercibleToAssetKeyPrefix

# This import is fragile but it can't be helped for the current typing.
# Continuous deployment will have to save us here.
from dagster._core.definitions.cacheable_assets import CacheableAssetsDefinition
from dagster._core.definitions.unresolved_asset_job_definition import (
    UnresolvedAssetJobDefinition,
)
from oso_dagster.config import DagsterConfig

type GenericAsset = t.Union[
    AssetsDefinition, SourceAsset, CacheableAssetsDefinition, AssetSpec
]
type NonCacheableAssetsDefinition = t.Union[AssetsDefinition, SourceAsset]
type AssetList = t.Iterable[GenericAsset]
type AssetDeps = t.Iterable[CoercibleToAssetDep]
type AssetKeyPrefixParam = CoercibleToAssetKeyPrefix
type FactoryJobDefinition = JobDefinition | UnresolvedAssetJobDefinition

logger = logging.getLogger(__name__)


class GenericGCSAsset:
    def clean_up(self):
        raise NotImplementedError()

    def sync(self):
        raise NotImplementedError()


@dataclass
class AssetFactoryResponse:
    assets: AssetList
    sensors: t.List[SensorDefinition] = field(default_factory=lambda: [])
    jobs: t.List[FactoryJobDefinition] = field(default_factory=lambda: [])
    checks: t.List[AssetChecksDefinition] = field(default_factory=lambda: [])

    def __add__(self, other: "AssetFactoryResponse") -> "AssetFactoryResponse":
        return AssetFactoryResponse(
            assets=list(self.assets) + list(other.assets),
            sensors=list(self.sensors) + list(other.sensors),
            checks=list(self.checks) + list(other.checks),
            jobs=list(self.jobs) + list(other.jobs),
        )

    def filter_assets(
        self, f: t.Callable[[NonCacheableAssetsDefinition], bool]
    ) -> t.Iterable[NonCacheableAssetsDefinition]:
        """Due to limitations of docs on CacheableAssetsDefinitions, we filter
        out any CacheableAssetsDefinitions as they cannot be compared against
        for filtering"""
        no_cacheable_assets = t.cast(
            t.List[NonCacheableAssetsDefinition],
            filter(lambda a: not isinstance(a, CacheableAssetsDefinition), self.assets),
        )
        return filter(f, no_cacheable_assets)

    def filter_assets_by_name(self, name: str):
        """The asset "name" in this context is the final part of the asset key."""
        filtered = self.filter_assets(lambda a: a.key.path[-1] == name)
        return filtered

    def find_job_by_name(
        self, name: str
    ) -> t.Optional[t.Union[JobDefinition, UnresolvedAssetJobDefinition]]:
        return next((job for job in self.jobs if job.name == name), None)


type EarlyResourcesAssetDecoratedFunction[**P] = t.Callable[
    P, AssetFactoryResponse | AssetsDefinition
]


class EarlyResourcesAssetFactory:
    """Defines an asset factory that requires some resources upon starting. This
    is most useful for asset factories that require some form of secret and use
    the secret resolver."""

    def __init__(
        self,
        f: EarlyResourcesAssetDecoratedFunction,
        caller: t.Optional[inspect.FrameInfo] = None,
        additional_annotations: t.Optional[t.Dict[str, t.Any]] = None,
        dependencies: t.Optional[t.List["EarlyResourcesAssetFactory"]] = None,
    ):
        self._f = f
        self._caller = caller
        self.additional_annotations = additional_annotations or {}
        self._dependencies = dependencies or []

    def __call__(
        self, dependencies: t.List[AssetFactoryResponse], **early_resources
    ) -> AssetFactoryResponse:
        annotations = self._f.__annotations__.copy()
        annotations.update(self.additional_annotations)
        early_resources["dependencies"] = dependencies
        global_config = t.cast(DagsterConfig, early_resources.get("global_config"))
        assert (
            global_config is not None
        ), "global_config is required for early resources"
        args: t.Dict[str, t.Any] = dict()
        for key, value in annotations.items():
            if key == "return":
                continue
            if key not in early_resources:
                raise Exception(
                    f"Failed to set early resource '{key}' for type {repr(value)}"
                )
            args[key] = early_resources[key]

        try:
            res = self._f(**args)
        except Exception:
            if self._caller:
                logger.error(
                    f"Skipping failed asset factories from {self._caller.filename}",
                    exc_info=global_config.verbose_logs,
                )
            else:
                logger.error(
                    f"Skipping failed asset factories from {self._f.__module__}.{self._f.__name__}",
                    exc_info=global_config.verbose_logs,
                )
            return AssetFactoryResponse(assets=[])

        if isinstance(res, AssetFactoryResponse):
            return res
        elif isinstance(res, AssetsDefinition):
            return AssetFactoryResponse(assets=[res])
        else:
            raise Exception("Invalid early resource factory")

    @property
    def dependencies(self):
        return self._dependencies[:]


def early_resources_asset_factory(
    *,
    caller_depth: int = 1,
    additional_annotations: t.Optional[t.Dict[str, t.Any]] = None,
    dependencies: t.Optional[t.List[EarlyResourcesAssetFactory]] = None,
):
    caller = inspect.stack()[caller_depth]

    def _decorator(f: EarlyResourcesAssetDecoratedFunction):
        return EarlyResourcesAssetFactory(
            f,
            caller=caller,
            additional_annotations=additional_annotations,
            dependencies=dependencies,
        )

    return _decorator
