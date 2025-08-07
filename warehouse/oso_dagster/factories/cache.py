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
    key: str | None = None
    check_specs: None = None
    owners: t.Sequence[str] | None = None
    kinds: t.AbstractSet[str] | None = None
    pool: str | None = None

    def as_dagster_asset(self, f: t.Callable, **kwargs):
        return dg.asset(
            f,
            name=self.name,
            key_prefix=self.key_prefix,
            ins=self.ins,
            deps=self.deps,
            metadata=self.metadata,
            tags=self.tags,
            description=self.description,
            config_schema=self.config_schema,
            required_resource_keys=self.required_resource_keys,
            resource_defs=self.resource_defs,
            hooks=self.hooks,
            io_manager_def=self.io_manager_def,
            io_manager_key=self.io_manager_key,
            dagster_type=self.dagster_type,
            op_tags=self.op_tags,
            group_name=self.group_name,
            output_required=self.output_required,
            code_version=self.code_version,
            key=dg.AssetKey.from_user_string(self.key) if self.key else None,
            owners=self.owners or [],
            kinds=self.kinds or set(),
            pool=self.pool,
            **kwargs,
        )


class CacheableJobOptions(BaseModel):
    """Derived from dg.job.__annotations__

    For options that are not support by the cache, we set the type to None so
    that attempts to use them will fail at static type checking time.
    """

    name: str | None = None
    description: str | None = None
    tags: t.Mapping[str, str] | None = None
    run_tags: t.Mapping[str, str] | None = None
    config: t.Mapping[str, t.Any] | None = None
    required_resource_keys: t.AbstractSet[str] | None = None
    resource_defs: t.Mapping[str, object] | None = None
    op_tags: t.Mapping[str, t.Any] | None = None
    code_version: str | None = None

    def as_dagster_job(self, f: t.Callable, **kwargs):
        return dg.job(
            name=self.name,
            description=self.description,
            tags=self.tags or {},
            config=self.config or {},
            # required_resource_keys=self.required_resource_keys,
            # resource_defs=self.resource_defs,
            # op_tags=self.op_tags,
            # code_version=self.code_version,
            **kwargs,
        )(f)


class CacheableSensorOptions(BaseModel):
    """Derived from dg.sensor.__annotations__

    For options that are not support by the cache, we set the type to None so
    that attempts to use them will fail at static type checking time.
    """

    name: str | None = None
    description: str | None = None
    minimum_interval_seconds: int | None = None
    required_resource_keys: set[str] | None = None
    metadata: t.Mapping[str, t.Any] | None = None
    tags: t.Mapping[str, str] | None = None
    code_version: str | None = None

    def as_dagster_sensor(self, f: t.Callable, **kwargs):
        return dg.sensor(
            name=self.name,
            description=self.description,
            minimum_interval_seconds=self.minimum_interval_seconds,
            required_resource_keys=self.required_resource_keys,
            metadata=self.metadata or {},
            tags=self.tags or {},
            **kwargs,
        )(f)


class CacheableAssetCheckOptions(BaseModel):
    """Derived from dg.asset_check.__annotations__

    For options that are not support by the cache, we set the type to None so
    that attempts to use them will fail at static type checking time.
    """

    asset: str
    name: str | None = None
    description: str | None = None
    op_tags: t.Mapping[str, str] | None = None
    config_schema: dg.Config | None = None
    required_resource_keys: set[str] | None = None
    resource_defs: t.Mapping[str, object] | None = None
    code_version: str | None = None

    def as_dagster_asset_check(self, f: t.Callable, **kwargs):
        return dg.asset_check(
            asset=dg.AssetKey.from_user_string(self.asset),
            name=self.name,
            description=self.description,
            op_tags=self.op_tags or {},
            config_schema=self.config_schema,
            required_resource_keys=self.required_resource_keys,
            resource_defs=self.resource_defs,
            **kwargs,
        )(f)


class CachedAssetOut(BaseModel):
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


class CachedInternalAssetDeps(BaseModel):
    type: t.Literal["internal_asset_dep"] = "internal_asset_dep"

    internal_asset_deps: dict[str, set[str]]

    def to_internal_asset_deps(self) -> dict[str, set[dg.AssetKey]]:
        """Convert to a Dagster internal asset dependencies dictionary"""
        return {
            k: {dg.AssetKey.from_user_string(dep) for dep in v}
            for k, v in self.internal_asset_deps.items()
        }

    @classmethod
    def from_internal_asset_deps(
        cls, internal_asset_deps: dict[str, set[dg.AssetKey]]
    ) -> "CachedInternalAssetDeps":
        """Create from a Dagster internal asset dependencies dictionary"""
        return cls(
            internal_asset_deps={
                k: {dep.to_user_string() for dep in v}
                for k, v in internal_asset_deps.items()
            }
        )


class CachedDeps(BaseModel):
    type: t.Literal["deps"] = "deps"

    deps: list[dict[str, str]]

    def to_deps(self) -> list[dg.AssetDep]:
        """Convert to a Dagster deps list"""
        return [
            dg.AssetDep(dg.AssetKey.from_user_string(dep["key"])) for dep in self.deps
        ]

    @classmethod
    def from_deps(cls, deps: list[dg.AssetDep]) -> "CachedDeps":
        """Create from a Dagster deps list"""
        return cls(deps=[{"key": dep.asset_key.to_user_string()} for dep in deps])


class CacheableMultiAssetOptions(BaseModel):
    """Derived from dg.multi_asset.__annotations__

    For options that are not support by the cache, we set the type to None so
    that attempts to use them will fail at static type checking time.
    """

    name: str | None = None
    outs: dict[str, CachedAssetOut]
    internal_asset_deps: CachedInternalAssetDeps
    deps: CachedDeps | None = None
    ins: t.Mapping[str, str] | None = None
    description: str | None = None
    config_schema: dg.Config | None = None
    required_resource_keys: t.AbstractSet[str] | None = None
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

    def as_dagster_multi_asset(self, f: t.Callable, **kwargs):
        return dg.multi_asset(
            name=self.name,
            outs={key: out.to_asset_out() for key, out in self.outs.items()},
            internal_asset_deps=self.internal_asset_deps.to_internal_asset_deps(),
            deps=self.deps.to_deps() if self.deps else None,
            ins={
                key: dg.AssetIn(key=dg.AssetKey.from_user_string(value))
                for key, value in (self.ins or {}).items()
            },
            description=self.description,
            config_schema=self.config_schema,
            required_resource_keys=self.required_resource_keys,
            backfill_policy=self.backfill_policy,
            op_tags=self.op_tags or {},
            can_subset=self.can_subset,
            resource_defs=self.resource_defs,
            group_name=self.group_name,
            retry_policy=self.retry_policy,
            code_version=self.code_version,
            specs=self.specs or [],
            check_specs=self.check_specs,
            pool=self.pool,
            **kwargs,
        )(f)
