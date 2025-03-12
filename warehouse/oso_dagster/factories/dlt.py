import logging
import typing as t
from uuid import uuid4

import dlt as dltlib
from dagster import (
    AssetExecutionContext,
    AssetIn,
    AssetKey,
    AssetMaterialization,
    Config,
    MaterializeResult,
    PartitionsDefinition,
    asset,
    define_asset_job,
)
from dagster_embedded_elt.dlt import DagsterDltResource
from dlt.common.destination import Destination
from dlt.common.libs.pydantic import pydantic_to_table_schema_columns
from dlt.sources import DltResource
from oso_dagster.config import DagsterConfig
from pydantic import BaseModel, Field

from ..utils import SecretResolver, resolve_secrets_for_func
from .common import (
    AssetDeps,
    AssetFactoryResponse,
    AssetKeyPrefixParam,
    EarlyResourcesAssetFactory,
    early_resources_asset_factory,
)
from .sql import PrefixedDltTranslator

logger = logging.getLogger(__name__)


class DltAssetConfig(Config):
    limit: int = 0
    with_resources: t.List[str] = Field(default_factory=lambda: [])


def pydantic_to_dlt_nullable_columns(b: t.Type[BaseModel]):
    table_schema_columns = pydantic_to_table_schema_columns(b)
    for column in table_schema_columns.values():
        column["nullable"] = True
    return table_schema_columns


