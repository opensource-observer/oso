from typing import List, Iterable, Union, Callable, Any, Dict
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


type EarlyResourcesAssetDecoratedFunction[**P] = Callable[
    P, AssetFactoryResponse | AssetsDefinition
]


class EarlyResourcesAssetFactory:
    """Defines an asset factory that requires some resources upon starting. This
    is most useful for asset factories that require some form of secret and use
    the secret resolver."""

    def __init__(self, f: EarlyResourcesAssetDecoratedFunction):
        self._f = f

    def __call__(self, **early_resources) -> AssetFactoryResponse:
        annotations = self._f.__annotations__
        args: Dict[str, Any] = dict()
        for key, value in annotations.items():
            if key not in early_resources:
                raise Exception(f"Failed to set early resource {key} or type {value}")
            args[key] = early_resources[key]

        res = self._f(**args)
        if isinstance(res, AssetFactoryResponse):
            return res
        elif isinstance(res, AssetsDefinition):
            return AssetFactoryResponse(assets=[res])
        else:
            raise Exception("Invalid early resource factory")


def early_resources_asset_factory(f: EarlyResourcesAssetDecoratedFunction):
    return EarlyResourcesAssetFactory(f)
