import types
from typing import List
from dataclasses import dataclass, field

from dagster import SensorDefinition, AssetsDefinition, JobDefinition


class GenericGCSAsset:
    def clean_up(self):
        raise NotImplementedError()

    def sync(self):
        raise NotImplementedError()


@dataclass
class AssetFactoryResponse:
    assets: List[AssetsDefinition]
    sensors: List[SensorDefinition] = field(default_factory=lambda: [])
    jobs: List[JobDefinition] = field(default_factory=lambda: [])


def load_assets_factories_from_modules(
    modules: List[types.ModuleType],
) -> AssetFactoryResponse:
    assets: List[AssetsDefinition] = []
    sensors: List[SensorDefinition] = []
    jobs: List[JobDefinition] = []
    for module in modules:
        for _, obj in module.__dict__.items():
            if type(obj) == AssetFactoryResponse:
                assets.extend(obj.assets)
                sensors.extend(obj.sensors)
                jobs.extend(obj.jobs)
    return AssetFactoryResponse(assets=assets, sensors=sensors, jobs=jobs)
