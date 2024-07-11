import logging
import inspect
from typing import List, Iterable, Union, Callable, Any, Dict, Optional
from dataclasses import dataclass, field

from dagster import (
    SensorDefinition,
    AssetsDefinition,
    JobDefinition,
    AssetChecksDefinition,
    SourceAsset,
)

# This import is fragile but it can't be helped for the current typing.
# Continuous deployment will have to save us here.
from dagster._core.definitions.cacheable_assets import CacheableAssetsDefinition
from dagster._core.definitions.asset_dep import CoercibleToAssetDep

type GenericAsset = Union[AssetsDefinition, SourceAsset, CacheableAssetsDefinition]
type AssetList = Iterable[GenericAsset]
type AssetDeps = Iterable[CoercibleToAssetDep]

logger = logging.getLogger(__name__)


class GenericGCSAsset:
    def clean_up(self):
        raise NotImplementedError()

    def sync(self):
        raise NotImplementedError()


@dataclass
class AssetFactoryResponse:
    assets: AssetList
    sensors: List[SensorDefinition] = field(default_factory=lambda: [])
    jobs: List[JobDefinition] = field(default_factory=lambda: [])
    checks: List[AssetChecksDefinition] = field(default_factory=lambda: [])

    def __add__(self, other: "AssetFactoryResponse") -> "AssetFactoryResponse":
        return AssetFactoryResponse(
            assets=list(self.assets) + list(other.assets),
            sensors=list(self.sensors) + list(other.sensors),
            checks=list(self.checks) + list(other.checks),
            jobs=list(self.jobs) + list(other.jobs),
        )


type EarlyResourcesAssetDecoratedFunction[**P] = Callable[
    P, AssetFactoryResponse | AssetsDefinition
]


class EarlyResourcesAssetFactory:
    """Defines an asset factory that requires some resources upon starting. This
    is most useful for asset factories that require some form of secret and use
    the secret resolver."""

    def __init__(
        self,
        f: EarlyResourcesAssetDecoratedFunction,
        caller: Optional[inspect.FrameInfo] = None,
    ):
        self._f = f
        self._caller = caller

    def __call__(self, **early_resources) -> AssetFactoryResponse:
        annotations = self._f.__annotations__
        args: Dict[str, Any] = dict()
        for key, value in annotations.items():
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
                    f"Skipping failed asset factories from {self._caller.filename}"
                )
            else:
                logger.error(
                    f"Skipping failed asset factories from {self._f.__module__}.{self._f.__name__}"
                )
            return AssetFactoryResponse(assets=[])

        if isinstance(res, AssetFactoryResponse):
            return res
        elif isinstance(res, AssetsDefinition):
            return AssetFactoryResponse(assets=[res])
        else:
            raise Exception("Invalid early resource factory")


def early_resources_asset_factory(*, caller_depth: int = 1):
    caller = inspect.stack()[caller_depth]

    def _decorator(f: EarlyResourcesAssetDecoratedFunction):
        return EarlyResourcesAssetFactory(f, caller=caller)

    return _decorator
