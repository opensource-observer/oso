# pyright: ignore[reportPrivateImportUsage]
"""
This module is used to import internal Dagster packages that we rely on.

Some of these internals might _change_ in the future so we should try to avoid
using them if we can. This however allows us to consolidate the imports in one
place so we can control them, make changes, and/or fixes to these expected
imports if they change in the future.

To avoid some common issues with imports being reported by the pyright when
importing from this module, it is suggested to use this module like this:

    from oso_dagster.utils import dagsterinternals as dginternals

    def some_function(some_param: dginternals.CoercibleToAssetDep):
        ...

This way, you can use the types and classes from this module without
worrying about pyright errors and it also makes it _very_ clear that
you are using an internal dagster object/package/module/etc.
"""

from dagster._core.definitions.asset_dep import (
    CoercibleToAssetDep,  # pyright: ignore[reportPrivateImportUsage]
)
from dagster._core.definitions.asset_key import (
    CoercibleToAssetKeyPrefix,  # pyright: ignore[reportPrivateImportUsage]
)

# This import is fragile but it can't be helped for the current typing.
# Continuous deployment will have to save us here.
from dagster._core.definitions.cacheable_assets import (
    CacheableAssetsDefinition,  # pyright: ignore[reportPrivateImportUsage]
)
from dagster._core.definitions.unresolved_asset_job_definition import (
    UnresolvedAssetJobDefinition,  # pyright: ignore[reportPrivateImportUsage]
)
from dagster._core.events import (
    JobFailureData,  # pyright: ignore[reportPrivateImportUsage]
)

__all__ = [
    "CoercibleToAssetDep",
    "CoercibleToAssetKeyPrefix",
    "CacheableAssetsDefinition",
    "UnresolvedAssetJobDefinition",
    "JobFailureData",
]
