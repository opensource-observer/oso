"""Provide a way to cache dagster assets that are loaded with our factory utilities"""

import typing as t
from inspect import signature

import dagster as dg
from pydantic import BaseModel


class CacheableAssetOptions(BaseModel):
    """Derived from dg.asset.__annotations__

    For options that are not support by the cache, we set the type to None so
    that attempts to use them will fail at static type checking time.
    """

    name: str | None = None
    key_prefix: t.Union[str, t.Sequence[str]] | None = None
    ins: t.Mapping[str, dg.AssetIn] | None = None
    deps: t.Iterable[t.Union[dg.AssetKey, str, t.Sequence[str], dg.AssetDep]] | None = (
        None
    )
    metadata: t.Mapping[str, t.Any] | None = None
    tags: t.Mapping[str, str] | None = None
    description: str | None = None
    config_schema: t.Type[dg.Config] | None = None
    required_resource_keys: t.AbstractSet[str] | None = None
    resource_defs: t.Mapping[str, object] | None = None
    # hooks currently not supported. We set the type to None to force static type failure if used
    hooks: None = None
    io_manager_def: object | None = None
    io_manager_key: str | None = None
    # dagster_type currently not supported
    dagster_type: None = None
    # partitions_def currently not supported
    op_tags: t.Mapping[str, t.Any] | None = None
    group_name: str | None = None
    output_required: bool = False
    automation_condition: None = None
    freshness_policy: None = None
    backfill_policy: None = None
    retry_policy: None = None
    code_version: str | None = None
    key: t.Union[dg.AssetKey, str, t.Sequence[str]] | None = None
    check_specs: None = None
    owners: t.Sequence[str] | None = None
    kinds: t.AbstractSet[str] | None = None
    pool: str | None = None


class CacheableMultiAssetOptions(BaseModel):
    """Derived from dg.multi_asset.__annotations__

    For options that are not support by the cache, we set the type to None so
    that attempts to use them will fail at static type checking time.
    """

    name: str | None = None
    ins: t.Mapping[str, str] | None = None
    deps: t.Iterable[t.Union[str, t.Sequence[str]]] | None = None
    description: str | None = None
    config_schema: dg.Config | None = None
    required_resource_keys: t.AbstractSet[str] | None = None
    internal_asset_deps: t.Mapping[str, set[str]] | None = None
    backfill_policy: dg.BackfillPolicy | None = None
    op_tags: t.Mapping[str, t.Any] | None = None
    can_subset: bool = False
    resource_defs: t.Mapping[str, object] | None = None
    group_name: str | None = None
    retry_policy: dg.RetryPolicy | None = None
    code_version: str | None = None
    specs: t.Sequence[dg.AssetSpec] | None = None
    check_specs: None = None
    pool: str | None = None


class CachedAssetOut(BaseModel):
    type: t.Literal["asset_out"] = "asset_out"

    model_key: str
    asset_key: str
    tags: t.Mapping[str, str]
    is_required: bool
    group_name: str
    kinds: set[str] | None

    def to_asset_out(self) -> dg.AssetOut:
        """Convert to a Dagster AssetOut object"""
        if "kinds" in signature(dg.AssetOut).parameters:
            return dg.AssetOut(
                key=dg.AssetKey.from_user_string(self.asset_key),
                tags=self.tags,
                is_required=self.is_required,
                group_name=self.group_name,
                kinds=self.kinds,
            )
        return dg.AssetOut(
            key=dg.AssetKey.from_user_string(self.asset_key),
            tags=self.tags,
            is_required=self.is_required,
            group_name=self.group_name,
        )

    @classmethod
    def from_asset_out(cls, model_key: str, asset_out: dg.AssetOut) -> "CachedAssetOut":
        """Create from a Dagster AssetOut object"""
        assert asset_out.key is not None, "AssetOut key must not be None"

        return cls(
            model_key=model_key,
            asset_key=asset_out.key.to_user_string(),
            tags=asset_out.tags or {},
            is_required=asset_out.is_required,
            group_name=asset_out.group_name or "",
            kinds=asset_out.kinds,
        )


def cacheable_asset(asset_out: dg.AssetOut) -> CachedAssetOut:
    """Create a asset that can be loaded from cache"""
    return CachedAssetOut.from_asset_out("model_key", asset_out)