def _dlt_factory[
    R: t.Union[AssetMaterialization, MaterializeResult],
    C: DltAssetConfig, **P,
](
    c: t.Callable[P, t.Any], config_type: t.Type[C] = DltAssetConfig
):
    def dlt_factory(
        config_type: t.Type[C] = config_type,
        dataset_name: str = "",
        name: str = "",
        key_prefix: t.Optional[AssetKeyPrefixParam] = None,
        deps: t.Optional[AssetDeps] = None,
        ins: t.Optional[t.Mapping[str, AssetIn]] = None,
        tags: t.Optional[t.MutableMapping[str, str]] = None,
        op_tags: t.Optional[t.MutableMapping[str, t.Any]] = None,
        log_intermediate_results: bool = False,
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
        op_tags = op_tags or {}

        key_prefix_str = ""
        if key_prefix:
            if isinstance(key_prefix, str):
                key_prefix_str = key_prefix
            else:
                key_prefix_str = "_".join(key_prefix)
        dataset_name = dataset_name or key_prefix_str

        def _decorator(
            f: t.Callable[..., t.Iterator[DltResource]],
        ) -> EarlyResourcesAssetFactory:
            asset_name = name or f.__name__

            @early_resources_asset_factory(caller_depth=2)
            def _factory(
                dlt_staging_destination: Destination,
                dlt_warehouse_destination: Destination,
                secrets: SecretResolver,
            ):

                # logger.info(f"Creating asset for {key_prefix} with {tags}")
                resolved_secrets = resolve_secrets_for_func(secrets, f)
                source = dltlib.source(f)

                asset_ins = dict(ins or {})

                # Exlude ins and resolved secrets
                extra_resources = (
                    set(f.__annotations__.keys())
                    - set(resolved_secrets.keys())
                    - set(asset_ins.keys())
                )

                # logger.info(f"Creating asset for {key_prefix} with {tags}")

                if "context" in extra_resources:
                    extra_resources.discard("context")

                if "partitions_def" in kwargs:
                    tags["opensource.observer/extra"] = "partitioned-assets"
                    # we specify these two times, one for the asset, the other for the job itself
                    tags["dagster/concurrency_key"] = f"{key_prefix_str}_{asset_name}"
                    op_tags["dagster/concurrency_key"] = (
                        f"{key_prefix_str}_{asset_name}"
                    )

                # logger.info(f"Creating asset for {key_prefix} with {tags}")
                # We need to ensure that both dlt and global_config are
                # available to the generated asset as they're used by the
                # generated function.
                final_extra_resources = extra_resources.union({"dlt", "global_config"})

                @asset(
                    name=asset_name,
                    key_prefix=key_prefix,
                    required_resource_keys=final_extra_resources,
                    deps=deps,
                    ins=asset_ins,
                    tags=tags,
                    op_tags=op_tags,
                    **kwargs,
                )
                def _dlt_asset(
                    context: AssetExecutionContext,
                    config: config_type,
                    **extra_source_args,
                ) -> t.Iterable[R]:
                    pipeline_name = f"{key_prefix_str}_{name}_{uuid4()}"

                    # Hack for now. Staging cannot be used if running locally.
                    # We need to change this interface. Instead of being reliant
                    # on the constant defining bigquery we should use some kind
                    # of generic function to wire this pipeline together.
                    pipeline = dltlib.pipeline(
                        pipeline_name,
                        destination=dlt_warehouse_destination,
                        dataset_name=dataset_name,
                    )

                    # When using the `required_resource_keys` we need to
                    # retrieve resources from context.resources
                    global_config = t.cast(
                        DagsterConfig, getattr(context.resources, "global_config")
                    )
                    assert (
                        global_config
                    ), "global_config resource is not loading correctly"
                    if global_config.enable_bigquery:
                        context.log.debug("dlt pipeline setup to use staging")
                        pipeline = dltlib.pipeline(
                            pipeline_name,
                            destination=dlt_warehouse_destination,
                            staging=dlt_staging_destination,
                            dataset_name=dataset_name,
                        )

                    dlt = t.cast(DagsterDltResource, getattr(context.resources, "dlt"))

                    source_args: t.Dict[str, t.Any] = extra_source_args
                    source_args.update(resolved_secrets)

                    if "context" in f.__annotations__:
                        source_args["context"] = context
                    if "dlt" in f.__annotations__:
                        source_args["dlt"] = dlt
                    if "config" in f.__annotations__:
                        source_args["config"] = config
                    if "global_config" in f.__annotations__:
                        source_args["global_config"] = global_config

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

                    dlt_run_options: t.Dict[str, t.Any] = {}
                    if global_config.enable_bigquery:
                        context.log.debug("dlt pipeline setup with bigquery and jsonl")
                        dlt_run_options["loader_file_format"] = "jsonl"

                    dlt_prefix_keys = (
                        [key_prefix]
                        if isinstance(key_prefix, str)
                        else (key_prefix or [])
                    )
                    dlt_source_name = (
                        dlt_prefix_keys[-1] if dlt_prefix_keys else key_prefix_str
                    )
                    dlt_key_prefix = dlt_prefix_keys[:-1]

                    results = dlt.run(
                        context=context,
                        dlt_source=dlt_source,
                        dlt_pipeline=pipeline,
                        dagster_dlt_translator=PrefixedDltTranslator(
                            prefix=dlt_key_prefix,
                            source_name=dlt_source_name,
                            tags=dict(tags),
                        ),
                        **dlt_run_options,
                    )
                    for result in results:
                        if log_intermediate_results and isinstance(
                            result, MaterializeResult
                        ):
                            if result.metadata:
                                context.log.info(
                                    f"Loaded '{result.asset_key}' into '{result.metadata['dataset_name']}' successfully"
                                )
                            else:
                                context.log.info(
                                    f"Loaded '{result.asset_key}' successfully"
                                )
                            continue

                        yield t.cast(R, result)

                    if log_intermediate_results:
                        asset_key_parts = []
                        if key_prefix:
                            if isinstance(key_prefix, str):
                                asset_key_parts = [key_prefix]
                            else:
                                asset_key_parts = list(key_prefix)
                        asset_key_parts.append(asset_name)

                        yield t.cast(
                            R, MaterializeResult(asset_key=AssetKey(asset_key_parts))
                        )

                asset_partitions = t.cast(
                    t.Optional[PartitionsDefinition[str]],
                    kwargs["partitions_def"] if "partitions_def" in kwargs else None,
                )

                _asset_job = define_asset_job(
                    name=f"{key_prefix_str}_{asset_name}_job",
                    selection=[_dlt_asset],
                    partitions_def=asset_partitions,
                    tags=tags,
                )

                return AssetFactoryResponse([_dlt_asset], [], [_asset_job])

            return _factory

        return _decorator

    return dlt_factory


dlt_factory = _dlt_factory(asset, DltAssetConfig)
