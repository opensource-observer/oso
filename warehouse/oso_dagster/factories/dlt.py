from typing import (
    List,
    Dict,
    Any,
    Mapping,
    Optional,
    Callable,
    Iterator,
    Iterable,
    cast,
    Union,
    Type,
)

from dagster import (
    asset,
    AssetIn,
    AssetExecutionContext,
    MaterializeResult,
    Config,
    AssetMaterialization,
)
import dlt as dltlib
from dlt.sources import DltResource
from dlt.common.destination import Destination
from dlt.common.libs.pydantic import pydantic_to_table_schema_columns
from dagster_embedded_elt.dlt import DagsterDltResource
from pydantic import Field, BaseModel

from .common import (
    AssetDeps,
    AssetKeyPrefixParam,
    early_resources_asset_factory,
    AssetFactoryResponse,
)
from ..utils import SecretResolver, resolve_secrets_for_func
from .sql import PrefixedDltTranslator
from .. import constants


class DltAssetConfig(Config):
    limit: int = 0
    with_resources: List[str] = Field(default_factory=lambda: [])


def pydantic_to_dlt_nullable_columns(b: Type[BaseModel]):
    table_schema_columns = pydantic_to_table_schema_columns(b)
    for column in table_schema_columns.values():
        column["nullable"] = True
    print(table_schema_columns)
    return table_schema_columns


def _dlt_factory[
    R: Union[AssetMaterialization, MaterializeResult],
    C: DltAssetConfig, **P,
](c: Callable[P, Any], config_type: Type[C] = DltAssetConfig):
    def dlt_factory(
        config_type: Type[C] = config_type,
        dataset_name: str = "",
        name: str = "",
        key_prefix: Optional[AssetKeyPrefixParam] = None,
        deps: Optional[AssetDeps] = None,
        ins: Optional[Mapping[str, AssetIn]] = None,
        tags: Optional[Mapping[str, str]] = None,
        *args: P.args,
        **kwargs: P.kwargs,
    ):
        """Generates a dlt based asset from a given dlt source. This also
        automatically configures the pipeline for this source to have the main
        datawarehouse as the destination.

        The builtin dagster_embedded_elt doesn't properly handle things like
        dependencies so this factory mixes some of that library and some bespoke OSO
        related dagster configuration.
        """
        tags = tags or {}

        key_prefix_str = ""
        if key_prefix:
            if isinstance(key_prefix, str):
                key_prefix_str = key_prefix
            else:
                key_prefix_str = "_".join(key_prefix)
        dataset_name = dataset_name or key_prefix_str

        def _decorator(f: Callable[..., Iterator[DltResource]]):
            asset_name = name or f.__name__

            @early_resources_asset_factory(caller_depth=2)
            def _factory(
                dlt_staging_destination: Destination,
                dlt_warehouse_destination: Destination,
                secrets: SecretResolver,
            ):
                resolved_secrets = resolve_secrets_for_func(secrets, f)
                source = dltlib.source(f)

                asset_ins = dict(ins or {})

                # Exlude ins and resolved secrets
                extra_resources = (
                    set(f.__annotations__.keys())
                    - set(resolved_secrets.keys())
                    - set(asset_ins.keys())
                )

                if "context" in extra_resources:
                    extra_resources.discard("context")

                @asset(
                    name=asset_name,
                    key_prefix=key_prefix,
                    required_resource_keys=extra_resources.union({"dlt"}),
                    deps=deps,
                    ins=asset_ins,
                    tags=tags,
                    **kwargs,
                )
                def _dlt_asset(
                    context: AssetExecutionContext,
                    config: config_type,
                    **extra_source_args,
                ) -> Iterable[R]:
                    # Hack for now. Staging cannot be used if running locally.
                    # We need to change this interface. Instead of being reliant
                    # on the constant defining bigquery we should use some kind
                    # of generic function to wire this pipeline together.
                    pipeline = dltlib.pipeline(
                        f"{key_prefix_str}_{name}",
                        destination=dlt_warehouse_destination,
                        dataset_name=dataset_name,
                    )
                    if constants.enable_bigquery:
                        context.log.debug("dlt pipeline setup to use staging")
                        pipeline = dltlib.pipeline(
                            f"{key_prefix_str}_{name}",
                            destination=dlt_warehouse_destination,
                            staging=dlt_staging_destination,
                            dataset_name=dataset_name,
                        )

                    dlt = cast(DagsterDltResource, getattr(context.resources, "dlt"))

                    source_args: Dict[str, Any] = extra_source_args
                    source_args.update(resolved_secrets)

                    if "context" in source.__annotations__:
                        source_args["context"] = context
                    if "dlt" in source.__annotations__:
                        source_args["dlt"] = dlt
                    if "config" in source.__annotations__:
                        source_args["config"] = config

                    for resource in extra_resources:
                        source_args[resource] = getattr(context.resources, resource)

                    context.log.debug(
                        f"creating the dlt source and passing the following args: {source_args.keys()}"
                    )
                    context.log.debug(f"new source dataset_name: {dataset_name}")
                    dlt_source = source(**source_args)

                    if config.limit:
                        dlt_source = dlt_source.add_limit(config.limit)
                    if len(config.with_resources) > 0:
                        dlt_source.with_resources(*config.with_resources)

                    dlt_run_options: Dict[str, Any] = {}
                    if constants.enable_bigquery:
                        context.log.debug("dlt pipeline setup with bigquery and jsonl")
                        dlt_run_options["loader_file_format"] = "jsonl"

                    results = dlt.run(
                        context=context,
                        dlt_source=dlt_source,
                        dlt_pipeline=pipeline,
                        dagster_dlt_translator=PrefixedDltTranslator(
                            source_name=key_prefix_str, tags=dict(tags)
                        ),
                        **dlt_run_options,
                    )
                    for result in results:
                        yield cast(R, result)
                    # else:
                    #     # If an empty set is returned we need to return something
                    #     return MaterializeResult(metadata={})

                return AssetFactoryResponse([_dlt_asset])

            return _factory

        return _decorator

    return dlt_factory


dlt_factory = _dlt_factory(asset, DltAssetConfig)
